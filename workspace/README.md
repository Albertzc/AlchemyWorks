# Workspace

> 所有权：本目录完全属于实例项目，不是工作流源定义目录。工作流仓库只提供此目录的入口，不同步或覆盖其中的业务内容。

存放实际应用源码、配置和测试；版本化工作流文档放在 `iteration/v{major}.{minor}/`，不应放入此目录。

`workspace/README.md` 是实例的当前系统功能说明：在 `05-review-release` 通过后由工作流根据当前版本 requirement 自动生成，包含版本标记和 `## 当前系统功能说明`。`workspace/workflow/` 中的 `manifest.yaml`、`traceability.json`、`current-state.json` 是工作流生成的实例状态，属于实例 Git 提交内容；`.workflow/` 下的缓存、Context Pack、task-runs 和 dashboard 是同步副本的本地运行数据，不放在这里。
