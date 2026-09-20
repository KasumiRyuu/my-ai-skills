INPUT_PARAMETERS
# ABACUS 3.10.1；按实际 STRU、赝势、轨道和 KPT 修改。
# 这是短程 NVE 验证起点，非已收敛的生产轨迹配置。
suffix            md_nve
ntype             1
pseudo_dir        ./pp
orbital_dir       ./orb

basis_type        lcao
ecutwfc           60               # Ry
scf_thr           1e-7             # 以力误差和能量漂移收敛测试
scf_nmax          100
# ks_solver 省略，按实际编译/设备选择；核对运行日志。
# 本版普通串行 LCAO lapack 有已知缺陷，需已验证的 MPI 求解路径。

calculation       md
md_type           nve
md_nstep          10               # 目标累计步号；包含初始第 0 帧
md_dt             1                # fs；须按最快振动做步长测试
md_tfirst         300              # K，离子初温
init_vel          false            # 随机初速；读速度时注意重新缩放
md_seed           42
md_dumpfreq       1
md_restartfreq    5
cal_stress        true             # 输出 MD_dump 的 VIRIAL(kbar)
# NVT：md_type nvt，另设 md_thermostat nhc 与 md_tlast。
# NPT：另给 md_pmode、md_pfirst/md_plast（kbar）。
# NPT/MSST 不执行 relax 的 fixed_axes/fixed_ibrav 约束。
# md_tfreq/md_pfreq 单位 fs^-1；续算见 MD 卡的文件布局。

symmetry          0
gamma_only        false            # 使用 KPT；不能自动假定大胞只需 Gamma
smearing_method   fd
smearing_sigma    0.00190009        # Ry，约 300 K 电子温度；独立于离子温度
# 此版 smearing_sigma_temp 有二倍换算问题，见有限温度卡。
# 固定电子温度 NVE 检查 K_ion + F_electronic 漂移。
mixing_type       broyden
mixing_beta       0.3
chg_extrap        second-order
# 默认输出结构不保留逐原子磁矩；磁性续算按磁性卡核验。
