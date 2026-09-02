# Vue 3 + Element Plus + openapi-typescript — Type Chain Recipe

> 实证：SourceLink v1 前端 14 个 view 一次性踩过的坑 + 正确链路。下次按此模板直接复制。

## 1. 工具链版本

- Vue 3.5 + Vite 5 + TypeScript 5.5
- Element Plus 2.8 + `@element-plus/icons-vue`
- Pinia 2.2 + `@tanstack/vue-query` 5.51
- `axios` 1.7 + `openapi-typescript` 7.4（**类型生成器**）
- `unplugin-auto-import` + `unplugin-vue-components`（Element Plus 按需）

## 2. 三层目录约定

```text
src/
├── api/
│   ├── client.ts          # axios instance + 拦截器
│   ├── schema.ts          # openapi-typescript 生成（或手工占位）
│   └── index.ts           # 各 *Api 对象 + 类型 re-export
├── composables/
│   └── useQueries.ts      # 所有 useQuery/useMutation composables
├── stores/                # Pinia stores（少用，缓存用 Vue Query）
├── components/
│   ├── layout/            # AppLayout, Sidebar, Topbar
│   ├── business/          # RunStatusBadge, PipelineStageTimeline, ErrorClassBox, WatermarkProgressBar
│   └── common/            # ConfirmDialog, EmptyState, DurationText
├── views/                 # 路由页面
├── router/index.ts
├── stores/
└── styles/index.css
```

## 3. **关键陷阱**：类型从哪里导出

`openapi-typescript` 默认把类型生成到 `src/api/schema.ts`，**但很多教程把 API 方法（`projectsApi.list()`）写在 `index.ts`**。结果：`index.ts` 里的类型是 `import type { ... } from './schema'`（私有），**不能**被外部 `import type { Project } from '@/api'` 用到。

### 错误示范

```ts
// src/api/index.ts
import type { Project } from './schema';  // ← 私有，未 re-export
export const projectsApi = { ... };
```

```ts
// src/composables/useQueries.ts
import { projectsApi, type Project } from '@/api';
//                       ^^^^^^^^^^^^ TS2459: Module '@/api' declares 'Project'
//                                    locally, but it is not exported.
```

### 正确做法：**显式 type re-export 块**

```ts
// src/api/index.ts
import type {
  Project, ProjectListResponse, Connector, ConnectorTestResult,
  Pipeline, PipelineListResponse, Run, RunListResponse, RunDetail,
  Watermark, DataQualityRule, RunLog,
} from './schema';

export type {
  Project, ProjectListResponse, Connector, ConnectorTestResult,
  Pipeline, PipelineListResponse, Run, RunListResponse, RunDetail,
  Watermark, DataQualityRule, RunLog, OverviewStats,
} from './schema';
```

这样下游可以：
```ts
import { projectsApi, type Project, type OverviewStats } from '@/api';
```

### 副陷阱：接口定义分散

如果某个类型是**手工定义**（如 `OverviewStats`，在 schema 没有），必须先把它**移到 schema.ts**，否则 `export type { OverviewStats } from './schema'` 会报 TS2484「Export declaration conflicts」。

## 4. Vue Query + 类型推导

```ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query';
import { projectsApi, type Project } from '@/api';
import { computed, type Ref } from 'vue';

export function useProjectsQuery(params?: Ref<{ q?: string }>) {
  return useQuery({
    queryKey: ['projects', params],   // params 是 Ref — 自动响应式
    queryFn: () => projectsApi.list(params?.value),
  });
}

export function usePipeline(id: Ref<string | undefined>) {
  return useQuery({
    queryKey: computed(() => ['pipeline', id.value]),
    queryFn: () => pipelinesApi.get(id.value!),
    enabled: computed(() => !!id.value),  // 关键：未就绪不发请求
  });
}
```

**要点**：
- `queryKey` 可以是 `Ref` 或 `ComputedRef`；框架自动响应式追踪
- `enabled` 用 `ComputedRef(() => !!id.value)` 而非 boolean — 否则首次渲染时 id 还没传进来就发请求
- `mutateAsync` 返回 `Promise<T>` — 用 `try/await/catch` 处理失败

## 5. Element Plus 按需 + 自动导入

`vite.config.ts`：

```ts
plugins: [
  vue(),
  AutoImport({
    resolvers: [ElementPlusResolver()],
    imports: ['vue', 'vue-router', 'pinia'],
    dts: 'src/auto-imports.d.ts',  // 类型补全
  }),
  Components({
    resolvers: [ElementPlusResolver()],
    dts: 'src/components.d.ts',
  }),
],
```

模板里**直接用** `<el-button>`、`<el-table>`、`<el-icon>` — 不需要 import。

图标需要 import：
```ts
import { Plus, Search, Folder, Connection } from '@element-plus/icons-vue';
```

或在 `main.ts` 全局注册（图标多时省事）：
```ts
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}
```

## 6. 单用户本地模式（v1 简化）

无登录系统时，axios 请求带固定 `X-User-Id`：

```ts
const STORAGE_KEY_USER = 'sourcelink-user-id';

instance.interceptors.request.use((config) => {
  const userId = localStorage.getItem(STORAGE_KEY_USER) ?? 'engineer';
  config.headers.set('X-User-Id', userId);
  return config;
});
```

v2 切换 Bearer Token 时只改这一处。

## 7. 错误响应统一格式

后端返回结构不一时，前端拦截器归一化：

```ts
instance.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const data = error.response?.data;
    const normalized: ApiError = {
      code: data?.code ?? data?.error ?? error.code,
      message: data?.message ?? data?.detail ?? error.message ?? '请求失败，请稍后再试',
      detail: data,
      error_class: data?.error_class,  // 后端 6 类错误
      hint: data?.hint,
    };
    return Promise.reject(normalized);
  }
);
```

页面只关心 `error.message` + `error.error_class`，不直接读 axios error。

## 8. Vue Router 14 条路由（按 SourceLink v1 实测）

```
/                         → PG-OVERVIEW    OverviewView
/projects                 → PG-PROJ-LIST   ProjectsView
/connectors               → PG-CONN-LIST   ConnectorsView
/connectors/new           → PG-CONN-EDIT   ConnectorEditView
/connectors/:id           → PG-CONN-EDIT   ConnectorEditView (同一组件，模式不同)
/pipelines                → PG-PIPE-LIST   PipelinesView
/pipelines/new            → PG-PIPE-EDIT   PipelineEditView
/pipelines/:id            → PG-PIPE-EDIT   PipelineEditView
/pipelines/:id/run        → PG-PIPE-RUN    PipelineRunView
/runs                     → PG-RUN-CENTER  RunsView
/runs/:id                 → PG-RUN-DETAIL  RunDetailView
/runs/:id/retry           → PG-RUN-RETRY   RunRetryView (可选，常并入详情)
/run-logs                 → PG-RUN-LOGS    RunLogsView
/data-quality             → PG-DQ          DataQualityView
/watermarks               → PG-WATERMARK   WatermarksView
/:pathMatch(.*)*          → 404            NotFoundView
```

每个 `meta.pg` 关联 feature-spec 的 PG-ID，方便面包屑 / 测试追溯。

## 9. type-check 验证脚本

```bash
cd workspace/frontend
npx vue-tsc --noEmit 2>&1 | grep "error TS" | grep -v "Cannot find module '@/views/"
```

`grep -v "Cannot find module '@/views/"` 过滤掉**分批交付时**「待写 view」产生的预期缺失，只看真实问题。

## 10. dev server 启动

```bash
cd workspace/frontend
npm install
npm run dev   # → http://127.0.0.1:5173，/api 代理到 localhost:8000
```

后端先起，否则页面打开全是 spinner + retry。

## 11. 生产构建 + API 类型同步

后端 `make gen-api` 触发的 `openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.ts` 会**覆盖整个 schema.ts**。约定：

- `schema.ts` 第一行注释：`/** 此文件由 gen-api 自动生成，请勿手改。 */`
- 手工补充的类型（如 `OverviewStats`）放在 `schema.ts` 末尾 + 显式标记

每次 `git diff src/api/schema.ts` 必须人工 review，确认覆盖未误删手工类型。

## 12. 常见踩坑

| 症状 | 原因 | 修复 |
|---|---|---|
| `Module '@/api' declares 'X' locally, but it is not exported` | 类型只 import 未 re-export | 加 `export type { X } from './schema'` 块 |
| `Export declaration conflicts` | 同一类型在两处定义 | 删 index.ts 本地定义，统一从 schema 导出 |
| `Cannot find name 'OverviewStats'` | import type 没生效 | 检查 `import { ... type X } from '@/api'` 写法 |
| view 模板里图标不显示 | 图标未注册 | `import { Plus } from '@element-plus/icons-vue'` 或全局注册 |
| `el-button` 报「没有注册组件」 | `unplugin-vue-components` 未配 | `Components({ resolvers: [ElementPlusResolver()] })` |
| 路由跳转后页面 404 | `:pathMatch(.*)*` 必须放最后 | 见上 router 模板 |
| ESLint 9 报 `Couldn't find an eslint.config.(js|mjs|cjs)` | 老 `.eslintrc.*` 在 v9 不识别 | 新增 `eslint.config.js`（flat config 格式），不是 `.eslintrc.cjs` |
| `vue/no-side-effects-in-computed-properties` 在 `computed` 写 ref.value | computed 应纯计算，副作用放 `watch` | 拆成：`const isX = computed(() => 纯逻辑)` + `watch(source, v => { isX 派生时同步写 ref })` |
| `vue/require-default-prop: Prop 'xxx' requires default value to be set` | 可选 prop 缺默认 | `withDefaults(defineProps<{ x?: T }>(), { x: undefined })` — 显式给 `undefined` |
| `npm run lint --fix` 触发成百条警告 | Vue 模板 `max-attributes-per-line` / `singleline-html-element-content-newline` | 跑一次 `--fix` 批量修；剩余手改 `withDefaults` |
| 用 `PipelineStageTimeline` 报错 prop 类型不对 | 该组件是给 `RunDetail` 用，不是给 `Pipeline` definition 预览 | 用前 `read_file` 看组件 prop 签名；不确定就别强行套组件，写内联 `<el-collapse>` 或 `<el-table>` |
| `npm install` 跑 6 分钟看似卡死 | 400+ 包冷装，正常 | `terminal(background=true)` 后台跑，前台继续推进 |

## 13. 多批渐进交付（10+ view 必读）

> 用户原话：「不需要一次性完成全部内容，可以拆分成几次来完成。」

强制规则（已实证）：

1. **每批 2-4 个 view，最多 5 个**。超出就拆。
2. **每批结束必跑**：`npx vue-tsc --noEmit 2>&1 | grep "error TS" | grep -v "Cannot find module '@/views/'"` — `grep -v` 过滤掉「待写 view」的预期缺失。
3. **批划分原则**：
   - 列表/CRUD 页面（轻量、可独立验证）放同一批
   - 含业务组件 + 时间轴 + 错误诊断的详情页单独一批
   - 边缘页（404 / 空状态）放最后一批
4. **副产修跨批累积**：A 批修的 type re-export / schema 类型补全，B 批才能用；不要把"待修"推到收尾。
5. **写新组件前先 `read_file` 看现有组件的 prop 定义**。盲猜组件签名（特别是 `PipelineStageTimeline` 给 Run 用还是 Pipeline 用）会撞类型墙。
6. **收尾前一次跑完**：`npm run type-check` / `npm run lint:check` / `npm run test-unit` / `npm run dev` 四件套，逐项确认 0 错 0 warning。

## 14. 上下文管理（用户原话「上下文太大的这个情况，有什么办法解决？」）

这是**类级别**工作流问题，不是单次抱怨。**5 个工具级手段**按优先级用：

| 优先级 | 工具 | 用法 |
|---|---|---|
| 1 | `search_files` / `search_content` | 找关键行而非全文读，省 80%+ token |
| 2 | `read_file offset=N limit=M` | 大文件分页（默认 200 行/页），按需读 |
| 3 | `patch` 改 5-30 行 | 不用 `write_file` 整页覆盖，避免上下文重复装载 |
| 4 | `delegate_task` | 探索性/汇总性子任务扔给隔离 context 子 agent，只回摘要 |
| 5 | `open_preview` + `read_preview` + vision | 浏览器看渲染态，代替读静态 HTML（原型/UI 阶段） |

**绝对不做**：

- 一次 `read_file` 拉 100KB+ 全文
- 把长文档复制到回复里（用 grep 摘要行）
- 把"待修"列表塞进 prompt，让 prompt 越来越长
- 一次性写 10+ 个 view（即使每个只有 100 行）