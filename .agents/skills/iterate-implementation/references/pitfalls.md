# Pitfalls — Implementation (Stage 04)

实战中遇到的问题与修复方案。基于 SourceLink v1 实施经验。

## 1. `patch` 工具缩进陷阱

**症状**：用 `patch` 工具的 `old_string` / `new_string` 替换大块代码时，函数体被错误缩进（或"被推入"了错误的层级），导致后续代码全部报错但 `compileall` 之前不一定会触发（如果被推入函数体内部）。

**最常见场景**：

- 用 `new_string` 替换**多行函数体**时，工具会保留你新写的缩进
- 替换后立即 `grep` 找原函数签名 → 函数被"散开"了

**修复策略**：

- 替换前先 `read_file` 看实际缩进（4 空格 / 8 空格）
- 每次大块 patch 后立即 `python3 -m compileall -q <dir>` 验证
- 替换时用**最小 unique snippet** 而非大段
- 连续多次 patch 缩进被搞乱时，停止 patch，用 `write_file` 整体重写

**预防脚本**：

```bash
# 每次大块 patch 后必跑
cd workspace/backend && python3 -m compileall -q sourcelink
```

## 2. async generator 不能 return value

**症状**：

```python
async def read(self, ...) -> Iterator[list[dict]]:
    if False:
        yield []
    return iter([])  # SyntaxError: 'return' with value in async generator
```

**修复**：

```python
async def read(self, ...) -> Iterator[list[dict]]:
    if False:
        yield []
    return  # bare return — 等价于 StopIteration
```

**根因**：async generator（`yield` 在内）只接受 `return` 不带值。

## 3. 顶层 `type X = ...` 语法陷阱

**症状**：

```python
type CreatedAt = Mapped[datetime]  # PEP 604 — 在某些 linter / 老 Python 版本不工作
```

**修复**：统一用工厂函数：

```python
def created_at_column():
    return mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
```

## 4. SQLite 不支持 PostgreSQL UUID 类型

**症状**：`sqlalchemy.dialects.postgresql.UUID` 在 SQLite `create_all()` 时报错。

**修复**：环境探测自动切换：

```python
import os
_USE_SQLITE = os.environ.get("DATABASE_URL", "sqlite:///./app.db").startswith("sqlite")

def _uuid_pk() -> Mapped[str]:
    if _USE_SQLITE:
        return mapped_column(String(36), primary_key=True, default=gen_uuid)
    return mapped_column(PG_UUID(as_uuid=False), primary_key=True, default=gen_uuid)
```

**进一步**：约束名 `WHERE deleted IS NULL` 在 SQLite 部分索引支持有限，生产 PG 才能用 `CREATE UNIQUE INDEX ... WHERE deleted IS NULL`。在 SQLite 上只用普通 `UNIQUE` 约束。

## 5. Pydantic v2 字段约束关键字

**症状**：

```python
name: str = Field(..., min=1, max=64)  # Pydantic v2 错误
```

**修复**：

```python
name: str = Field(..., min_length=1, max_length=64)
```

**记忆点**：Pydantic v2 字符串长度用 `min_length` / `max_length`，数值用 `ge` / `le`。

## 6. FastAPI `get_db` 依赖在测试中的 override

**症状**：`get_db` 是 generator（`yield`），直接 monkeypatch 函数体不工作。

**正确做法**：

```python
def _override():
    try:
        yield db_session
    finally:
        pass

app.dependency_overrides[get_db] = _override
```

**不要**：

```python
monkeypatch.setattr("sourcelink.db.session.get_db", db_session)  # 错 — 函数签名不匹配
```

## 7. 故意保留的"已知限制"必须显式列出

**反模式**：在 v1-source-code.md §5 里写"暂未实现的部分"，但忘记在交付消息中明确提醒用户 → 用户后续发现功能缺失，重复提问。

**正确做法**：

- v1-source-code.md §5 列 6-10 条已知限制 + 推迟版本
- 交付消息里再次强调"本轮不做的 N 件事"
- 任何占位实现（如 MySQL Driver 骨架）必须在 §5 显式标记

## 8. 测试用 time.sleep(0.1) 轮询异步 Run

**症状**：v1 用 `asyncio.create_task` 启动 Run 后，测试需要等待完成。

**危险模式**：

```python
# 危险
time.sleep(5)  # 5 秒硬等待 — 慢测试
```

**正确做法**：

```python
deadline = time.time() + 5
while time.time() < deadline:
    r = client.get(...).json()
    if r["status"] in ("succeeded", "failed", "cancelled"):
        break
    time.sleep(0.1)
else:
    pytest.fail("Run 未在 5s 内完成")
```

**更进一步**：v1.1 应改用 `httpx.AsyncClient` + FastAPI 异步 + `asyncio.Event` 通知，**完全消除轮询**。

## 9. CSV Driver 默认路径权限

**症状**：测试中给目标 CSV 路径设一个**父目录不存在**的位置，写入会失败 —— 但错误信息是 `FileNotFoundError`，与"overwrite 二次确认"完全无关，导致 AC-004 测试无法验证阻断逻辑。

**修复**：AC-004 测试用真实"超过期望值"的 row_count 配置（不是路径错误），用 verified_run 验证阻断语义。

## 10. 一次性 make 目标应包含 compileall

**预防**：在 Makefile 加 `make compile-check` 目标：

```makefile
compile-check:
	$(VENV)/bin/python -m compileall -q sourcelink
```

每次大块 patch 后跑一次。

## 11. PEP 8 — Pydantic 模型与 SQLAlchemy 混排

Pydantic schema 文件 + SQLAlchemy model 文件应分开：

- `models/` — SQLAlchemy ORM（继承 `Base`）
- `schemas/` — Pydantic DTO（API 契约）

混排会导致：

- 循环依赖（model 引用 schema 又被 schema 引用）
- 测试 setup 复杂
- 编译警告
