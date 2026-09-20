INPUT_PARAMETERS
# 普通串行 LCAO lapack 有本版缺陷；使用已验证的 MPI 求解路径。
# 普通半局域 LCAO 的 NSCF DOS 骨架；先有相同物理设置下的收敛 SCF。
# SCF 建议 out_chg 1 10，并保存全部自旋与需要的 TAU/其他状态。
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
out_dos           1
# nbands          ...              # 继承 SCF 带数，按目标能量窗口与占据尾部检验。
symmetry          0
gamma_only        0
kspacing          0
kpoint_file       KPT
dos_sigma         0.07
dos_edelta_ev     0.01

# 使用经验证的规则 KPT 网格；DOS 通常需要比 SCF 更密的采样。
# 多 k LCAO 要 PDOS 时把上面的 out_dos 改为 2，不能重复添加同名参数。
# PDOS/PBANDS 需 MPI 构建；实数 Gamma 的 nspin=2 PDOS 峰位有缺陷。
# dos_sigma、dos_edelta_ev 单位 eV，只控制谱，不设置电子温度。
# 继承 SCF 的 nspin、XC、nelec、smearing 等；按能量窗口增加 nbands。
# binary 密度优先于 cube；read_file_dir 与 suffix 必须指向正确的一次 SCF。
