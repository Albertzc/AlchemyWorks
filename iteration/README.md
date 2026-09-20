# Iterations

> 所有权：本目录属于实例项目。`README.md` 和 `raw-requirement/README.md` 是工作流提供的初始化说明；`v{major}.{minor}/` 与 `archive/` 下的需求、设计、实施、评审和归档内容由实例项目维护并提交。

存放版本化交付物。不要手工创建版本目录；baseline 门禁通过后使用 `python .workflow/workflow.py init-version` 创建下一个版本。

`raw-requirement/` 仅存放用户提供的原始需求。运行 `python .workflow/workflow.py route-requirement` 确定当前输入对应的版本；Agent 仅可读取，不得修改、重命名或删除其中的文件。不要手工创建或移动版本目录；使用 `init-version` 和版本管理规则。
