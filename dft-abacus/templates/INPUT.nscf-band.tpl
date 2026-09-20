INPUT_PARAMETERS
# 普通串行 LCAO lapack 有本版缺陷；使用已验证的 MPI 求解路径。
# 普通半局域 LCAO 的 NSCF 能带骨架；从已收敛 SCF 继承全部物理设置。
# SCF 先用 out_chg 1 10 保存 cube，同时保留配套的 binary/TAU 等文件。
# LCAO Gamma-only binary 的标志可能不兼容；确认回退读取 cube 成功。
suffix            Si2
ntype             1
pseudo_dir        ./pp
orbital_dir       ./orb
read_file_dir     ./OUT.Si2
basis_type        lcao
ecutwfc           60
calculation       nscf
init_chg          file
out_band          1
# nbands          ...              # 继承 SCF 带数，按目标能量窗口与占据尾部检验。
symmetry          0
gamma_only        0
kspacing          0
kpoint_file       KLINES

# 改 read_file_dir 以匹配 SCF 目录；suffix 影响优先读取的 binary 文件名。
# 改结构、电子数、自旋、泛函、电子温度时不能直接复用此示例密度。
# KLINES 必须来自实际晶格；ecutwfc=60 只是示例，应与 SCF 一致。
# LCAO 投影能带可加 out_proj_band 1，输出 PBANDS_1 等。
# PW 需同步改 basis_type/solver/轨道依赖，并测试 pw_diag_thr（如 1e-8）。
