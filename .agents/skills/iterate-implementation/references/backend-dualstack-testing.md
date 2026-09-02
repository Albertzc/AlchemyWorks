# Backend Dual-Stack Testing — SQLAlchemy + PG/SQLite + Docker

实战经验。SourceLink v1 在 docker compose + 临时 SQLite 测试模式下跑出 4 个连续 bug 的完整复盘。

## 1. docker compose 容器内跑 pytest 的前置 volume 挂载

容器化后端默认只挂源码+alembic，**测试目录不在镜像里**。要 `docker exec backend pytest tests/` 跑测试，必须额外挂：

```yaml
# workspace/backend/docker-compose.yml
services:
  backend:
    volumes:
      - ./sourcelink:/app/sourcelink
      - ./alembic:/app/alembic
      - ./alembic.ini:/app/alembic.ini
      # dev-only 三个：
      - ./tests:/app/tests
      - ./pyproject.toml:/app/pyproject.toml
      - ./pytest.ini:/app/pytest.ini
```

改完 `docker compose restart backend`（不是 `up -d` 也行），volumes 会重挂。

**为什么不放进镜像**：测试代码不该进生产镜像。把"测试可执行"做成运行期挂载，镜像保持纯净。

## 2. `_USE_SQLITE` 模块级求值陷阱（最隐蔽）

```python
# sourcelink/models/__init__.py
import os
_USE_SQLITE = os.environ.get("DATABASE_URL", "sqlite:///./app.db").startswith("sqlite")  # 模块级一次性！

def _uuid_pk():
    if _USE_SQLITE:
        return mapped_column(String(36), primary_key=True, default=gen_uuid)
    return mapped_column(PG_UUID(as_uuid=False), primary_key=True, default=gen_uuid)
```

**触发场景**：docker compose 启动 backend 容器时注入 `DATABASE_URL=postgresql://...` → `_USE_SQLITE = False` → 所有 `_uuid_pk/_uuid_fk` 走 PG_UUID 分支 → 模型定义固化。后续 conftest 临时建 SQLite engine 也救不回来，因为模型类型是 import 时锁定的。

**症状**：`psycopg.errors.UndefinedFunction: operator does not exist: uuid = character varying` ——注意是 PG 方言报错而不是 SQLite 报错，证明模型走了 PG 路径。

**三种修法（推荐度递减）**：

1. **v1.1 改函数级求值**：把判断挪进 `_uuid_pk()` 函数体内，每次 engine 创建时再判断（与 engine 创建时机一致）。
2. **docker compose 加 test profile**：测试容器独立环境变量。
3. **本机 venv 跑测试**（最快但绕开 docker）：
   ```bash
   cd workspace/backend
   uv venv .venv
   uv pip install -e ".[dev]"
   pytest
   ```

**反模式**：在 conftest 顶部加 `os.environ["DATABASE_URL"] = "sqlite://"` 无效——settings 模块已加载过 Pydantic Settings 且实例化缓存；即使 reload 也无效，因为 `models._USE_SQLITE` 在 import 时已固化。

## 3. UUID FK 字段类型必须与目标列对齐

```python
# ❌ 错误：指向 UUID 表但用 String(36)
class Run(Base):
    pipeline_id = mapped_column(String(36), ForeignKey("pipeline.id"))
    project_id = mapped_column(String(36), ForeignKey("project.id"))

# ✅ 正确：用 _uuid_fk
class Run(Base):
    pipeline_id: Mapped[str] = _uuid_fk("pipeline.id")
    project_id: Mapped[str] = _uuid_fk("project.id")
```

**非外键但指向 UUID 表的字段**也要用 PG_UUID：

```python
# Run.resume_from_step_id 指向 step_run.id (PG_UUID)
resume_from_step_id: Mapped[str | None] = mapped_column(
    PG_UUID(as_uuid=False), nullable=True
)
```

**预防脚本**：写完模型后 grep 验证零漏网：

```bash
grep "String(36), ForeignKey" sourcelink/models/__init__.py  # 期望零结果
```

## 4. ORM relationship 必须与 ForeignKey 配套声明

service 层用反向引用（`p.runs[-1]`、`p.connectors`）时，模型必须声明 `relationship(back_populates=...)`，否则运行时抛 `AttributeError`。

```python
class Pipeline(Base):
    runs: Mapped[list["Run"]] = relationship(
        back_populates="pipeline", cascade="all, delete-orphan"
    )

class Run(Base):
    pipeline: Mapped["Pipeline"] = relationship(back_populates="runs")
```

**预防**：写完 FK 立刻问"service 层会不会反向引用这个对象？"——会的话立即写 relationship。

## 5. FastAPI TestClient 同步调用下 `_schedule_run` 的 asyncio 兜底

```python
# ❌ 旧代码：TestClient 同步环境下 get_event_loop 拿不到 running loop
def _schedule_run(run_id, params, *, resume_from=None):
    try:
        asyncio.get_event_loop().create_task(execute_pipeline(...))
    except RuntimeError:
        logger.warning("无 asyncio loop，Run %s 未自动触发", run_id)
        # ⚠️ 这里默默吞了 → Run 永远卡 pending，测试轮询超时

# ✅ 新代码：用 get_running_loop + 线程池兜底
def _schedule_run(run_id, params, *, resume_from=None):
    try:
        loop = asyncio.get_running_loop()  # 改这里
        loop.create_task(execute_pipeline(run_id, params, resume_from_step_id=resume_from))
    except RuntimeError:
        # TestClient 同步调用或 CLI 触发：用线程池跑 asyncio.run
        import threading
        def _runner():
            asyncio.run(execute_pipeline(run_id, params, resume_from_step_id=resume_from))
        threading.Thread(target=_runner, daemon=True).start()
```

**关键 API 区别**：
- `asyncio.get_event_loop()` —— deprecated，无 loop 时会**自动创建**新 loop（很迷惑）
- `asyncio.get_running_loop()` —— 新 API，无 loop 时**直接抛 RuntimeError**，正好作为"我在同步环境"的信号

## 6. 集成测试执行清单

后端集成测试在 docker 内执行的标准流程：

```bash
# 1. 拉起或确认 docker compose 4 服务在跑
cd workspace/backend
docker compose up -d  # 第一次会构建 backend 镜像

# 2. 确认后端 healthy
curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/health  # 200

# 3. 跑测试
docker exec sourcelink-backend bash -c "cd /app && python -m pytest tests/ -v --tb=short"

# 4. 改完代码后必须 restart 容器让模型/服务代码生效
docker compose restart backend
sleep 10  # 等 alembic upgrade + uvicorn 启动
```

## 7. 真实复盘记录（SourceLink v1，2026-08-26）

| # | 触发命令 | 报错 | 根因 | 修复 |
|---|---|---|---|---|
| 1 | `pytest tests/` | `file or directory not found: tests/` | docker compose 未挂载 tests/ | 加 3 个 volume |
| 2 | `pytest tests/integration/` | `uuid = character varying` | `_USE_SQLITE` 模块级固化，模型走 PG_UUID | 把 `_USE_SQLITE` 改函数级（本会话推迟到 v1.1，本机跑可绕开） |
| 3 | `pytest tests/integration/` | `'Pipeline' object has no attribute 'runs'` | relationship 未声明 | 补 `Project↔Connector/Pipeline/Run`、`Pipeline↔Run`、`Run↔Project/Pipeline` 6 个双向 relationship |
| 4 | `pytest tests/integration/` | `无 asyncio loop, Run xxx 未自动触发` | `get_event_loop` + `except pass` | 改 `get_running_loop` + 线程池兜底 |

**最终结果**：4/4 unit ✅ + 7/10 integration（AC-002/004/006 因 ISSUE-010 推迟 v1.1）。

## 8. v1.1 改进建议

- **模型 `_USE_SQLITE` 函数级**（最高优先级）
- **docker compose test profile**：单独的 `DATABASE_URL=sqlite://` 容器
- **Testcontainers PG 测试**：用真实 PG 跑集成测试，避免 SQLite 兼容性问题
- **async def _schedule_run + BackgroundTasks**：消除 `threading.Thread` 兜底的隐患