---
name: convergence
description: >-
  ABACUS 的 SCF 不收敛、缓慢、密度或能量振荡，或需要调整混合/展宽/空带/早停与续算时调用。依据 v3.10.1 源码识别密度判据、磁化混合及有限温度边界。
license: LGPL-3.0
metadata:
  version: 0.2.1
  author: D. Liu
  source: ABACUS v3.10.1 source audit
  source-repository: https://github.com/deepmodeling/abacus-develop
  source-license: LGPL-3.0
  abacus.capability-id: cap.abacus.convergence
---

# SCF 收敛与排障

先读 [排障流程与源码依据](../references/capabilities/abacus-convergence.md)。本卡处理电子自洽迭代；若内层已收敛而外层优化/轨迹有问题，转对应任务。仅审核日志和输入时无需执行 DFT；实际运行需有效结构、赝势和相应基组资源。

1. 从现有输入和日志提取 DRHO/EDIFF、对角化警告、磁矩、占据和实际参数。确认是持续缓慢下降、振荡还是停滞；不必为排障先重跑默认输入。
2. 记录 `scf_thr_type`。类型 1 是倒空间加权二次型；类型 2 是无量纲实空间残差。`scf_ene_thr` 是额外的 `DeltaE_womix` 条件，不是 EDIFF 的别名。
3. 对不稳定迭代评估减小 `mixing_beta`、磁化混合与预处理；Kerker 压制小 G 长波长分量，并在 `mixing_beta<=0.1` 时跳过。增大历史长度不保证更好。
4. 对占据问题检查 k 点、空带和展宽；指定物理温度时用 FD 并保持目标温度。务必读 [本版本温度转换与熵](../references/finite-temperature.md)，不能用高斯/MP 修正冒充物理电子熵。
5. `scf_os_stop` 是可选趋势早停，会把缓慢下降也截停；不等于收敛。若残差持续下降，预算内提高 `scf_nmax` 或兼容续算可以合理。
6. 区分混合历史重建 `mixing_restart`、密度初始化 `init_chg file` 与独立文件机制 `restart_load`。DFT+U 的 U-ramping/DMR 混合是分支受限的可选策略。

每轮保留输入 diff、残差变化、收敛步数和最终物理态。交付本次最终 SCF 块的收敛证据；到上限或早停时不能因出现总能/时间尾行就宣布成功。最后按目标量做 [精度测试](../accuracy/SKILL.md)。

相关资源：[静态 SCF](../static/SKILL.md)、[输出判读](../references/capabilities/abacus-output-reading.md)、[PW 模板](../templates/INPUT.scf-pw.tpl)、[LCAO 模板](../templates/INPUT.scf-lcao.tpl)。
