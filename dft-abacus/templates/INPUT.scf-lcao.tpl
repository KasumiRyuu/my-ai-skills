INPUT_PARAMETERS
# 示意模板：必须填写真实 STRU/KPT/赝势/轨道，并做收敛测试。
suffix            Si2
ntype             1
pseudo_dir        ./pp
orbital_dir       ./orb
basis_type        lcao
calculation       scf

ecutwfc           60               # Ry；影响 FFT/积分精度，轨道基组质量另须检查
scf_thr_type      2                # 实空间归一化 L1 密度残差，无量纲
scf_thr           1e-7
scf_nmax          100
# nbands          ...              # 默认按 nspin/电子数决定且不超过 NLOCAL；高温需检验空带

# 不强制求解器：默认随编译支持/设备选择。
# CPU: 有ELPA用genelpa；无ELPA的MPI版用scalapack_gvx；串行用lapack。
# 本版串行 lapack 有波函数回写/越界缺陷，采用已验证的 MPI 求解路径。
# GPU cusolver/cusolvermp 要核对 CUDA/MPI 及相应编译支持。
mixing_type       broyden
# mixing_beta     0.8              # nspin=1 默认；nspin=2/4 默认0.4，磁化混合另核对

# 以下是默认的数值展宽起点，不是物理电子温度。
smearing_method   gauss
smearing_sigma    0.015            # Ry
# 有带隙且整数填充可改 smearing_method fixed。
# 物理4000 K：把上面两行改为 fd 与 sigma=0.02533452 Ry。
# 本版本 temp4000 -> sigma0.01266726 Ry，实际FD温度约2000 K；不要混淆。
# sigma/temp 同时写时后出现行覆盖前者；建议只留一个，详见 references/finite-temperature.md。

out_chg           1 10             # 默认out_chg0仍写二进制；本行额外写高精度cube
# LCAO Gamma-only binary 有标志兼容问题；保留 cube 并核验续算读取成功。
# init_chg        file             # 续算：先检查旧二进制优先于cube的问题
# read_file_dir   ./OUT.previous/   # 省略时为OUT.<suffix>/；./不是输出目录
# printe          1
# cal_force       true
# cal_stress      true
