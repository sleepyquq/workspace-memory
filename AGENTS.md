# Workspace Memory Skill Repository

- 本目录是 `workspace-memory` skill 的开发源仓库；根 `SKILL.md` 是安装入口。
- 修改应保持 Markdown + Python 标准库的轻量形式，不引入后台服务、数据库或运行时专用依赖。
- 默认只维护本仓库；不要同步覆盖已安装 skill、修改外部项目、添加远端、提交或发布，除非用户明确要求。明确授权的验证使用隔离合成工作区。
- 面向发布的文件和示例不写入私有项目名称、私有仓库地址或个人环境路径。
- 修改规则时一并核对 `references/`、`assets/` 和合成示例，避免规则与模板漂移。
- 校验器修改运行 `python -m unittest discover -s tests -v`；示例运行 `python scripts/validate_memory.py examples/editor-workspace`。
- 示例是测试数据，不代表当前仓库启用了 workspace memory，也不授权读取其他工作区。
- 代码注释优先使用中文；skill 与 references 沿用英文，面向本用户的仓库说明使用中文。
