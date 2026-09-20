# 示例 Si 原胞；必须替换为目标结构和实际存在的配套文件。
ATOMIC_SPECIES
Si  28.0855  Si.pz-vbc.UPF

NUMERICAL_ORBITAL
Si_lda_8.0au_50Ry_2s2p1d

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

# LATTICE_CONSTANT 单位 Bohr，晶格行是无量纲向量。
# Cartesian 原子坐标单位为 LATTICE_CONSTANT，不是 Angstrom。
# m 1 1 1 允许移动；固定方向改为 0；SCF 本身不会移动原子。
# NUMERICAL_ORBITAL 每行仅写一个文件名，不能夹行尾注释。
