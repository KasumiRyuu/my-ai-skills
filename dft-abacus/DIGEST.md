# ABACUS v3.10.1 阅读入口

基线：tag `v3.10.1`，commit `f71921fe848659deac8db319cd4311b55b5ad480`。
本包以实现为依据，各任务参考统一说明参数含义与适用条件。

- 开始计算或审核输入：读[主入口](SKILL.md)，再按任务加载子技能。
- 物理电子温度、电子熵及 4000 K：读[有限电子温度](references/finite-temperature.md)。本版 `smearing_sigma_temp` 的换算与物理 Ry 标度不一致；双参数的覆盖顺序由 INPUT 行顺序决定。
- 寻找实现证据：读[源码依据](references/source-audit.md)。参数的读取、重置、检查、运行使用和输出应连成调用链，不能仅从手册或变量名判断。
- 实现限制：串行 LCAO、双网格、数值解析、投影谱、波函数后处理、磁态续算、冻结约束、优化标签时序与 LR/RT-TDDFT 的适用条件，见[源码索引](references/source-audit.md)和[验证记录](test-results.md)。
- 具体术语与快速判断：读[术语表](references/glossary.md)与[决策速查](references/cheatsheet.md)。
- 文件起点：读[模板说明](templates/README.md)。模板必须替换占位符、匹配外部数据并做收敛测试，不提供材料无关的“可靠精度”。
- 验证覆盖和限制：读[验证记录](test-results.md)；[行为用例](test-prompts.json)列出后续复核场景。

同一体系的不同基组、展宽、赝势、磁态和泛函可能改变比较的物理量。不能把两个示例总能之差直接等同于基组误差，也不能用示例步数、默认阈值或文件成功写出证明计算可靠。
