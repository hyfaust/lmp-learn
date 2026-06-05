#!/usr/bin/env python3
"""
项目 12：PyLammps 高级接口演示
================================
PyLammps 是 LAMMPS 的高级 Python 封装，提供了更 Pythonic 的语法。
与底层的 lammps 模块相比，PyLammps：

- 使用属性（attribute）而非 command() 字符串
- 支持链式调用
- 提供更直观的数据访问
- 适合快速原型和交互式探索

运行方式：
    python pylammps_demo.py
    python pylammps_demo.py scan    # 运行参数扫描演示

对比两种接口：
    底层接口:  lmp.command("units lj")
    PyLammps:  L.units("lj")

前提条件：
    LAMMPS 已安装且 Python 绑定可用。
"""

# ============================================================
# 第一部分：导入和初始化
# ============================================================

import sys
import numpy as np

# 尝试导入 PyLammps
# PyLammps 是 lammps 模块的高级封装
try:
    # 从 lammps 模块导入 PyLammps 类和底层 lammps 类
    from lammps import PyLammps, lammps
except ImportError as e:
    # 导入失败时，给出详细的排查建议
    print("=" * 60)
    print("错误：无法导入 LAMMPS Python 模块")
    print("=" * 60)
    print()
    print("PyLammps 需要 LAMMPS 的 Python 绑定。")
    print()
    print("安装/排查步骤：")
    print()
    print("1. 确认 LAMMPS 已安装：")
    print("   which lmp")
    print()
    print("2. 确认 Python 绑定可用：")
    print("   python -c 'import lammps'")
    print()
    print("3. 如果使用 pip 安装：")
    print("   pip install lammps")
    print()
    print("4. 如果从源码编译 LAMMPS：")
    print("   需要启用 PYTHON 包：")
    print("   cmake -D PKG_PYTHON=yes -D PYTHON_EXECUTABLE=$(which python) ...")
    print()
    print("5. 设置库路径：")
    print("   export LD_LIBRARY_PATH=/path/to/lammps/lib:$LD_LIBRARY_PATH")
    print("   export PYTHONPATH=/path/to/lammps/lib/python:$PYTHONPATH")
    print()
    print("原始错误：", e)
    print("=" * 60)
    exit(1)


# ============================================================
# 第二部分：创建 PyLammps 实例
# ============================================================

def 创建实例():
    """
    创建并返回一个 PyLammps 实例。

    PyLammps() 会在内部创建一个底层 lammps 实例。
    可以传入命令行参数来控制 LAMMPS 的行为。
    """
    print("[演示 1] 创建 PyLammps 实例")
    print()

    try:
        # cmdargs 传递给 LAMMPS 的命令行参数
        # "-log none"：不写日志文件
        # "-screen none"：不在屏幕上打印输出
        L = PyLammps(cmdargs=["-log", "none", "-screen", "none"])
    except Exception as e:
        print(f"  创建实例失败：{e}")
        print("  请检查 'lmp' 命令是否在 PATH 中")
        print("  可以运行 'which lmp' 来确认")
        exit(1)

    print(f"  PyLammps 实例创建成功")
    print(f"  实例类型：{type(L).__name__}")
    print()
    return L


# ============================================================
# 第三部分：基本命令语法演示
# ============================================================

def 演示基本命令(L):
    """
    展示 PyLammps 的命令语法，与底层接口做对比。

    PyLammps 的核心思想：LAMMPS 命令名就是 Python 方法名。
    例如：
        LAMMPS 命令          PyLammps 语法
        units lj             L.units("lj")
        boundary p p p       L.boundary("p", "p", "p")
        pair_style lj/cut    L.pair_style("lj/cut", 2.5)
    """
    print("[演示 2] PyLammps 命令语法对比")
    print()
    print("  语法对比：")
    print("  " + "-" * 55)
    print(f"  {'底层接口':<28s}  {'PyLammps':<28s}")
    print("  " + "-" * 55)
    print(f"  {'lmp.command(\"units lj\")':<28s}  {'L.units(\"lj\")':<28s}")
    print(f"  {'lmp.command(\"boundary p p p\")':<28s}  {'L.boundary(\"p\",\"p\",\"p\")':<28s}")
    print(f"  {'lmp.command(\"pair_style lj/cut 2.5\")':<28s}  {'L.pair_style(\"lj/cut\", 2.5)':<28s}")
    print("  " + "-" * 55)
    print()

    # 使用 PyLammps 语法设置基本模拟参数
    # 每个方法调用等价于一行 LAMMPS 命令
    L.units("lj")              # 使用 LJ 约化单位
    L.dimension(3)             # 三维模拟
    L.boundary("p", "p", "p")  # 三方向周期性边界
    L.atom_style("atomic")     # 简单原子模型

    print("  基本设置完成：units=lj, 3D, 周期性边界, atomic")
    print()


# ============================================================
# 第四部分：创建体系
# ============================================================

def 演示创建体系(L):
    """
    演示如何使用 PyLammps 创建一个 LJ 液体体系。
    """
    print("[演示 3] 创建原子体系")
    print()

    # 创建 FCC 格子，约化密度 0.8442
    L.lattice("fcc", 0.8442)

    # 定义模拟区域：4x4x4 个晶胞
    L.region("box", "block", 0, 4, 0, 4, 0, 4)

    # 创建盒子和原子
    L.create_box(1, "box")     # 1 种原子类型
    L.create_atoms(1, "box")   # 在盒子中填充原子

    # 获取体系信息
    # L.system 是 PyLammps 提供的便捷属性
    natoms = L.system.natoms
    print(f"  原子数：{natoms}")

    # 设置势函数
    L.pair_style("lj/cut", 2.5)          # LJ 势，截断 2.5σ
    L.pair_coeff(1, 1, 1.0, 1.0, 2.5)   # ε=1.0, σ=1.0
    L.mass(1, 1.0)                        # 质量=1.0

    print("  势函数：LJ, ε=1.0, σ=1.0, rc=2.5")
    print()


# ============================================================
# 第五部分：运行模拟
# ============================================================

def 演示运行模拟(L):
    """
    演示如何设置和运行模拟。
    """
    print("[演示 4] 设置计算和运行模拟")
    print()

    # 邻居列表设置
    L.neighbor(0.3, "bin")
    L.neigh_modify("delay", 0, "every", 1, "check", "yes")

    # 生成初始速度（T*=1.44，随机种子 87287）
    L.velocity("all", "create", 1.44, 87287, "loop", "geom")

    # 热力学输出设置
    L.thermo(100)  # 每 100 步输出一次
    L.thermo_style("custom", "step", "temp", "pe", "ke", "etotal", "press")

    # 设置 NVT 恒温器并运行
    # fix 命令：对 "all" 组使用 Nosé-Hoover NVT 恒温器
    # 参数：组名, fix类型, 温度控制, 起始温度, 终止温度, 阻尼系数
    L.fix(1, "all", "nvt", "temp", 1.44, 1.44, 0.5)
    L.timestep(0.005)

    print("  运行 NVT 平衡（3000 步）...")
    L.run(3000)
    print("  NVT 平衡完成")
    print()

    # 切换到 NVE 系综
    L.unfix(1)  # 移除 NVT fix
    L.fix(2, "all", "nve")

    print("  运行 NVE 生产模拟（5000 步）...")
    L.run(5000)
    print("  NVE 生产运行完成")
    print()


# ============================================================
# 第六部分：使用 info() 查看体系信息
# ============================================================

def 演示信息查看(L):
    """
    演示如何使用 PyLammps 的信息查询功能。
    """
    print("[演示 5] 查看体系信息")
    print()

    # L.system 提供了便捷的体系信息访问
    print(f"  原子数：{L.system.natoms}")
    print(f"  当前时间步：{L.system.ntimestep}")

    # 也可以通过底层实例获取更多信息
    底层 = L.lmp
    version = 底层.version()
    print(f"  LAMMPS 版本：{version}")

    # 获取盒子信息
    box = 底层.extract_box()
    print(f"  盒子范围：")
    print(f"    x: [{box[0]:.4f}, {box[1]:.4f}]")
    print(f"    y: [{box[2]:.4f}, {box[3]:.4f}]")
    print(f"    z: [{box[4]:.4f}, {box[5]:.4f}]")
    print()


# ============================================================
# 第七部分：查看 compute / fix / variable
# ============================================================

def 演示计算查看(L):
    """
    演示如何查看已定义的 compute、fix、variable。
    """
    print("[演示 6] 查看已定义的计算和约束")
    print()

    # 查看所有 compute
    print("  已定义的 compute：")
    try:
        for c in L.computes:
            print(f"    - {c}")
    except (AttributeError, TypeError):
        print("    （无法获取 computes 列表）")

    # 查看所有 fix
    print("  已定义的 fix：")
    try:
        for f in L.fixes:
            print(f"    - {f}")
    except (AttributeError, TypeError):
        print("    （无法获取 fixes 列表）")

    # 查看所有 variable
    print("  已定义的 variable：")
    try:
        for v in L.variables:
            print(f"    - {v}")
    except (AttributeError, TypeError):
        print("    （无法获取 variables 列表）")

    # 查看运行历史
    print("  运行记录：")
    try:
        for i, run_data in enumerate(L.runs):
            steps = run_data.get("Step", ["?"])
            print(f"    Run {i}: {len(steps)} 数据点")
    except (AttributeError, TypeError):
        print("    （无法获取 runs 列表）")
    print()


# ============================================================
# 第八部分：参数扫描
# ============================================================

def 演示参数扫描():
    """
    演示使用 PyLammps 进行参数扫描。

    参数扫描是 Python 接口最强大的功能之一。
    在纯 LAMMPS 输入脚本中实现参数扫描需要编写复杂的循环，
    而在 Python 中只需一个简单的 for 循环。
    """
    print("[演示 7] 参数扫描——不同密度下的热力学性质")
    print()

    # 定义要扫描的密度值
    densities = [0.5, 0.7, 0.8442, 1.0]
    results = []

    for rho in densities:
        print(f"  扫描密度 ρ* = {rho} ...")

        # 每次循环创建新的 PyLammps 实例
        # 这样可以确保完全干净的状态
        L = PyLammps(cmdargs=["-log", "none", "-screen", "none"])

        # 设置模拟（每次都从头开始）
        L.units("lj")
        L.dimension(3)
        L.boundary("p", "p", "p")
        L.atom_style("atomic")
        L.lattice("fcc", rho)                   # 密度通过 lattice 参数控制
        L.region("box", "block", 0, 3, 0, 3, 0, 3)
        L.create_box(1, "box")
        L.create_atoms(1, "box")
        L.mass(1, 1.0)
        L.pair_style("lj/cut", 2.5)
        L.pair_coeff(1, 1, 1.0, 1.0, 2.5)
        L.velocity("all", "create", 1.0, 12345, "loop", "geom")
        L.fix(1, "all", "nve")
        L.timestep(0.003)

        # 运行模拟
        L.run(2000)

        # 获取结果
        natoms = L.system.natoms
        results.append({
            "rho": rho,
            "natoms": natoms,
        })

        print(f"    原子数 = {natoms}")

        # 关闭实例释放内存
        L.close()

    # 打印结果汇总
    print()
    print("  参数扫描结果汇总：")
    print(f"  {'ρ*':>8s}  {'原子数':>8s}")
    print(f"  {'-'*20}")
    for r in results:
        print(f"  {r['rho']:8.3f}  {r['natoms']:8d}")
    print()
    print("  提示：密度越大，相同盒子中的原子数越多")
    print()


# ============================================================
# 第九部分：与底层接口互操作
# ============================================================

def 演示互操作():
    """
    演示 PyLammps 与底层 lammps 实例的互操作。

    PyLammps 内部持有一个底层 lammps 实例（通过 L.lmp 访问）。
    当 PyLammps 没有提供你需要的高级方法时，
    可以随时回到底层接口。
    """
    print("[演示 8] PyLammps 与底层接口的互操作")
    print()

    # 创建 PyLammps 实例
    L = PyLammps(cmdargs=["-log", "none", "-screen", "none"])

    # 使用 PyLammps 语法设置
    L.units("lj")
    L.dimension(3)
    L.boundary("p", "p", "p")
    L.atom_style("atomic")
    L.lattice("fcc", 0.8442)
    L.region("box", "block", 0, 2, 0, 2, 0, 2)
    L.create_box(1, "box")
    L.create_atoms(1, "box")
    L.pair_style("lj/cut", 2.5)
    L.pair_coeff(1, 1, 1.0, 1.0, 2.5)
    L.mass(1, 1.0)
    L.velocity("all", "create", 1.0, 12345, "loop", "geom")
    L.fix(1, "all", "nve")
    L.timestep(0.005)
    L.run(500)

    # --- 通过底层实例提取数据 ---
    底层 = L.lmp  # 获取底层 lammps 实例
    natoms = L.system.natoms

    # 使用底层的 gather_atoms 方法提取坐标
    x = 底层.gather_atoms("x", 1, 3)  # 提取所有原子的 x,y,z
    coords = np.array(x).reshape(natoms, 3)

    # 使用底层的 extract_compute 方法提取温度
    temp = 底层.extract_compute("thermo_temp", 0, 0)

    print(f"  原子数：{natoms}")
    print(f"  当前温度：{temp:.4f}")
    print(f"  前 3 个原子的坐标：")
    for i in range(min(3, natoms)):
        print(f"    原子 {i+1}: ({coords[i][0]:.4f}, {coords[i][1]:.4f}, {coords[i][2]:.4f})")

    L.close()
    print()


# ============================================================
# 第十部分：PyLammps vs 底层接口对比
# ============================================================

def 打印对比总结():
    """
    打印 PyLammps 和底层接口的对比总结。
    """
    print("[演示 9] PyLammps vs 底层接口对比总结")
    print()
    print("  " + "=" * 58)
    print(f"  {'特性':<18s}  {'PyLammps':<18s}  {'底层 lammps':<18s}")
    print("  " + "-" * 58)
    comparisons = [
        ("命令语法",        "Pythonic",       "字符串 command()"),
        ("数据访问",        "属性/方法",      "extract_* 函数"),
        ("学习难度",        "简单",           "需要了解 C API"),
        ("性能",            "稍慢（有封装层）","最快（直接调用）"),
        ("灵活性",          "高",             "最高"),
        ("调试体验",        "方便",           "需要手动"),
        ("脚本自动化",      "优秀",           "优秀"),
        ("Jupyter 集成",    "原生支持",       "需要额外封装"),
    ]
    for feature, pyl, base in comparisons:
        print(f"  {feature:<18s}  {pyl:<18s}  {base:<18s}")
    print("  " + "=" * 58)
    print()
    print("  选择建议：")
    print("    - 交互式探索、原型开发、教学演示 → PyLammps")
    print("    - 生产级脚本、性能敏感场景 → 底层 lammps 接口")
    print("    - 两者可以混合使用（通过 L.lmp 访问底层实例）")
    print()


# ============================================================
# 主程序入口
# ============================================================

def main():
    """
    主函数：按顺序运行所有演示。
    """
    print("=" * 60)
    print("项目 12：PyLammps 高级接口演示")
    print("=" * 60)
    print()

    # 如果命令行参数为 "scan"，只运行参数扫描演示
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        演示参数扫描()
        return

    # 创建实例
    L = 创建实例()

    # 按顺序运行各个演示
    演示基本命令(L)
    演示创建体系(L)
    演示运行模拟(L)
    演示信息查看(L)
    演示计算查看(L)

    # 关闭当前实例
    L.close()
    print("  实例已关闭")
    print()

    # 参数扫描（会创建新的实例）
    演示参数扫描()

    # 互操作演示
    演示互操作()

    # 对比总结
    打印对比总结()

    print("=" * 60)
    print("PyLammps 演示全部完成！")
    print()
    print("关键要点：")
    print("  1. PyLammps 提供更 Pythonic 的语法，适合快速开发")
    print("  2. 可以通过 L.lmp 随时访问底层实例")
    print("  3. 参数扫描在 Python 中非常自然（for 循环）")
    print("  4. 与 NumPy/Matplotlib 集成方便数据分析")
    print("=" * 60)


if __name__ == "__main__":
    main()
