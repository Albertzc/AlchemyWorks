# Iterations

存放版本化交付物。不要手工创建版本目录；baseline 门禁通过后使用 `python .workflow/workflow.py init-version` 创建下一个版本。

`raw-requirement/` 仅存放用户提供的原始需求。运行 `python .workflow/workflow.py route-requirement` 确定当前输入对应的版本；Agent 仅可读取，不得修改、重命名或删除其中的文件。
