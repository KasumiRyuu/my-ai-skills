INPUT_PARAMETERS
# 示意模板：必须填写真实 STRU/KPT/赝势，并对数值设置做收敛测试。
suffix            Si2
ntype             1
pseudo_dir        ./pp
basis_type        pw
calculation       scf

# 截断能单位 Ry。默认 ecutrho=4*ecutwfc 是起点，不保证精度。
ecutwfc           60
# ecutrho         240
scf_thr_type      1                # 倒空间库仑加权残差二次型；不是总能差
scf_thr           1e-9
scf_nmax          100
# nbands          ...              # 默认值按 nspin/电子数决定；有限温度需检验空带尾部

ks_solver         cg               # PW 允许 cg/dav/dav_subspace/bpcg
mixing_type       broyden
# mixing_beta     0.8              # nspin=1 默认；磁性默认 0.4，磁化参数另核对

# 显式选择占据：以下是数值展宽起点，不代表真实电子温度。
smearing_method   gauss
smearing_sigma    0.015            # Ry
# 有带隙且整数填充可改 smearing_method fixed。
# 物理 4000 K：把上面两行改为 fd 与 sigma=0.02533452 Ry。
# v3.10.1 的 smearing_sigma_temp 4000 实际等价 sigma=0.01266726 Ry（FD 约2000 K）。
# 若用 temp 关键词实现物理4000 K，本版本需约8000；优先直接用sigma，勿盲目跨版本沿用。
# sigma/temp 两者同时写时，INPUT 中后出现的行覆盖前者；建议只用一个。

# out_chg 0 默认仍写二进制密度；下面额外保存高精度 cube。
out_chg           1 10
# init_chg        file             # 续算时启用，并确认实际读取的二进制/cube 与体系兼容
# read_file_dir   ./OUT.previous/   # 省略时为 OUT.<suffix>/；./ 表示工作目录
# printe          1                # 逐步打印能量分项（包括熵项）
# cal_force       true             # 用户需要力时启用
# cal_stress      true             # 用户需要应力时启用
