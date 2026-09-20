# my-ai-skills

个人维护的 AI Skills 集合。

| 目录 | 用途 |
| --- | --- |
| [safe-autonomous-ops-windows](safe-autonomous-ops-windows/SKILL.md) | Windows 本机与 SSH 远程 Linux 工作区的安全操作规范，包含路径检查、备份和恢复流程。 |
| [safe-autonomous-ops-linux](safe-autonomous-ops-linux/SKILL.md) | Linux/POSIX 本机与 SSH 远端工作区的安全操作规范，包含远程连接、文件传输、回滚和恢复约束。 |
| [nature-style-plotting](nature-style-plotting/SKILL.md) | 使用 Matplotlib 创建、修改和审查 Nature 风格科研图。 |
| [dft-abacus](dft-abacus/SKILL.md) | 依据 ABACUS v3.10.1 源码准备、审核和排查 DFT 计算，覆盖输入、精度、SCF、电子温度与熵、结构优化、AIMD、电子结构、磁性及性能。 |

每项技能的入口为对应目录中的 `SKILL.md`；按需包含 `agents/` 界面元数据、`references/` 补充资料和 `templates/` 模板。

## dft-abacus

当前技能版本为 `0.2.1`，以 ABACUS `v3.10.1` 的源码实现为依据，包含 7 个任务子技能和 12 张能力卡。其他 ABACUS 版本或本地补丁需要重新核对相关实现。

- [阅读入口](dft-abacus/DIGEST.md)：按任务定位技能说明及参考资料。
- [输入模板](dft-abacus/templates/README.md)：INPUT、STRU、KPT 和能带路径的文件骨架。
- [源码依据](dft-abacus/references/source-audit.md)：版本基线、函数位置及适用条件。
- [验证记录](dft-abacus/test-results.md)：源码核对、局部执行检查及其边界；[行为用例](dft-abacus/test-prompts.json)用于后续复核。

复制或安装时应保留整个 `dft-abacus/` 目录，子技能共用包内参考资料和模板。模板中的占位符、赝势及轨道文件需要按实际体系补齐，并进行精度收敛检查；现有验证不代表已完成真实材料的完整 DFT 计算。

## 维护

- 在本仓库中维护技能源文件。
- 已复制安装到用户目录的技能是独立副本；源文件更新后需要同步安装副本。
- 新建的 .trash/ 回滚备份、环境文件、密钥及本地缓存默认通过 .gitignore 排除；已显式提交的备份随 Git 管理。
- 已提交的 .trash/ 备份关闭换行转换，保留原始文件字节及 SHA-256 校验值。
- 文本文件的换行方式由 .gitattributes 管理。
