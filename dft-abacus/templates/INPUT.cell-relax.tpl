INPUT_PARAMETERS
# ABACUS 3.10.1；按实际 STRU、赝势和 KPT 修改。
# 先收敛截断、k 点、力/应力及 SCF；以下数值仅作起点。
suffix            cell_relax_run
ntype             1
pseudo_dir        ./pp

basis_type        pw
ecutwfc           60               # Ry
scf_thr           1e-8
scf_nmax          100
ks_solver         cg

calculation       cell-relax
relax_method      cg               # 非 cg 自动改用旧版 relax
relax_new         true
relax_nmax        100
force_thr_ev      0.01             # eV/Angstrom；只设一种力阈值
stress_thr        0.5              # kbar，检查约束后的应力梯度
out_stru          true
# cell-relax 自动打开 cal_force/cal_stress。
# 约束见 relax 卡：fixed_axes / fixed_ibrav / fixed_atoms。

symmetry          0
smearing_method   gaussian
smearing_sigma    0.01             # Ry，数值展宽；非电子温度 K
mixing_type       broyden
mixing_beta       0.4
chg_extrap        first-order
# 使用独立 KPT；若改用 kspacing，须另做 k 点收敛。
# 检查结束原因，勿把未计算力的新坐标配上上一构型的能量。
# 该时序也涉及中间步及 JSON；磁性重开需核查逐原子磁矩。
