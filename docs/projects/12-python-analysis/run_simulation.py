#!/usr/bin/env python3
"""
项目 12：Python 驱动的 LAMMPS 模拟
=====================================
本脚本演示如何使用 Python 的 lammps 模块来完全控制一个
Lennard-Jones 熔化模拟——从创建盒子到运行到提取结果，
全部在 Python 中完成，无需手动编写 LAMMPS 输入脚本。

运行方式：
    python run_simulation.py

前提条件：
    LAMMPS 已编译并安装，且 Python 绑定可用。
    如果使用系统安装的 LAMMPS，确保 lmp 命令在 PATH 中。
"""

# ============================================================
# 第一部分：导入模块
# ============================================================

# 尝试导入 LAMMPS 的 Python 绑定
# 如果失败，给出友好的提示信息，帮助用户排查问题
try:
    from lammps import lammps  # 导入 lammps 核心类
except ImportError as e:
    # 如果导入失败，打印详细的错误信息和解决方案
    print("=" * 60)
    print("错误：无法导入 LAMMPS Python 模块 (lammps)")
    print("=" * 60)
    print()
    print("可能的原因和解决方案：")
    print()
    print("1. LAMMPS 未安装 Python 绑定：")
    print("   - 如果你通过包管理器安装 LAMMPS，可能没有包含 Python 支持")
    print("   - 需要重新编译 LAMMPS，启用 PYTHON 包：")
    print("     cmake -D PKG_PYTHON=yes ...")
    print()
    print("2. Python 路径未配置：")
    print("   - LAMMPS 的 Python 模块可能安装在非标准路径")
    print("   - 尝试设置环境变量：")
    print("     export PYTHONPATH=/path/to/lammps/lib:$PYTHONPATH")
    print()
    print("3. 虚拟环境问题：")
    print("   - 如果使用 conda 或 venv，确保在正确的环境中")
    print("   - 尝试：pip install lammps")
    print()
    print("4. 检查 LAMMPS 安装：")
    print("   - 在终端运行：lmp -h | grep -i python")
    print("   - 或在 Python 中：import lammps; print(lammps.__file__)")
    print()
    print("原始错误信息：", e)
    print("=" * 60)
    exit(1)

# 导入其他需要的标准库
import os          # 用于文件路径操作
import sys         # 用于获取系统信息
import numpy as np # 用于数值计算（可选，用于后处理）

print("=" * 60)
print("项目 12：Python 驱动的 LAMMPS 模拟")
print("=" * 60)
print()


# ============================================================
# 第二部分：创建 LAMMPS 实例
# ============================================================

# 创建 LAMMPS 实例
# - 参数 ["-log", "none"] 表示不写日志文件（避免和手动运行的日志冲突）
# - 你也可以传入 ["-screen", "none"] 来禁止屏幕输出
# - 还可以指定可执行文件名，例如 lammps(name="lmp")
print("[步骤 1] 创建 LAMMPS 实例...")

# 尝试用 "lmp" 作为可执行文件名创建实例
# 如果你的 LAMMPS 可执行文件叫其他名字（如 lmp_serial、lmpi_g++），
# 请修改这里的参数
try:
    lmp = lammps(cmdargs=["-log", "none", "-screen", "none"])
except Exception as e:
    print(f"  创建实例失败：{e}")
    print("  提示：请检查 'lmp' 命令是否在 PATH 中")
    print("  可以运行 'which lmp' 来确认")
    exit(1)

# 打印 LAMMPS 版本信息，确认实例创建成功
version = lmp.version()
print(f"  LAMMPS 版本：{version}")
print(f"  实例创建成功！")
print()


# ============================================================
# 第三部分：用 command() 方法发送 LAMMPS 命令
# ============================================================
# command() 方法每次发送一行 LAMMPS 命令，就像在输入脚本中写的一样。
# 这是最基本的接口，适合你已经熟悉 LAMMPS 命令语法的情况。

print("[步骤 2] 初始化模拟设置...")

# --- 初始化设置 ---
# units lj：使用 Lennard-Jones 约化单位
lmp.command("units lj")

# dimension 3：三维模拟
lmp.command("dimension 3")

# boundary p p p：三个方向都使用周期性边界条件
lmp.command("boundary p p p")

# atom_style atomic：使用简单的原子模型（无电荷、无键）
lmp.command("atom_style atomic")

# --- 创建原子 ---
# lattice fcc 0.8442：创建面心立方（FCC）格子，约化密度 0.8442
# 这是 LJ 液体在 T*=1.0 附近的典型密度
lmp.command("lattice fcc 0.8442")

# region box block 0 4 0 4 0 4：定义一个 4×4×4 个晶胞的模拟盒子
lmp.command("region box block 0 4 0 4 0 4")

# create_box 1 box：基于 region 创建模拟盒子，1 种原子类型
lmp.command("create_box 1 box")

# create_atoms 1 box：在盒子中按格子填充原子
lmp.command("create_atoms 1 box")

print(f"  原子数：{lmp.get_natoms()}")

# --- 定义势函数 ---
# pair_style lj/cut 2.5：LJ 势函数，截断半径 2.5σ
lmp.command("pair_style lj/cut 2.5")

# pair_coeff 1 1 1.0 1.0 2.5：
#   ε = 1.0（势阱深度）
#   σ = 1.0（原子直径）
#   截断距离 = 2.5
lmp.command("pair_coeff 1 1 1.0 1.0 2.5")

# mass 1 1.0：所有原子的质量设为 1.0
lmp.command("mass 1 1.0")

print("  势函数设置完成：LJ, ε=1.0, σ=1.0, rc=2.5")
print()


# ============================================================
# 第四部分：使用 commands_list() 批量发送命令
# ============================================================
# 对于多行命令，使用 commands_list() 比逐行调用 command() 更高效。
# 所有命令按列表顺序依次执行。

print("[步骤 3] 配置输出和运行参数...")

# 构建命令列表
setup_cmds = [
    # --- 邻居列表设置 ---
    "neighbor 0.3 bin",           # 邻居列表皮肤距离 0.3
    "neigh_modify delay 0 every 1 check yes",  # 每步检查是否需要重建

    # --- 输出热力学信息 ---
    # 每 100 步输出一次温度、压强、能量等
    "thermo 100",
    "thermo_style custom step temp pe ke etotal press vol density",

    # --- 定义用于数据提取的 compute ---
    # compute pe/atom：计算每个原子的势能（后面会用 extract_compute 提取）
    "compute pe all pe/atom",
    # compute ke/atom：计算每个原子的动能
    "compute ke all ke/atom",
    # compute stress/atom：计算每个原子的应力张量
    "compute stress all stress/atom NULL",
    # compute rdf：计算径向分布函数
    # 参数：组 ID，bin 数量，类型对 1-1
    "compute myRDF all rdf 100 1 1",
    # fix ave/time：每隔 100 步对 RDF 做一次平均，写入文件
    "fix rdf_out all ave/time 100 1 100 c_myRDF[*] file rdf.dat mode vector",

    # --- 轨迹输出 ---
    # dump：每 500 步写一次轨迹文件（XYZ 格式）
    "dump myDump all atom 500 dump.lammpstrj",

    # --- 初始速度 ---
    # 在 T*=1.44 下生成 Maxwell-Boltzmann 分布的初始速度
    "velocity all create 1.44 87287 loop geom",
]

# 批量执行这些命令
lmp.commands_list(setup_cmds)
print("  输出和计算设置完成")
print()


# ============================================================
# 第五部分：运行模拟 —— NVT 平衡
# ============================================================

print("[步骤 4] 运行 NVT 平衡（5000 步）...")

# 设置 NVT 系综（等温等容）
# fix nvt：Nosé-Hoover 恒温器
# 参数：组，温度控制方式，起始温度，终止温度，阻尼参数（时间单位）
nvt_cmds = [
    "fix myNVT all nvt temp 1.44 1.44 0.5",
    "timestep 0.005",    # 时间步长 0.005 LJ 时间单位
    "run 5000",          # 运行 5000 步（25 个 LJ 时间单位）
]
lmp.commands_list(nvt_cmds)

# 通过 extract_compute 获取当前温度
# "thermo_temp" 是 LAMMPS 内置的热力学 compute
# style=0 表示全局标量，type=0 表示获取当前值
temp = lmp.extract_compute("thermo_temp", 0, 0)
print(f"  NVT 平衡完成，当前温度 T* = {temp:.4f}")
print()


# ============================================================
# 第六部分：运行模拟 —— NVE 生产运行
# ============================================================

print("[步骤 5] 运行 NVE 生产模拟（10000 步）...")

# 切换到 NVE 系综（微正则系综，总能量守恒）
# 先取消 NVT 的 fix
lmp.command("unfix myNVT")

# 重新定义用于提取数据的 thermo_style（这次包含更丰富的信息）
lmp.command("thermo_style custom step temp pe ke etotal press vol")

# 设置 NVE 系综
nve_cmds = [
    "fix myNVE all nve",
    "run 10000",         # 运行 10000 步
]
lmp.commands_list(nve_cmds)

print(f"  NVE 生产运行完成")
print()


# ============================================================
# 第七部分：从 LAMMPS 中提取数据
# ============================================================
# LAMMPS Python 接口提供了多种数据提取方法。
# 这里演示最常用的几种。

print("[步骤 6] 提取模拟数据...")
print()

# --- 7.1 get_natoms()：获取原子总数 ---
natoms = lmp.get_natoms()
print(f"  原子总数：{natoms}")

# --- 7.2 extract_compute()：提取 compute 的结果 ---
# 参数说明：
#   第 1 个参数：compute 的名称
#   第 2 个参数：style（0=全局，1=每原子，2=每局域）
#   第 3 个参数：type（0=标量，1=矢量，2=数组）
temp = lmp.extract_compute("thermo_temp", 0, 0)
press = lmp.extract_compute("thermo_press", 0, 0)
pe_total = lmp.extract_compute("thermo_pe", 0, 0)
print(f"  温度 T* = {temp:.6f}")
print(f"  压强 P* = {press:.6f}")
print(f"  总势能 PE = {pe_total:.6f}")
print(f"  每原子势能 = {pe_total / natoms:.6f}")

# --- 7.3 extract_atom()：提取原子属性 ---
# 返回指向 LAMMPS 内部数据的指针（ctypes 数组）
# 需要用 numpy 将其转为方便操作的数组

# 提取原子坐标：x[id][3]，id 从 1 开始
x = lmp.extract_atom("x")
# 提取原子速度：v[id][3]
v = lmp.extract_atom("v")

# 将 ctypes 数组转为 numpy 数组，方便处理
# 注意：LAMMPS 的原子索引从 1 开始，但 Python 数组从 0 开始
# 这里我们需要小心处理
coords = np.ctypeslib.as_array(x, shape=(natoms + 1, 3))
vels = np.ctypeslib.as_array(v, shape=(natoms + 1, 3))

# 取前 natoms 个原子的坐标（跳过索引 0）
coords = coords[1:natoms + 1]
vels = vels[1:natoms + 1]

print(f"\n  前 5 个原子的坐标：")
print(f"  {'ID':>4s}  {'x':>10s}  {'y':>10s}  {'z':>10s}")
print(f"  {'-'*40}")
for i in range(5):
    print(f"  {i+1:4d}  {coords[i][0]:10.4f}  {coords[i][1]:10.4f}  {coords[i][2]:10.4f}")

# --- 7.4 gather_atoms()：更方便的原子数据提取 ---
# gather_atoms 返回一个扁平的 numpy 数组
# 比 extract_atom 更安全，自动处理索引问题
x_gathered = lmp.gather_atoms("x", 1, 3)  # 提取 x 坐标，每个原子 3 个分量
v_gathered = lmp.gather_atoms("v", 1, 3)  # 提取速度，每个原子 3 个分量

# reshape 为 (natoms, 3) 的数组
coords_g = np.array(x_gathered).reshape(natoms, 3)
vels_g = np.array(v_gathered).reshape(natoms, 3)

print(f"\n  使用 gather_atoms 提取的前 5 个原子坐标：")
for i in range(5):
    print(f"  {i+1:4d}  {coords_g[i][0]:10.4f}  {coords_g[i][1]:10.4f}  {coords_g[i][2]:10.4f}")

# --- 7.5 extract_global()：提取全局标量 ---
box_vol = lmp.extract_global("boxxhi") - lmp.extract_global("boxxlo")
print(f"\n  模拟盒子 x 方向长度：{box_vol:.4f}")

# --- 7.6 获取盒子信息 ---
# extract_box 返回：(xlo, xhi, ylo, yhi, zlo, zhi, xy, xz, yz, ...)
box_info = lmp.extract_box()
print(f"  盒子范围：")
print(f"    x: [{box_info[0]:.4f}, {box_info[1]:.4f}]")
print(f"    y: [{box_info[2]:.4f}, {box_info[3]:.4f}]")
print(f"    z: [{box_info[4]:.4f}, {box_info[5]:.4f}]")
print()


# ============================================================
# 第八部分：使用 NumPy 进行简单分析
# ============================================================

print("[步骤 7] 使用 NumPy 进行数据分析...")
print()

# --- 8.1 计算质心速度 ---
# 质心速度 = 所有原子速度的平均值
# 在 NVE 系综中，质心速度应接近零（如果初始速度已去除漂移）
com_velocity = np.mean(vels_g, axis=0)
print(f"  质心速度：({com_velocity[0]:.6e}, {com_velocity[1]:.6e}, {com_velocity[2]:.6e})")

# --- 8.2 计算动能分布 ---
# 每个原子的动能 = 0.5 * m * v^2
ke_per_atom = 0.5 * np.sum(vels_g ** 2, axis=1)  # m=1
mean_ke = np.mean(ke_per_atom)
std_ke = np.std(ke_per_atom)
print(f"  平均每原子动能：{mean_ke:.6f} ± {std_ke:.6f}")

# --- 8.3 计算速度分布 ---
# Maxwell-Boltzmann 分布的理论值：<(1/2)mv^2> = (3/2) kT
# 在 LJ 单位中 k_B = 1
theoretical_ke = 1.5 * temp
print(f"  理论平均动能：{theoretical_ke:.6f}")
print(f"  实际/理论 比值：{mean_ke / theoretical_ke:.4f}")

# --- 8.4 计算原子间距离矩阵（前 20 个原子，示意） ---
n_sample = min(20, natoms)
sample_coords = coords_g[:n_sample]

# 计算距离矩阵
# dist[i][j] = |r_i - r_j|
diff = sample_coords[:, np.newaxis, :] - sample_coords[np.newaxis, :, :]
dist_matrix = np.sqrt(np.sum(diff ** 2, axis=2))

print(f"\n  前 {n_sample} 个原子之间的距离矩阵（左上 5x5）：")
print(f"  {'':>8s}", end="")
for j in range(5):
    print(f"  {'atom'+str(j+1):>8s}", end="")
print()
for i in range(5):
    print(f"  {'atom'+str(i+1):>8s}", end="")
    for j in range(5):
        print(f"  {dist_matrix[i][j]:8.4f}", end="")
    print()

# --- 8.5 计算均方位移 (MSD) ---
# MSD = <|r(t) - r(0)|^2>
# 这里我们使用从 NVE 开始保存的初始坐标和当前坐标来估算
# 注意：实际计算 MSD 需要跟踪轨迹，这里只是一个简单的演示
print(f"\n  均方位移（MSD）估算需要轨迹数据，详见 analyze.py")
print()


# ============================================================
# 第九部分：参数扫描示例
# ============================================================
# 使用 Python 可以方便地进行参数扫描——
# 只需修改参数、重新运行即可。

print("[步骤 8] 参数扫描示例：不同密度下的温度...")
print()

# 记录不同密度下的最终温度
density_results = []

# 扫描 3 个密度值
for rho in [0.6, 0.8, 1.0]:
    print(f"  扫描密度 ρ* = {rho}...")

    # 清除旧的模拟设置
    lmp.command("clear")

    # 重新初始化
    lmp.commands_list([
        "units lj",
        "dimension 3",
        "boundary p p p",
        "atom_style atomic",
        f"lattice fcc {rho}",
        "region box block 0 3 0 3 0 3",
        "create_box 1 box",
        "create_atoms 1 box",
        "pair_style lj/cut 2.5",
        "pair_coeff 1 1 1.0 1.0 2.5",
        "mass 1 1.0",
        "velocity all create 1.0 12345 loop geom",
        "fix 1 all nve",
        "timestep 0.003",
        "run 2000",
    ])

    # 提取最终温度
    final_temp = lmp.extract_compute("thermo_temp", 0, 0)
    final_pe = lmp.extract_compute("thermo_pe", 0, 0)
    final_natoms = lmp.get_natoms()

    density_results.append({
        "rho": rho,
        "natoms": final_natoms,
        "temp": final_temp,
        "pe_per_atom": final_pe / final_natoms if final_natoms > 0 else 0,
    })

    print(f"    原子数={final_natoms}, T*={final_temp:.4f}, PE/atom={final_pe/final_natoms:.4f}")

print()
print("  参数扫描结果汇总：")
print(f"  {'ρ*':>6s}  {'N':>6s}  {'T*':>10s}  {'PE/N':>10s}")
print(f"  {'-'*36}")
for r in density_results:
    print(f"  {r['rho']:6.2f}  {r['natoms']:6d}  {r['temp']:10.4f}  {r['pe_per_atom']:10.4f}")
print()


# ============================================================
# 第十部分：清理和关闭
# ============================================================

print("[步骤 9] 清理资源...")

# close() 方法释放 LAMMPS 占用的内存
# 在脚本结束前调用是个好习惯
lmp.close()
print("  LAMMPS 实例已关闭")
print()

print("=" * 60)
print("模拟全部完成！")
print()
print("生成的文件：")
print("  - dump.lammpstrj  （轨迹文件，可用 OVITO 可视化）")
print("  - rdf.dat         （径向分布函数数据）")
print()
print("下一步：")
print("  - 运行 analyze.py 来分析模拟结果")
print("  - 使用 OVITO 打开 dump.lammpstrj 查看轨迹")
print("=" * 60)
