---
name: static
description: >-
  用 ABACUS v3.10.1 做单点 SCF、有限电子温度与电子熵计算，选择基组/求解器/初始化，或核验总能与 SCF 收敛时调用。依据源码区分展宽、电子自由能及两种密度残差判据。
license: LGPL-3.0
metadata:
  version: 0.2.1
  author: D. Liu
  source: ABACUS v3.10.1 source audit
  source-repository: https://github.com/deepmodeling/abacus-develop
  source-license: LGPL-3.0
  abacus.capability-id: cap.abacus.static-scf
---

# 单点 SCF

先读 [完整流程与源码依据](../references/capabilities/abacus-static.md)。涉及电子温度、熵或自由能时，必须同时读 [温度参数与能量口径](../references/finite-temperature.md)。本卡需要可运行的 ABACUS、结构与赝势；LCAO 另需兼容的数值原子轨道。只做配置/审核时无需执行 DFT。

1. 从现有文件和用户目标确认结构、电子数、自旋、赝势/轨道、基组、k 点和精度要求；关键科学条件缺失才提问。
2. 选 [PW 模板](../templates/INPUT.scf-pw.tpl) 或 [LCAO 模板](../templates/INPUT.scf-lcao.tpl)，按真实体系填写。核对求解器构建和实际实现；本版普通串行 LCAO 的默认 lapack 有波函数未回写等缺陷，不能作为可靠基线。
3. 明确数值展宽或物理电子温度。默认是 `gauss 0.015 Ry`，并非固定占据。物理 4000 K 的 FD 计算优先设 `smearing_method fd`、`smearing_sigma 0.02533452`；本版本 `smearing_sigma_temp 4000` 实际产生约 2000 K 的 FD 占据，详见专门说明。
4. 记录 `scf_thr_type`：PW 默认 1（倒空间加权二次型），LCAO 默认 2（无量纲归一化实空间残差）。`scf_ene_thr>0` 是附加条件，不能替代密度收敛。
5. 用兼容密度做续算时，核对 `read_file_dir` 和日志实际读取路径；该版本先读二进制密度，再尝试 cube。默认 `out_chg 0` 仍可写二进制密度，但 LCAO Gamma-only 存在读写标志不一致，不能保证仅凭该文件续算；用 `out_chg 1 10` 另存高精度 cube，按参考卡检查兼容性及回退成功证据。
6. 验收本次最终 SCF 块的收敛状态、有限数值、实际参数与物理目标。仅 `!FINAL_ETOT_IS` 或正常退出不够。FD 下该总能已含占据熵项，应按自由能 F 报告，且不能再重复加 `-TS`。

交付输入及改动理由、实际参数与文件路径、收敛证据、能量名称/单位。有限温度还需报告 sigma、物理电子温度、熵项及空带收敛情况；不得把源码审核写成已完成材料体系实测。

相邻任务：[SCF 排障](../convergence/SKILL.md)、[数值精度](../accuracy/SKILL.md)、[结构优化](../relax/SKILL.md)、[输出判读](../references/capabilities/abacus-output-reading.md)。
