# my-ai-skills

个人维护的 AI Skills 集合。

| 目录 | 用途 |
| --- | --- |
| safe-autonomous-ops-windows | Windows 本机与 SSH 远程 Linux 工作区的安全操作规范，包含路径检查、备份和恢复流程。 |
| safe-autonomous-ops-linux | Linux/POSIX 项目工作区的安全操作规范。 |
| nature-style-plotting | 使用 Matplotlib 创建、修改和审查 Nature 风格科研图。 |

每项技能的入口为对应目录中的 SKILL.md；agents/ 保存界面元数据，references/ 保存补充资料。

## 维护

- 在本仓库中维护技能源文件。
- 已复制安装到用户目录的技能是独立副本；源文件更新后需要同步安装副本。
- .trash/ 回滚备份、环境文件、密钥及本地缓存通过 .gitignore 排除。
- 文本文件的换行方式由 .gitattributes 管理。
