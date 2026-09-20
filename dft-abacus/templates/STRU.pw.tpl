# 示例 Si 原胞；普通 PW 不需要 NUMERICAL_ORBITAL。
# PW 若使用 NAO 初始化或 onsite 投影等额外功能，需要另补轨道文件。
ATOMIC_SPECIES
Si  28.0855  Si.pz-vbc.UPF

LATTICE_CONSTANT
10.2

LATTICE_VECTORS
0.5 0.5 0.0
0.5 0.0 0.5
0.0 0.5 0.5

ATOMIC_POSITIONS
Cartesian
Si
0.0
2
0.00 0.00 0.00 m 1 1 1
0.25 0.25 0.25 m 1 1 1

# 实际晶格 = LATTICE_CONSTANT（Bohr）乘以上三个晶格行。
# Cartesian 原子坐标单位为 LATTICE_CONSTANT；不是 Angstrom。
# 替换结构与实际赝势文件；m 的 1 允许移动、0 固定。
