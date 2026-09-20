---
name: relax
description: 用 ABACUS v3.10.1 优化原子位置或晶胞，设置力/应力和自由度约束，判断优化是否收敛及从结构重开。
license: LGPL-3.0
metadata:
  catalog-hidden: true
  version: 0.2.1
  author: D. Liu
  distilled-on: 2026-09-21
  source: ABACUS v3.10.1 源码核验
  source-repository: https://github.com/deepmodeling/abacus-develop
  source-license: LGPL-3.0
  abacus.capability-id: cap.abacus.relax
---

# 结构优化

先读取并遵循 [完整任务说明](../references/capabilities/abacus-relax.md)，再按用户体系生成输入；该说明以 3.10.1 的参数解析和执行分支为准。

重点检查 `relax_new` 与 `relax_method` 是否匹配、力阈值单位与覆盖关系、受约束的梯度判据，以及输出结构是否有对应的已收敛力/应力。每个实际位移步的 STRU/JSON 都可能与同一步旧几何的力能错位，不限于末步；不能把达到步数上限当成收敛。磁性重开还须核查逐原子磁矩是否保留，不能只恢复几何。

模板：[固定胞](../templates/INPUT.relax.tpl)、[变胞](../templates/INPUT.cell-relax.tpl)。

电子自洽见 [convergence](../convergence/SKILL.md)，结构格式见 [inputs](../inputs/SKILL.md)，实际电子温度见 [有限电子温度](../references/finite-temperature.md)。

运行条件：需要可运行的 ABACUS 环境，并自备目标元素的赝势文件（LCAO 另需数值原子轨道文件）与产物中声明的输入结构。
