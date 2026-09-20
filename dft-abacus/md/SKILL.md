---
name: md
description: 配置 ABACUS v3.10.1 的 AIMD 系综、离子温度、步长、轨迹输出和断点续算；区分电子温度与离子温度。
license: LGPL-3.0
metadata:
  catalog-hidden: true
  version: 0.2.1
  author: D. Liu
  distilled-on: 2026-09-21
  source: ABACUS v3.10.1 源码核验
  source-repository: https://github.com/deepmodeling/abacus-develop
  source-license: LGPL-3.0
  abacus.capability-id: cap.abacus.md
---

# 分子动力学

先读取并遵循 [完整任务说明](../references/capabilities/abacus-md.md)，再按用户体系生成输入；该说明以 3.10.1 的参数解析和执行分支为准。

重点检查电子/离子温度、初速度重缩放、控压频率单位、累计步数和 checkpoint 文件布局。`MD_dump` 的 `VIRIAL` 是 kbar。FIRE 的阈值被覆盖且判停包含冻结分量；MSST 速度更新不屏蔽冻结方向；NPT/MSST 不执行 relax 的晶胞约束。磁性续算须核查输出 STRU 的逐原子磁矩或兼容磁化密度，几何 checkpoint 不自动保存磁态。

模板：[INPUT.md](../templates/INPUT.md.tpl)。

电子自洽见 [convergence](../convergence/SKILL.md)，结构格式见 [inputs](../inputs/SKILL.md)，实际电子温度见 [有限电子温度](../references/finite-temperature.md)。

运行条件：需要可运行的 ABACUS 环境，并自备目标元素的赝势文件（LCAO 另需数值原子轨道文件）与产物中声明的输入结构。
