INPUT_PARAMETERS
# ABACUS 3.10.1；按实际 STRU、赝势、轨道和 KPT 修改。
# 数值是起点，须先收敛力与电子自洽精度。
suffix            relax_run
ntype             1
pseudo_dir        ./pp
orbital_dir       ./orb

basis_type        lcao
# 普通串行 LCAO lapack 有本版缺陷；使用已验证的 MPI 求解路径。
ecutwfc           60               # Ry
scf_thr           1e-7             # 非通用 Ry 能量阈值，见收敛卡
scf_nmax          100

calculation       relax
relax_method      cg
relax_new         true
relax_nmax        50
force_thr_ev      0.01             # eV/Angstrom；不同时设置 force_thr
out_stru          true             # 额外保存逐步 STRU_ION<step>_D

symmetry          0
mixing_type       broyden
mixing_beta       0.4
chg_extrap        first-order
smearing_method   gaussian         # 数值展宽；真实电子温度另用 FD
smearing_sigma    0.01             # Ry，须收敛；不是电子温度 K
# 每个发生位移的步，输出结构都可能与同一步力能错位。
# 达到上限不等于收敛；磁性重开需核查逐原子磁矩。
