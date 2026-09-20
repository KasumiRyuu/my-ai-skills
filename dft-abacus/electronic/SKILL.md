---
name: electronic
description: 设置 ABACUS 3.10.1 的能带、DOS/PDOS、电荷/势、波函数、H/S 矩阵、Mulliken、Wannier90 和 Berry phase 输出，核对 SCF 到 NSCF 的数据复用及输出含义。
license: LGPL-3.0
metadata:
  version: 0.2.1
  author: D. Liu
  audited-on: 2026-09-21
  source: ABACUS v3.10.1 source implementation
  source-repository: https://github.com/deepmodeling/abacus-develop
  source-license: LGPL-3.0
  abacus.capability-id: cap.abacus.electronic
---

# 电子结构与输出

先读 [电子结构流程与输出语义](../references/capabilities/abacus-electronic.md)，按目标选择流程。能带/加密网格 DOS 通常用 SCF → NSCF；电荷、势、H/S 和 Mulliken 可以直接在 SCF 输出；只取 S 的 `get_S` 无需收敛电荷。

1. 对普通半局域泛函的能带/DOS，核对已经收敛的 SCF，保留结构、赝势、轨道、泛函、自旋和电子数。`out_chg 1 10` 生成便于检查和复用的 cube；本版默认还写二进制密度。
2. NSCF 明确 `read_file_dir` 与 `suffix`。程序强制 `init_chg=file`，读取失败会终止，不能退回原子密度。binary 比 cube 优先；不要让旧 binary 遮蔽目标 cube。LCAO Gamma-only binary 有本版标志不一致问题，需保存 cube 并核对实际回退读取成功。多自旋和 meta-GGA 需保留全部密度分量及 TAU；DFT+U/杂化不能套用“只有一个 cube 即足够”。
3. 能带用 [INPUT.nscf-band.tpl](../templates/INPUT.nscf-band.tpl) 与 [KLINES.example](../templates/KLINES.example)：`gamma_only 0`、`kspacing 0`、`symmetry 0` 或 `-1`，路径须匹配实际晶格。
4. DOS 用 [INPUT.nscf-dos.tpl](../templates/INPUT.nscf-dos.tpl) 与收敛的规则网格。普通多 k LCAO 的 PDOS 用 `out_dos 2`；投影 DOS/PBANDS 需 MPI 构建，Gamma-only nspin=2 的 PDOS 下自旋峰位有本版缺陷。`dos_sigma` 是谱线高斯展宽（eV），不设置电子温度；`.bxsf` writer 不完整，不作为即用费米面方案。
5. 验收时核对数据内容、单位、k 点和能量零点。`BANDS_*.dat` 的能量未自动减费米能；`DOS*_smearing.dat` 第三列是未乘能量步长的累计和；LCAO 投影能带文件叫 `PBANDS_*`。
6. 波函数、矩阵、Wannier90 和 Berry phase 依照参考中的基组、构建和自旋限制设置。PW 多 k 波函数后处理用 `mem_saver 0`；PW 部分电荷、Berry 与 Wannier90 要有效 KPAR=1。LCAO nspin=4 的 Berry 电子相位未实现；UNK 与部分电荷还有各自限制，不能把输入接受或文件存在当成可用证明。
7. 核对部分电荷的实际权重、PW 实空间模平方的体积归一化；cube 读取成功也不验证数据完整性和几何相容。

前置工作见 [输入文件](../inputs/SKILL.md)、[SCF](../static/SKILL.md) 和 [精度](../accuracy/SKILL.md)；磁性/SOC 与高级泛函分别见 [磁性](../references/capabilities/abacus-magnetism-soc.md)、[高级泛函](../references/capabilities/abacus-advanced-functionals.md)。
