---
name: accuracy
description: 为 ABACUS 3.10.1 选择并验证 PW/LCAO 基组、截断能、k 点、赝势/轨道和空带数的数值精度；用于收敛测试，不用于单次 SCF 迭代排障。
license: LGPL-3.0
metadata:
  version: 0.2.1
  author: D. Liu
  audited-on: 2026-09-21
  source: ABACUS v3.10.1 source implementation
  source-repository: https://github.com/deepmodeling/abacus-develop
  source-license: LGPL-3.0
  abacus.capability-id: cap.abacus.accuracy
---

# 数值精度

先读 [基组、截断、k 点与空带数](../references/capabilities/abacus-accuracy.md)。区分输入默认值、程序的硬约束和需要按体系实测的精度选择。

1. 明确目标量、可接受误差、结构/电子温度/磁态、已有赝势与轨道；用现有信息拟定扫描，不把默认值或模板值直接认定为收敛值。
2. PW 收敛 `ecutwfc`；LCAO 分别检查轨道空间和网格/积分参数。LCAO 提高 `ecutwfc` 仍可能显著改变结果，且未显式设置的 `lcao_ecut` 会随之改变。
3. `ecutwfc`、`ecutrho` 单位 Ry；`ecutrho` 默认 `4*ecutwfc`，正值比率低于 4 会终止。独立密度网格测试按基组分支判断：本版 LCAO 双网格有尺寸缺陷，手工 ndz 的开关检查也有笔误，先读参考卡。超软赝势不能靠固定倍数保证精度。
4. k 网格按方向及物理维度加密；`kspacing` 是带 `2π` 的倒空间间距，单位 Bohr⁻¹。记录实际生成的 KPT 和最终 k 点，避免自动设置覆盖路径或网格。
5. 展宽、电子温度、空带数、SCF/本征求解精度也会影响比较。固定目标电子温度做数值测试，勿为收敛方便改变用户要研究的温度。4000 K 的热电子设置见 [static](../static/SKILL.md)。
6. 每个比较点都先确认 SCF 收敛，再比较同一物理量；固定赝势、轨道、泛函、磁态、单位与每原子归一化口径。最终交付参数、实际采样、收敛表与资源文件的可追溯记录。

[SCF 迭代排障](../convergence/SKILL.md) 与数值完备性测试不同；二者都通过才可据此评估精度。模板位于 [templates](../templates/README.md)，其数值只是起点。
