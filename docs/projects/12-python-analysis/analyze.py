#!/usr/bin/env python3
"""
项目 12：LAMMPS 模拟数据的 Python 分析
=========================================
本脚本演示如何用 Python（NumPy + Matplotlib）来分析
LAMMPS 模拟产生的数据，包括：

1. 解析 LAMMPS 日志文件（thermo 输出）
2. 读取 RDF（径向分布函数）数据
3. 计算 MSD（均方位移）和扩散系数
4. 绘制多种专业图表

运行方式：
    python analyze.py

前提条件：
    - numpy
    - matplotlib
    - 先运行 run_simulation.py 生成数据文件

注意：如果某些数据文件不存在，脚本会使用示例数据来演示。
"""

# ============================================================
# 第一部分：导入模块
# ============================================================

import os              # 文件路径操作
import sys             # 系统信息
import re              # 正则表达式，用于解析日志文件
import numpy as np     # 数值计算

# 尝试导入 matplotlib，如果未安装则给出提示
try:
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式后端（服务器环境也能用）
    import matplotlib.pyplot as plt
    from matplotlib.ticker import AutoMinorLocator
    HAS_MATPLOTLIB = True
except ImportError:
    print("警告：未安装 matplotlib，将只进行数据计算，不生成图表。")
    print("安装方法：pip install matplotlib")
    HAS_MATPLOTLIB = False

print("=" * 60)
print("项目 12：LAMMPS 数据分析")
print("=" * 60)
print()

# 获取当前脚本所在目录（数据文件也在这里）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# 第二部分：解析 LAMMPS 日志文件
# ============================================================
# LAMMPS 日志文件（log.lammps）包含 thermo 输出数据。
# 但是日志文件中可能包含多次 run 的输出、警告信息等，
# 需要用正则表达式来正确解析。

def parse_lammps_log(filename):
    """
    解析 LAMMPS 日志文件，提取 thermo 输出数据。

    参数：
        filename: 日志文件的路径

    返回：
        dict: 键为列名（如 'Step', 'Temp', 'PotEng' 等），
              值为 numpy 数组。
              如果解析失败，返回 None。

    LAMMPS 日志格式示例：
    ----------------------------------------
    Step Temp PotEng KinEng TotEng Press
         0    1.44   -5.43    2.16   -3.27   -1.23
       100    1.35   -5.50    2.02   -3.48   -1.45
       ...
    ----------------------------------------
    """
    print(f"  解析日志文件：{filename}")

    # 检查文件是否存在
    if not os.path.isfile(filename):
        print(f"  文件不存在：{filename}")
        return None

    with open(filename, 'r') as f:
        content = f.read()

    # 策略：查找 thermo 输出数据块
    # thermo 输出的特征是以列名行开头，后面跟数字行
    # 使用正则表达式匹配

    # 匹配列名行（由字母和空格组成）和数据行（由数字和空格组成）
    # 这个模式匹配 thermo_style custom 输出的数据块
    blocks = re.findall(
        r'^(Step\s+.*\n'           # 列名行：以 "Step" 开头
        r'(?:\s*[\d.eE+\-]+\s+\S.*\n)+)',  # 后面跟多行数字数据
        content,
        re.MULTILINE
    )

    if not blocks:
        # 尝试另一种格式：LAMMPS 可能用不同的 thermo_style
        # 也匹配 "Step" 开头后面跟数字行
        blocks = re.findall(
            r'^(Step\s+.*\n'
            r'(?:\s*[-\d.eE+]+\s+.*\n)+)',
            content,
            re.MULTILINE
        )

    if not blocks:
        print("  警告：未能在日志文件中找到 thermo 数据块")
        print("  提示：请确保模拟使用了 thermo_style custom")
        return None

    # 取最后一个数据块（通常是生产运行的数据）
    last_block = blocks[-1]
    lines = last_block.strip().split('\n')

    # 第一行是列名
    header = lines[0].split()
    print(f"  找到列：{header}")

    # 后面的行是数据
    data_lines = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) == len(header):
            try:
                row = [float(x) for x in parts]
                data_lines.append(row)
            except ValueError:
                continue  # 跳过无法解析的行

    if not data_lines:
        print("  警告：数据块中没有有效数据行")
        return None

    # 转为 numpy 数组并构建字典
    data_array = np.array(data_lines)
    result = {}
    for i, name in enumerate(header):
        result[name] = data_array[:, i]

    print(f"  成功解析 {len(data_lines)} 行数据")
    return result


def parse_lammps_log_simple(filename):
    """
    简化解析方法：查找所有以数字开头的行作为数据行。
    适用于日志格式不标准的情况。

    参数：
        filename: 日志文件路径

    返回：
        dict: 同 parse_lammps_log
    """
    print(f"  使用简化方法解析日志文件：{filename}")

    if not os.path.isfile(filename):
        print(f"  文件不存在：{filename}")
        return None

    header = None
    data_lines = []

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 检测列名行（包含 'Step' 或 'step'）
            if line.startswith('Step') or line.startswith('step'):
                header = line.split()
                data_lines = []  # 新的列名意味着新的数据块
                continue

            # 如果已有列名，尝试解析数据行
            if header is not None:
                parts = line.split()
                if len(parts) == len(header):
                    try:
                        row = [float(x) for x in parts]
                        data_lines.append(row)
                    except ValueError:
                        continue

    if header and data_lines:
        data_array = np.array(data_lines)
        result = {}
        for i, name in enumerate(header):
            result[name] = data_array[:, i]
        print(f"  成功解析 {len(data_lines)} 行数据")
        return result
    else:
        print("  未能解析到数据")
        return None


# ============================================================
# 第三部分：读取 RDF 数据
# ============================================================

def read_rdf_data(filename):
    """
    读取 LAMMPS fix ave/time 输出的 RDF 数据文件。

    LAMMPS 输出的 RDF 文件格式（来自 compute rdf + fix ave/time）：
    ----------------------------------------
    # Time-averaged data for fix rdf_out
    # TimeStep Number-of-rows
    # Row c_myRDF[1] c_myRDF[2] c_myRDF[3] c_myRDF[4]
    100 100
    1 0.005 0.0 0.0 0.0
    2 0.015 0.0 0.0 0.001
    ...
    ----------------------------------------

    参数：
        filename: RDF 数据文件路径

    返回：
        tuple: (r, g_r, coordination) 或 (None, None, None)
               r: 距离数组
               g_r: g(r) 数组
               coordination: 配位数数组（累积）
    """
    print(f"  读取 RDF 数据：{filename}")

    if not os.path.isfile(filename):
        print(f"  文件不存在：{filename}")
        return None, None, None

    # 跳过注释行，读取数据
    r_list = []
    gr_list = []

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            # 跳过注释行和空行
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            # RDF 数据行有 4-5 列：序号 r g(r) coordination ...
            if len(parts) >= 3:
                try:
                    # 第 2 列是 r，第 3 列是 g(r)
                    r_list.append(float(parts[1]))
                    gr_list.append(float(parts[2]))
                except (ValueError, IndexError):
                    continue

    if not r_list:
        print("  未能读取到 RDF 数据")
        return None, None, None

    r = np.array(r_list)
    g_r = np.array(gr_list)

    print(f"  读取了 {len(r)} 个数据点")
    print(f"  r 范围：[{r[0]:.4f}, {r[-1]:.4f}]")
    print(f"  g(r) 最大值：{np.max(g_r):.4f}")

    return r, g_r, None


# ============================================================
# 第四部分：计算均方位移 (MSD) 和扩散系数
# ============================================================

def calculate_msd_from_trajectory(filename, natoms=None, skip_frames=0):
    """
    从 XYZ 轨迹文件计算均方位移（MSD）。

    MSD(t) = <|r(t) - r(0)|^2> = (1/N) * Σ |r_i(t) - r_i(0)|^2

    扩散系数 D = MSD / (6 * t)  （三维空间中）

    参数：
        filename: XYZ 轨迹文件路径
        natoms: 原子数（如果为 None，从文件第一行读取）
        skip_frames: 跳过前 N 帧（用于去除平衡阶段）

    返回：
        tuple: (time_steps, msd_values, diffusion_coeff)
               或 (None, None, None) 如果失败
    """
    print(f"  从轨迹文件计算 MSD：{filename}")

    if not os.path.isfile(filename):
        print(f"  文件不存在：{filename}")
        return None, None, None

    # 读取所有帧的坐标
    frames = []       # 每个元素是一个 (natoms, 3) 的数组
    timesteps = []    # 每帧的时间步

    with open(filename, 'r') as f:
        while True:
            # 读取原子数
            line = f.readline()
            if not line:
                break  # 文件结束
            line = line.strip()
            if not line:
                continue
            try:
                n = int(line)
            except ValueError:
                continue

            # 读取注释行（通常包含时间步信息）
            comment = f.readline().strip()
            # 尝试从注释中提取时间步
            ts_match = re.search(r'(\d+)', comment)
            if ts_match:
                timesteps.append(int(ts_match.group(1)))
            else:
                timesteps.append(len(frames))

            # 读取坐标
            coords = []
            for _ in range(n):
                parts = f.readline().split()
                if len(parts) >= 4:
                    # XYZ 格式：类型 x y z
                    coords.append([float(parts[1]), float(parts[2]), float(parts[3])])

            if len(coords) == n:
                frames.append(np.array(coords))
            else:
                # 如果读取不完整，跳过这一帧
                print(f"  警告：帧 {len(frames)} 读取不完整，跳过")

    if len(frames) < 2:
        print("  轨迹文件中帧数不足（至少需要 2 帧）")
        return None, None, None

    # 跳过平衡阶段
    if skip_frames > 0 and skip_frames < len(frames):
        frames = frames[skip_frames:]
        timesteps = timesteps[skip_frames:]
        print(f"  跳过前 {skip_frames} 帧，剩余 {len(frames)} 帧")

    print(f"  共读取 {len(frames)} 帧，每帧 {len(frames[0])} 个原子")

    # 计算 MSD
    # 使用第一帧作为参考位置
    ref_coords = frames[0]
    n_frames = len(frames)
    msd_values = []

    for i in range(n_frames):
        # 计算位移（不使用最小镜像约定，因为 MSD 应该跟踪实际位移）
        dr = frames[i] - ref_coords
        # MSD = 平均位移的平方
        msd = np.mean(np.sum(dr ** 2, axis=1))
        msd_values.append(msd)

    msd_values = np.array(msd_values)
    time_steps = np.array(timesteps, dtype=float)

    # 如果时间步是数字，转换为实际时间（需要知道时间步长）
    # 这里我们使用时间步差作为时间轴
    dt = time_steps - time_steps[0]

    # 计算扩散系数
    # D = MSD / (6 * t)，只取后半段（线性区域）
    half = len(dt) // 2
    if half > 1 and dt[half] > 0:
        # 对后半段做线性拟合
        # MSD = 6*D*t + b
        coeffs = np.polyfit(dt[half:], msd_values[half:], 1)
        slope = coeffs[0]
        diffusion_coeff = slope / 6.0
        print(f"  扩散系数 D = {diffusion_coeff:.6e} （时间步单位）")
    else:
        diffusion_coeff = None
        print("  数据点不足，无法计算扩散系数")

    return time_steps, msd_values, diffusion_coeff


# ============================================================
# 第五部分：绘图函数
# ============================================================

def plot_thermo_data(data, output_dir):
    """
    绘制热力学量随时间步的变化图。

    图表包含：
    - 温度 (Temperature)
    - 势能 (Potential Energy)
    - 总能量 (Total Energy)
    - 压强 (Pressure)

    参数：
        data: parse_lammps_log 返回的字典
        output_dir: 输出图片的目录
    """
    if not HAS_MATPLOTLIB:
        print("  跳过绘图（matplotlib 未安装）")
        return
    if data is None:
        print("  无数据，跳过绘图")
        return

    print("  绘制热力学量变化图...")

    # 找到步骤列
    step_key = None
    for key in ['Step', 'step']:
        if key in data:
            step_key = key
            break
    if step_key is None:
        print("  数据中没有 Step 列")
        return

    steps = data[step_key]

    # 确定要绘制的物理量
    # (列名, 显示名, 颜色, y轴标签)
    quantities = []
    for col_name, display_name, color, ylabel in [
        ('Temp', 'Temperature', '#e74c3c', r'Temperature $T^*$'),
        ('PotEng', 'Potential Energy', '#2ecc71', r'Potential Energy $PE^*$'),
        ('TotEng', 'Total Energy', '#3498db', r'Total Energy $E^*$'),
        ('Press', 'Pressure', '#9b59b6', r'Pressure $P^*$'),
        ('KinEng', 'Kinetic Energy', '#f39c12', r'Kinetic Energy $KE^*$'),
        ('Volume', 'Volume', '#1abc9c', r'Volume $V^*$'),
    ]:
        if col_name in data:
            quantities.append((col_name, display_name, color, ylabel))

    if not quantities:
        print("  数据中没有可绘制的列")
        return

    # 创建子图
    n_plots = len(quantities)
    n_cols = 2
    n_rows = (n_plots + 1) // 2

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 4 * n_rows))
    # 确保 axes 是二维数组
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    if n_cols == 1:
        axes = axes.reshape(-1, 1)

    fig.suptitle('LAMMPS Simulation: Thermodynamic Quantities',
                 fontsize=14, fontweight='bold')

    for idx, (col_name, display_name, color, ylabel) in enumerate(quantities):
        row = idx // n_cols
        col = idx % n_cols
        ax = axes[row, col]

        ax.plot(steps, data[col_name], color=color, linewidth=0.8, alpha=0.9)
        ax.set_xlabel('Time Step')
        ax.set_ylabel(ylabel)
        ax.set_title(display_name)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())

    # 隐藏多余的子图
    for idx in range(n_plots, n_rows * n_cols):
        row = idx // n_cols
        col = idx % n_cols
        axes[row, col].set_visible(False)

    plt.tight_layout()
    output_file = os.path.join(output_dir, 'thermo_plot.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  已保存：{output_file}")


def plot_rdf(r, g_r, output_dir, title="Radial Distribution Function"):
    """
    绘制径向分布函数 g(r)。

    参数：
        r: 距离数组
        g_r: g(r) 数组
        output_dir: 输出目录
        title: 图表标题
    """
    if not HAS_MATPLOTLIB:
        print("  跳过绘图（matplotlib 未安装）")
        return
    if r is None or g_r is None:
        print("  无 RDF 数据，跳过绘图")
        return

    print("  绘制径向分布函数...")

    fig, ax = plt.subplots(figsize=(8, 5))

    # 绘制 g(r) 曲线
    ax.plot(r, g_r, color='#2c3e50', linewidth=1.5, label='g(r)')

    # 填充曲线下面的区域
    ax.fill_between(r, 0, g_r, alpha=0.15, color='#3498db')

    # 添加参考线 g(r) = 1（理想气体）
    ax.axhline(y=1.0, color='#e74c3c', linestyle='--', linewidth=0.8,
               label='Ideal gas: g(r) = 1')

    # 标注第一峰位置
    if len(g_r) > 0:
        peak_idx = np.argmax(g_r)
        peak_r = r[peak_idx]
        peak_gr = g_r[peak_idx]
        ax.annotate(f'1st peak: r={peak_r:.2f}\ng(r)={peak_gr:.2f}',
                    xy=(peak_r, peak_gr),
                    xytext=(peak_r + 0.5, peak_gr * 0.8),
                    arrowprops=dict(arrowstyle='->', color='#e74c3c'),
                    fontsize=10, color='#e74c3c')

    ax.set_xlabel(r'Distance $r / \sigma$', fontsize=12)
    ax.set_ylabel(r'$g(r)$', fontsize=12)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    output_file = os.path.join(output_dir, 'rdf_plot.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  已保存：{output_file}")


def plot_msd(timesteps, msd, diffusion_coeff, output_dir):
    """
    绘制均方位移（MSD）随时间的变化。

    参数：
        timesteps: 时间步数组
        msd: MSD 数组
        diffusion_coeff: 扩散系数
        output_dir: 输出目录
    """
    if not HAS_MATPLOTLIB:
        print("  跳过绘图（matplotlib 未安装）")
        return
    if timesteps is None or msd is None:
        print("  无 MSD 数据，跳过绘图")
        return

    print("  绘制均方位移...")

    fig, ax = plt.subplots(figsize=(8, 5))

    # 绘制 MSD 曲线
    ax.plot(timesteps, msd, color='#2c3e50', linewidth=1.2, label='MSD(t)')

    # 如果有扩散系数，绘制线性拟合线
    if diffusion_coeff is not None:
        half = len(timesteps) // 2
        t_fit = timesteps[half:]
        # 线性拟合线：MSD = 6*D*t + b
        msd_fit = 6 * diffusion_coeff * (t_fit - timesteps[0])
        # 加上截距（使拟合线经过数据中间）
        offset = msd[half] - msd_fit[0]
        ax.plot(t_fit, msd_fit + offset, color='#e74c3c', linestyle='--',
                linewidth=1.5, label=f'Linear fit (D = {diffusion_coeff:.4e})')

        # 标注线性区域
        ax.axvspan(t_fit[0], t_fit[-1], alpha=0.08, color='#e74c3c',
                   label='Linear region')

    ax.set_xlabel('Time Step', fontsize=12)
    ax.set_ylabel(r'MSD $(\sigma^2)$', fontsize=12)
    ax.set_title('Mean Square Displacement', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_file = os.path.join(output_dir, 'msd_plot.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  已保存：{output_file}")


def plot_velocity_distribution(velocities, output_dir, temperature=None):
    """
    绘制速度分布图，并与 Maxwell-Boltzmann 理论分布对比。

    Maxwell-Boltzmann 分布（三维）：
    f(v) = 4π (m/2πkT)^(3/2) * v^2 * exp(-mv^2/2kT)

    参数：
        velocities: 速度数组，形状 (natoms, 3)
        output_dir: 输出目录
        temperature: 温度（用于理论曲线，LJ 单位中 k_B=1）
    """
    if not HAS_MATPLOTLIB:
        print("  跳过绘图（matplotlib 未安装）")
        return
    if velocities is None:
        print("  无速度数据，跳过绘图")
        return

    print("  绘制速度分布...")

    # 计算速率 |v| = sqrt(vx^2 + vy^2 + vz^2)
    speeds = np.sqrt(np.sum(velocities ** 2, axis=1))

    fig, ax = plt.subplots(figsize=(8, 5))

    # 绘制速度直方图
    n_bins = 50
    counts, bin_edges, patches = ax.hist(speeds, bins=n_bins, density=True,
                                          alpha=0.7, color='#3498db',
                                          edgecolor='white', linewidth=0.5,
                                          label='Simulation data')

    # 绘制 Maxwell-Boltzmann 理论曲线
    if temperature is not None:
        v = np.linspace(0, np.max(speeds) * 1.1, 200)
        # 三维 Maxwell-Boltzmann 分布（m=1, k_B=1）
        # f(v) = 4π (1/2πT)^(3/2) * v^2 * exp(-v^2/2T)
        T = temperature
        f_v = 4 * np.pi * (1.0 / (2 * np.pi * T)) ** 1.5 * v ** 2 * np.exp(-v ** 2 / (2 * T))
        ax.plot(v, f_v, color='#e74c3c', linewidth=2,
                label=f'Maxwell-Boltzmann (T*={T:.2f})')

    ax.set_xlabel(r'Speed $|v|$', fontsize=12)
    ax.set_ylabel(r'Probability density', fontsize=12)
    ax.set_title('Velocity Distribution', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_file = os.path.join(output_dir, 'velocity_dist.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  已保存：{output_file}")


def plot_energy_conservation(data, output_dir):
    """
    绘制能量守恒图——检查 NVE 系综中总能量是否守恒。

    在 NVE 系综中，总能量应该基本不变（数值误差范围内）。
    能量漂移量 |ΔE/E_0| 应该远小于 1。

    参数：
        data: 日志数据字典
        output_dir: 输出目录
    """
    if not HAS_MATPLOTLIB:
        return
    if data is None or 'TotEng' not in data:
        return

    print("  绘制能量守恒检查图...")

    steps = data.get('Step', np.arange(len(data['TotEng'])))
    total_energy = data['TotEng']

    # 计算相对能量漂移
    E0 = total_energy[0]
    if abs(E0) > 1e-10:
        relative_drift = (total_energy - E0) / abs(E0)
    else:
        relative_drift = total_energy - E0

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # 上图：总能量
    ax1.plot(steps, total_energy, color='#2c3e50', linewidth=0.8)
    ax1.set_ylabel(r'Total Energy $E^*$', fontsize=12)
    ax1.set_title('Energy Conservation Check (NVE)', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # 标注能量漂移
    drift_info = f'E_0 = {E0:.6f}\n|ΔE/E_0| = {np.max(np.abs(relative_drift)):.2e}'
    ax1.text(0.02, 0.98, drift_info, transform=ax1.transAxes,
             verticalalignment='top', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 下图：相对能量漂移
    ax2.plot(steps, relative_drift, color='#e74c3c', linewidth=0.8)
    ax2.set_xlabel('Time Step', fontsize=12)
    ax2.set_ylabel(r'Relative Drift $\Delta E / E_0$', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)

    plt.tight_layout()
    output_file = os.path.join(output_dir, 'energy_conservation.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  已保存：{output_file}")


# ============================================================
# 第六部分：生成示例数据（当真实数据不存在时）
# ============================================================

def generate_sample_log_data():
    """
    生成模拟 LAMMPS 日志的示例数据。
    用于演示绘图功能，当真实模拟数据不存在时使用。
    """
    print("  生成示例数据用于演示...")
    np.random.seed(42)

    n_steps = 200
    steps = np.arange(0, n_steps * 100, 100, dtype=float)

    # 模拟温度：从高温平衡到目标温度
    T_target = 1.0
    T_init = 1.44
    temp = T_target + (T_init - T_target) * np.exp(-steps / 5000)
    temp += np.random.normal(0, 0.05, n_steps) * np.sqrt(T_target / n_steps)

    # 模拟势能：随温度降低而降低
    pe = -5.5 + 0.3 * (temp - T_target) + np.random.normal(0, 0.02, n_steps)

    # 模拟动能：与温度成正比 (3/2) NkT
    ke = 1.5 * temp + np.random.normal(0, 0.01, n_steps)

    # 总能量
    etotal = pe + ke

    # 压强
    press = -1.0 + 0.5 * (temp - T_target) + np.random.normal(0, 0.1, n_steps)

    # 体积（NPT 下会变化，这里模拟基本不变）
    volume = np.full(n_steps, 512.0) + np.random.normal(0, 0.5, n_steps)

    return {
        'Step': steps,
        'Temp': temp,
        'PotEng': pe,
        'KinEng': ke,
        'TotEng': etotal,
        'Press': press,
        'Volume': volume,
    }


def generate_sample_rdf_data():
    """
    生成示例 RDF 数据。
    模拟 LJ 液体的典型 g(r) 曲线。
    """
    print("  生成示例 RDF 数据...")
    np.random.seed(42)

    r = np.linspace(0.01, 4.0, 400)
    # 简单的 g(r) 模型：用高斯峰模拟
    rho = 0.8442  # LJ 液体密度

    # 基础值（理想气体 g(r)=1）
    g_r = np.ones_like(r)

    # 第一峰（最近邻壳层）
    g_r += 1.8 * np.exp(-((r - 1.09) / 0.12) ** 2)
    # 第二峰
    g_r += 0.6 * np.exp(-((r - 2.0) / 0.2) ** 2)
    # 第三峰（弱）
    g_r += 0.2 * np.exp(-((r - 3.0) / 0.25) ** 2)

    # 硬核排斥区（r < σ 时 g(r) → 0）
    g_r[r < 0.95] *= np.exp(-((0.95 - r[r < 0.95]) / 0.05) ** 2)

    # 添加少量噪声
    g_r += np.random.normal(0, 0.02, len(r))
    g_r = np.maximum(g_r, 0)  # g(r) 不能为负

    return r, g_r


def generate_sample_trajectory_data():
    """
    生成示例轨迹数据（简化，仅用于演示 MSD 计算）。
    """
    print("  生成示例轨迹数据...")
    np.random.seed(42)

    n_atoms = 32
    n_frames = 200
    dt = 0.005  # 时间步长

    # 生成随机行走轨迹（模拟扩散）
    D = 0.05  # 扩散系数
    sigma = np.sqrt(2 * D * dt)

    # 初始位置（随机分布在立方盒子中）
    L = 5.0  # 盒子边长
    positions = np.random.uniform(0, L, (n_atoms, 3))

    all_frames = [positions.copy()]
    for _ in range(n_frames - 1):
        # 每步添加随机位移
        displacement = np.random.normal(0, sigma, (n_atoms, 3))
        positions += displacement
        all_frames.append(positions.copy())

    return all_frames, n_atoms


# ============================================================
# 第七部分：主程序
# ============================================================

def main():
    """
    主函数：依次执行数据读取、分析和绘图。
    """
    output_dir = SCRIPT_DIR  # 图片输出到脚本所在目录

    print()
    print("-" * 60)
    print("[分析 1] 解析 LAMMPS 日志文件")
    print("-" * 60)

    # 尝试解析日志文件
    # 优先查找当前目录下的 log.lammps
    log_file = os.path.join(SCRIPT_DIR, 'log.lammps')
    if not os.path.isfile(log_file):
        # 也查找上一级目录
        log_file = os.path.join(SCRIPT_DIR, '..', 'log.lammps')

    log_data = parse_lammps_log(log_file)

    if log_data is None:
        print("  未找到日志文件，使用示例数据演示...")
        log_data = generate_sample_log_data()

    print()

    print("-" * 60)
    print("[分析 2] 绘制热力学量变化图")
    print("-" * 60)
    plot_thermo_data(log_data, output_dir)
    print()

    print("-" * 60)
    print("[分析 3] 分析径向分布函数 (RDF)")
    print("-" * 60)

    # 尝试读取 RDF 数据
    rdf_file = os.path.join(SCRIPT_DIR, 'rdf.dat')
    r, g_r, _ = read_rdf_data(rdf_file)

    if r is None:
        print("  未找到 RDF 文件，使用示例数据演示...")
        r, g_r = generate_sample_rdf_data()

    plot_rdf(r, g_r, output_dir)
    print()

    print("-" * 60)
    print("[分析 4] 计算均方位移 (MSD)")
    print("-" * 60)

    # 尝试从轨迹文件计算 MSD
    traj_file = os.path.join(SCRIPT_DIR, 'dump.lammpstrj')
    timesteps, msd, D = calculate_msd_from_trajectory(traj_file)

    if timesteps is None:
        print("  未找到轨迹文件，使用示例数据演示...")
        frames, n_atoms = generate_sample_trajectory_data()

        # 手动计算 MSD
        ref = frames[0]
        msd_list = []
        ts_list = []
        for i, frame in enumerate(frames):
            dr = frame - ref
            msd_val = np.mean(np.sum(dr ** 2, axis=1))
            msd_list.append(msd_val)
            ts_list.append(i * 100)

        timesteps = np.array(ts_list, dtype=float)
        msd = np.array(msd_list)

        # 计算扩散系数
        half = len(timesteps) // 2
        dt = timesteps[half:] - timesteps[0]
        if dt[-1] > 0:
            coeffs = np.polyfit(dt, msd[half:], 1)
            D = coeffs[0] / 6.0
            print(f"  扩散系数 D = {D:.6e}")
        else:
            D = None

    plot_msd(timesteps, msd, D, output_dir)
    print()

    print("-" * 60)
    print("[分析 5] 绘制速度分布")
    print("-" * 60)

    # 生成示例速度数据（实际应从模拟中提取）
    np.random.seed(42)
    T = 1.0  # LJ 单位中的温度
    n_atoms = 256
    # Maxwell-Boltzmann 分布的速度分量：高斯分布，标准差 sqrt(kT/m)
    sample_velocities = np.random.normal(0, np.sqrt(T), (n_atoms, 3))
    plot_velocity_distribution(sample_velocities, output_dir, temperature=T)
    print()

    print("-" * 60)
    print("[分析 6] 能量守恒检查")
    print("-" * 60)

    # 如果日志数据包含总能量，绘制能量守恒图
    if log_data is not None and 'TotEng' in log_data:
        plot_energy_conservation(log_data, output_dir)
    else:
        print("  无总能量数据，跳过能量守恒检查")
    print()

    # ============================================================
    # 汇总
    # ============================================================
    print("=" * 60)
    print("数据分析完成！")
    print()
    print("生成的图表：")

    # 列出所有生成的图片文件
    for fname in sorted(os.listdir(output_dir)):
        if fname.endswith('.png'):
            fpath = os.path.join(output_dir, fname)
            fsize = os.path.getsize(fpath)
            print(f"  - {fname}  ({fsize / 1024:.1f} KB)")

    print()
    print("提示：")
    print("  - 这些图表是用示例数据生成的")
    print("  - 先运行 run_simulation.py 生成真实数据")
    print("  - 然后重新运行 analyze.py 来分析真实模拟结果")
    print("=" * 60)


# 当脚本直接运行时，执行 main 函数
if __name__ == "__main__":
    main()
