---

# 项目 12：Python 接口与数据分析

---

## 学习目标

完成本项目后，你将能够：

1. **理解 LAMMPS Python 接口的架构和用途**：知道为什么需要 Python 接口、它与传统输入脚本的区别、以及两种 Python 接口（底层 `lammps` 模块和高级 `PyLammps`）各自的适用场景。
2. **掌握用 Python 驱动 LAMMPS 模拟的完整流程**：能够创建 LAMMPS 实例、发送命令、设置模拟参数、运行模拟、并提取计算结果，全程在 Python 中完成。
3. **学会从 LAMMPS 中提取各种数据**：掌握 `extract_atom`、`extract_compute`、`gather_atoms` 等核心方法的参数含义和使用场景，能够将模拟数据转为 NumPy 数组进行后续处理。
4. **能够用 Python 对模拟数据进行后处理和可视化**：掌握日志文件解析、RDF/MSD 数据读取、速度分布分析等常见后处理任务，并使用 Matplotlib 绘制专业的科学图表。
5. **能够使用 Python 进行参数扫描和自动化工作流**：理解如何利用 Python 的循环和函数封装来实现参数扫描、批量运行和结果汇总，建立从模拟到分析的完整自动化流程。

---

## 背景知识

### 为什么使用 Python

#### 从一个问题开始

假设你正在研究 LJ 液体的性质，需要在 10 个不同温度下各运行一次模拟，然后提取温度、能量、RDF 等数据，最后画图比较。如果用传统的 LAMMPS 输入脚本，你可能需要：

1. 编写一个输入脚本模板
2. 用 Shell 脚本替换模板中的温度参数，生成 10 个输入脚本
3. 分别运行这 10 个脚本
4. 从 10 个日志文件中手动提取数据
5. 把数据整理成表格
6. 用其他工具（如 Excel、Origin）画图

这个过程繁琐、容易出错、且难以复用。

**使用 Python 接口**，同样的工作可以在一个脚本中完成：

```python
for T in [0.5, 0.7, 0.9, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 3.5]:
    lmp = lammps()
    # ... 设置模拟 ...
    lmp.command(f"velocity all create {T} 12345 loop geom")
    lmp.command(f"fix 1 all nvt temp {T} {T} 0.5")
    lmp.command("run 10000")
    temp = lmp.extract_compute("thermo_temp", 0, 0)
    results.append({"T": T, "actual_T": temp})
    lmp.close()

# 直接在 Python 中画图
plt.plot([r["T"] for r in results], [r["actual_T"] for r in results])
plt.savefig("scan.png")
```

#### Python 接口的优势

| 场景 | 传统方式 | Python 方式 |
|------|---------|------------|
| 参数扫描 | 编写循环 Shell 脚本 | `for` 循环 + 修改变量 |
| 数据分析 | 输出到文件 -> 外部工具读取 | 直接访问 LAMMPS 内部数据 |
| 工作流自动化 | 多个 Shell 脚本串联 | 一个 Python 函数搞定 |
| 可视化 | dump 文件 + OVITO | `matplotlib` 实时绘图 |
| 机器学习集成 | 复杂的文件 I/O | NumPy 数组直接交互 |
| 错误处理 | 手动检查日志 | `try/except` 异常捕获 |

#### 什么时候不需要 Python 接口？

Python 接口并不是万能的。以下情况用传统输入脚本更合适：

- **简单的单次模拟**：写一个输入脚本直接运行更简单
- **超大规模并行模拟**：Python 层有少量通信开销
- **只需要 LAMMPS 内部计算**：不需要把数据传到 Python 中

**经验法则**：如果你需要**修改参数**、**提取数据**或**与其他工具集成**，用 Python 接口；如果只是跑一个固定的模拟，输入脚本就够了。

---

### LAMMPS Python 接口

LAMMPS 提供了两种 Python 接口，适用于不同的使用场景。

#### 底层接口：`lammps` 模块

`lammps` 模块是 LAMMPS C++ 库的直接 Python 绑定。它的用法和输入脚本几乎一一对应：

```python
from lammps import lammps

# 创建 LAMMPS 实例
# cmdargs 可以传入命令行参数
lmp = lammps(cmdargs=["-log", "none", "-screen", "none"])

# 发送单条命令——就像在输入脚本中写一行
lmp.command("units lj")
lmp.command("dimension 3")
lmp.command("boundary p p p")

# 发送命令列表——批量执行，比逐条调用更高效
lmp.commands_list([
    "atom_style atomic",
    "lattice fcc 0.8442",
    "region box block 0 4 0 4 0 4",
    "create_box 1 box",
    "create_atoms 1 box",
])

# 从文件执行——等价于 LAMMPS 的 -in 命令行参数
lmp.file("in.melt")

# 从字符串执行
lmp.commands_string("""
    pair_style lj/cut 2.5
    pair_coeff 1 1 1.0 1.0 2.5
    mass 1 1.0
""")

# 运行模拟
lmp.command("run 1000")

# 关闭实例（释放内存）
lmp.close()
```

**底层接口的特点**：

- 命令语法与 LAMMPS 输入脚本完全一致
- 功能最全，所有 LAMMPS 命令都可以使用
- 性能最好（直接调用 C++ 库，无额外封装层）
- 适合生产级脚本

#### 高级接口：`PyLammps`

`PyLammps` 是底层接口的高级封装，提供了更 "Pythonic" 的语法：

```python
from lammps import PyLammps

# 创建实例
L = PyLammps()

# 命令名就是方法名，参数直接传入
L.units("lj")                    # 等价于 lmp.command("units lj")
L.atom_style("atomic")           # 等价于 lmp.command("atom_style atomic")
L.lattice("fcc", 0.8442)         # 等价于 lmp.command("lattice fcc 0.8442")
L.region("box", "block", 0, 4, 0, 4, 0, 4)

# 创建体系
L.create_box(1, "box")
L.create_atoms(1, "box")
L.pair_style("lj/cut", 2.5)
L.pair_coeff(1, 1, 1.0, 1.0, 2.5)
L.mass(1, 1.0)

# 获取体系信息（属性访问）
natoms = L.system.natoms
print(f"原子数：{natoms}")

# 运行
L.velocity("all", "create", 1.44, 87287, "loop", "geom")
L.fix(1, "all", "nvt", "temp", 1.44, 1.44, 0.5)
L.run(1000)

# 访问底层实例（可以随时回到底层接口）
底层实例 = L.lmp
version = 底层实例.version()

L.close()
```

**PyLammps 的特点**：

- 语法更简洁、更直观
- 内置信息查询（`L.system`、`L.computes`、`L.fixes`）
- 支持 Jupyter Notebook 交互式使用
- 性能略有开销（多了封装层）
- 适合教学、原型开发和交互式探索

#### 两种接口的选择

```
你的需求是什么？
    |
    +-- 快速探索 / 教学演示 / Jupyter Notebook
    |   +-- 使用 PyLammps
    |
    +-- 生产级脚本 / 性能敏感 / 需要最大灵活性
    |   +-- 使用底层 lammps 模块
    |
    +-- 不确定？
        +-- 从 PyLammps 开始，需要时通过 L.lmp 访问底层实例
```

---

### 数据提取方法

Python 接口最强大的功能之一是**直接从模拟中提取数据**——不需要先写入文件再读取。

#### `extract_compute`：提取 compute 的结果

LAMMPS 的 `compute` 用于计算各种物理量（温度、能量、RDF 等）。`extract_compute` 可以直接获取这些计算结果。

```python
# 语法：lmp.extract_compute(compute_id, style, type)
#
# style 参数：
#   0 = GLOBAL（全局量，如整个体系的温度）
#   1 = PER-ATOM（每原子量，如每个原子的势能）
#   2 = LOCAL（局部量，如每对原子的信息）
#
# type 参数：
#   0 = SCALAR（标量，一个数）
#   1 = VECTOR（向量，一组数）
#   2 = ARRAY（数组，二维表）

# 示例 1：获取全局温度（标量）
# "thermo_temp" 是 LAMMPS 内置的 compute
temp = lmp.extract_compute("thermo_temp", 0, 0)
print(f"温度 = {temp:.4f}")

# 示例 2：获取全局压强（标量）
press = lmp.extract_compute("thermo_press", 0, 0)
print(f"压强 = {press:.4f}")

# 示例 3：获取总势能（标量）
pe = lmp.extract_compute("thermo_pe", 0, 0)
print(f"总势能 = {pe:.4f}")

# 示例 4：获取 MSD 向量
# 需要先定义 compute：lmp.command("compute myMSD all msd")
msd = lmp.extract_compute("myMSD", 0, 1)  # style=0, type=1 (向量)
# msd[0] = MSD_x, msd[1] = MSD_y, msd[2] = MSD_z, msd[3] = MSD_total
```

**内置的 thermo compute 名称**：

| 名称 | 含义 |
|------|------|
| `thermo_temp` | 温度 |
| `thermo_press` | 压强 |
| `thermo_pe` | 势能 |
| `thermo_ke` | 动能 |

#### `extract_atom`：提取原子属性

`extract_atom` 返回指向 LAMMPS 内部数据的**指针**（ctypes 数组），可以直接访问，但需要小心处理。

```python
# 语法：lmp.extract_atom(name)
# 返回 ctypes 指针，指向 LAMMPS 内部的原子数据

# 提取原子坐标
# x 是一个 ctypes 二维数组：x[atom_id][xyz]
# 注意：atom_id 从 1 开始（不是 0！）
x = lmp.extract_atom("x")
# 访问第 1 个原子的 x 坐标：x[1][0]
# 访问第 1 个原子的 y 坐标：x[1][1]

# 提取原子速度
v = lmp.extract_atom("v")

# 提取原子受力
f = lmp.extract_atom("f")
```

**注意**：`extract_atom` 返回的是 C 指针，使用时需要了解底层数据布局。对于大多数情况，推荐使用下面的 `gather_atoms`。

#### `gather_atoms`：收集原子数据（推荐）

`gather_atoms` 是提取原子数据的**推荐方法**。它会把 LAMMPS 内部的数据**复制**为 Python 列表，更安全、更易用。

```python
import numpy as np

# 语法：lmp.gather_atoms(name, type, count)
#   name:  属性名（"x"=坐标, "v"=速度, "f"=力）
#   type:  数据类型（1=float, 2=int）
#   count: 每个原子的分量数（3=xyz, 1=标量）

# 获取所有原子的坐标
n = lmp.get_natoms()
x = lmp.gather_atoms("x", 1, 3)  # 返回长度为 n*3 的一维列表
# [x1, y1, z1, x2, y2, z2, x3, y3, z3, ...]

# 转为 numpy 数组并 reshape
coords = np.array(x).reshape(n, 3)  # shape: (n, 3)
# coords[i][0] = 第 i 个原子的 x 坐标

# 获取速度
v = lmp.gather_atoms("v", 1, 3)
vels = np.array(v).reshape(n, 3)

# 获取受力
f = lmp.gather_atoms("f", 1, 3)
forces = np.array(f).reshape(n, 3)
```

#### 三种方法的对比

| 方法 | 返回类型 | 优点 | 缺点 | 推荐场景 |
|------|---------|------|------|---------|
| `extract_compute` | float/array | 直接获取计算结果 | 需要知道 style/type 参数 | 获取温度、能量等全局量 |
| `extract_atom` | C 指针 | 零拷贝，性能最佳 | 需要处理 ctypes，索引从 1 开始 | 性能关键的场景 |
| `gather_atoms` | Python list | 安全、易用、可直接转 NumPy | 有数据复制开销 | **大多数场景的首选** |

---

### 数据后处理

模拟完成后，通常需要对输出数据进行各种分析。常见的后处理任务包括：

#### 日志文件解析

LAMMPS 日志文件（`log.lammps`）包含 `thermo` 输出的热力学数据。但日志文件的格式不是简单的 CSV——它可能包含多次 `run` 的输出、警告信息、错误信息等。解析时需要：

1. **找到列名行**：通常以 `Step` 开头
2. **匹配数据行**：由数字组成的行
3. **处理多次 run**：日志中可能有多个数据块，需要选择正确的那个

```python
import re

def parse_lammps_log(filename):
    """解析 LAMMPS 日志文件中的 thermo 数据"""
    with open(filename, 'r') as f:
        content = f.read()

    # 查找所有 thermo 数据块
    # thermo 输出的格式：列名行 + 多行数字数据
    blocks = re.findall(
        r'^(Step\s+.*\n'
        r'(?:\s*[\d.eE+\-]+\s+\S.*\n)+)',
        content,
        re.MULTILINE
    )

    if not blocks:
        return None

    # 取最后一个块（通常是生产运行）
    lines = blocks[-1].strip().split('\n')
    header = lines[0].split()

    data = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) == len(header):
            data.append([float(x) for x in parts])

    import numpy as np
    result = {}
    data_array = np.array(data)
    for i, name in enumerate(header):
        result[name] = data_array[:, i]

    return result
```

**正则表达式解释**：

- `Step\s+.*`：匹配以 "Step" 开头的行
- `[\d.eE+\-]+`：匹配数字（含科学记数法）
- `re.MULTILINE`：让 `^` 匹配每行开头

#### RDF 数据读取

LAMMPS 的 `compute rdf` + `fix ave/time` 输出的 RDF 文件格式：

```
# Time-averaged data for fix rdf_out
# TimeStep Number-of-rows
# Row c_myRDF[1] c_myRDF[2] c_myRDF[3] c_myRDF[4]
100 100
1 0.005 0.0 0.0 0.0
2 0.015 0.0 0.0 0.001
...
```

其中第 2 列是距离 r，第 3 列是 g(r)。

#### 轨迹文件处理

LAMMPS dump 文件（XYZ 格式）每帧包含：

- 第 1 行：原子数
- 第 2 行：注释行（通常包含时间步）
- 后面每行：类型 x y z

从轨迹可以计算：

- **MSD（均方位移）**：跟踪原子位移，提取扩散系数
- **VACF（速度自相关函数）**：描述速度记忆效应
- **原子轨迹可视化**：用 OVITO 或 Python 绘制

**MSD 的物理意义**：

- 短时间：弹道运动，MSD ~ t^2
- 长时间：扩散运动，MSD ~ t
- 扩散系数 D = MSD / (6t)（三维空间）

---

### matplotlib 绑图

Matplotlib 是 Python 中最常用的绑图库。在 LAMMPS 数据分析中，常用的图表类型包括：

#### 基本绑图流程

```python
import matplotlib.pyplot as plt

# 1. 创建图表
fig, ax = plt.subplots(figsize=(8, 5))

# 2. 绘制数据
ax.plot(x_data, y_data, color='#2c3e50', linewidth=1.5, label='Simulation')

# 3. 添加标注
ax.set_xlabel(r'Distance $r / \sigma$', fontsize=12)
ax.set_ylabel(r'$g(r)$', fontsize=12)
ax.set_title('Radial Distribution Function', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# 4. 保存图片
plt.tight_layout()
plt.savefig('rdf_plot.png', dpi=150, bbox_inches='tight')
plt.close()
```

#### 无头环境（服务器）

在没有图形界面的服务器上，需要使用非交互式后端：

```python
import matplotlib
matplotlib.use('Agg')  # 必须在 import plt 之前调用！
import matplotlib.pyplot as plt
```

#### 常用图表类型

| 图表类型 | 用途 | matplotlib 函数 |
|---------|------|----------------|
| 折线图 | 热力学量随时间变化 | `ax.plot()` |
| 散点图 | 原子位置分布 | `ax.scatter()` |
| 直方图 | 速度分布、能量分布 | `ax.hist()` |
| 填充图 | RDF 曲线（填充下方区域） | `ax.fill_between()` |
| 多子图 | 同时展示多个物理量 | `fig, axes = plt.subplots(nrows, ncols)` |

---

### 参数扫描

参数扫描是 Python 接口最实用的功能之一。基本模式：

```python
from lammps import lammps

# 定义要扫描的参数
temperatures = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
results = []

for T in temperatures:
    print(f"运行温度 T* = {T} ...")

    # 每次创建新的 LAMMPS 实例（确保干净状态）
    lmp = lammps(cmdargs=["-log", "none", "-screen", "none"])

    # 设置模拟（大部分参数相同）
    lmp.commands_list([
        "units lj",
        "atom_style atomic",
        "boundary p p p",
        "lattice fcc 0.8442",
        "region box block 0 4 0 4 0 4",
        "create_box 1 box",
        "create_atoms 1 box",
        "pair_style lj/cut 2.5",
        "pair_coeff 1 1 1.0 1.0 2.5",
        "mass 1 1.0",
    ])

    # 修改扫描参数
    lmp.command(f"velocity all create {T} 12345 loop geom")
    lmp.command(f"fix 1 all nvt temp {T} {T} 0.5")
    lmp.command("run 5000")

    # 提取结果
    final_T = lmp.extract_compute("thermo_temp", 0, 0)
    final_PE = lmp.extract_compute("thermo_pe", 0, 0)
    n = lmp.get_natoms()

    results.append({"T_target": T, "T_actual": final_T, "PE_per_atom": final_PE / n})
    lmp.close()

# 汇总结果
print(f"\n{'T_target':>10}  {'T_actual':>10}  {'PE/N':>10}")
for r in results:
    print(f"{r['T_target']:>10.2f}  {r['T_actual']:>10.4f}  {r['PE_per_atom']:>10.4f}")
```

**关键技巧**：

- 每次循环创建新实例，避免状态污染
- 使用 f-string 构建命令字符串
- 在循环中提取结果并存入列表
- 循环结束后统一处理和画图

---

## 脚本逐行解析

本项目包含三个 Python 脚本，下面逐一解析。

### `run_simulation.py` — Python 驱动的 LAMMPS 模拟

这是本项目的核心脚本，演示如何用 Python 完全控制一个 LJ 熔化模拟。

#### 第一部分：导入和错误处理

```python
try:
    from lammps import lammps
except ImportError as e:
    print("错误：无法导入 LAMMPS Python 模块")
    print("可能的原因和解决方案：...")
    exit(1)
```

**要点**：

- `try/except` 捕获导入错误，给出友好的提示
- 这比直接崩溃好得多——用户能立刻知道怎么解决
- 常见原因：LAMMPS 未安装 Python 绑定、路径未配置

#### 第二部分：创建 LAMMPS 实例

```python
lmp = lammps(cmdargs=["-log", "none", "-screen", "none"])
version = lmp.version()
```

**要点**：

- `cmdargs` 传递 LAMMPS 命令行参数
- `"-log none"` 不写日志文件（避免冲突）
- `"-screen none"` 不在屏幕打印输出（Python 自己处理输出）
- `version()` 返回 LAMMPS 版本字符串，用于确认实例正常

#### 第三部分：发送命令

```python
# 方法 1：逐条发送
lmp.command("units lj")
lmp.command("dimension 3")

# 方法 2：批量发送（更高效）
setup_cmds = [
    "neighbor 0.3 bin",
    "neigh_modify delay 0 every 1 check yes",
    "thermo 100",
    ...
]
lmp.commands_list(setup_cmds)
```

**要点**：

- `command()` 一次发一行，适合少量命令
- `commands_list()` 一次发一批，效率更高
- 命令语法与 LAMMPS 输入脚本完全一致

#### 第四部分：运行模拟

```python
# NVT 平衡
lmp.commands_list([
    "fix myNVT all nvt temp 1.44 1.44 0.5",
    "timestep 0.005",
    "run 5000",
])

# 切换到 NVE 生产运行
lmp.command("unfix myNVT")
lmp.commands_list([
    "fix myNVE all nve",
    "run 10000",
])
```

**要点**：

- 先用 NVT 平衡温度，再用 NVE 做生产运行
- `unfix` 移除旧的 fix，再设置新的
- `run` 命令会阻塞直到模拟完成

#### 第五部分：提取数据

```python
# 提取全局量
temp = lmp.extract_compute("thermo_temp", 0, 0)  # 标量
pe_total = lmp.extract_compute("thermo_pe", 0, 0)

# 提取原子坐标（推荐方法）
x = lmp.gather_atoms("x", 1, 3)  # 所有原子的 xyz
coords = np.array(x).reshape(natoms, 3)

# 提取原子速度
v = lmp.gather_atoms("v", 1, 3)
vels = np.array(v).reshape(natoms, 3)
```

**要点**：

- `extract_compute` 的三个参数：compute 名、style（0=全局）、type（0=标量）
- `gather_atoms` 返回扁平列表，需要 `reshape` 成 (natoms, 3)
- 转为 NumPy 数组后可以做各种数值计算

#### 第六部分：NumPy 数据分析

```python
# 计算质心速度
com_velocity = np.mean(vels, axis=0)

# 计算动能分布
ke_per_atom = 0.5 * np.sum(vels ** 2, axis=1)
mean_ke = np.mean(ke_per_atom)

# 计算距离矩阵
diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
dist_matrix = np.sqrt(np.sum(diff ** 2, axis=2))
```

**要点**：

- `np.mean(vels, axis=0)` 沿第一个轴（原子）求平均
- `np.sum(vels ** 2, axis=1)` 计算每个原子的速率平方
- 广播机制 `[:, np.newaxis, :]` 用于高效计算距离矩阵

#### 第七部分：参数扫描

```python
for rho in [0.6, 0.8, 1.0]:
    lmp.command("clear")  # 清除所有设置
    lmp.commands_list([
        "units lj",
        f"lattice fcc {rho}",  # 用 f-string 插入参数
        ...
        "run 2000",
    ])
    temp = lmp.extract_compute("thermo_temp", 0, 0)
    density_results.append({"rho": rho, "temp": temp})
```

**要点**：

- `clear` 命令清除所有模拟设置，从头开始
- f-string（`f"lattice fcc {rho}"`）用于动态插入参数值
- 每次迭代提取结果存入列表

#### 第八部分：清理

```python
lmp.close()  # 释放 LAMMPS 占用的内存
```

**要点**：

- 脚本结束前调用 `close()` 是好习惯
- 不调用也不会崩溃，但可能有内存泄漏
- 在 `for` 循环中，每次迭代结束都应该 `close()`

---

### `analyze.py` — 数据分析与可视化

这个脚本独立于 LAMMPS 模拟，专注于数据的读取、分析和绑图。

#### 日志解析函数 `parse_lammps_log()`

```python
def parse_lammps_log(filename):
    # 1. 读取整个文件内容
    with open(filename, 'r') as f:
        content = f.read()

    # 2. 用正则表达式查找 thermo 数据块
    # 模式：以 "Step" 开头的列名行 + 多行数字
    blocks = re.findall(
        r'^(Step\s+.*\n(?:\s*[\d.eE+\-]+\s+\S.*\n)+)',
        content, re.MULTILINE
    )

    # 3. 取最后一个数据块（生产运行）
    # 4. 解析列名和数据行
    # 5. 返回字典 {"Step": array, "Temp": array, ...}
```

#### RDF 数据读取 `read_rdf_data()`

```python
def read_rdf_data(filename):
    # 跳过注释行（以 # 开头）
    # 解析数据行：序号 距离 g(r) 配位数
    # 返回 (r_array, g_r_array, None)
```

#### MSD 计算 `calculate_msd_from_trajectory()`

```python
def calculate_msd_from_trajectory(filename):
    # 1. 读取 XYZ 轨迹文件的所有帧
    # 2. 以第一帧为参考位置
    # 3. 计算 MSD(t) = <|r(t) - r(0)|^2>
    # 4. 对后半段做线性拟合提取扩散系数
    #    D = slope / 6（三维空间）
```

#### 绘图函数

脚本包含多个绘图函数，每个负责一种图表：

1. **`plot_thermo_data()`**：温度、能量、压强随时间变化的子图
2. **`plot_rdf()`**：径向分布函数 g(r)，标注第一峰位置
3. **`plot_msd()`**：均方位移，标注线性拟合区域和扩散系数
4. **`plot_velocity_distribution()`**：速度直方图 + Maxwell-Boltzmann 理论曲线
5. **`plot_energy_conservation()`**：NVE 系综中的能量守恒检查

每个函数都遵循相同的模式：

```python
def plot_xxx(data, output_dir):
    if not HAS_MATPLOTLIB: return    # 检查 matplotlib
    if data is None: return           # 检查数据
    fig, ax = plt.subplots(...)       # 创建图表
    ax.plot(...)                       # 绘制数据
    ax.set_xlabel(...)                 # 添加标注
    plt.savefig(output_file)          # 保存图片
    plt.close()                        # 关闭图表释放内存
```

#### 示例数据生成

当真实的模拟数据不存在时（例如你还没有运行 `run_simulation.py`），脚本会自动生成示例数据来演示绘图功能。这保证了脚本**始终可以运行**，方便学习。

---

### `pylammps_demo.py` — PyLammps 高级接口

这个脚本演示 PyLammps 的各种功能。

#### 核心功能

| 函数 | 演示内容 |
|------|---------|
| `创建实例()` | 创建 PyLammps 实例，错误处理 |
| `演示基本命令()` | PyLammps vs 底层接口的语法对比 |
| `演示创建体系()` | 创建 FCC 晶体体系 |
| `演示运行模拟()` | NVT 平衡 + NVE 生产运行 |
| `演示信息查看()` | 使用 `L.system` 查看体系信息 |
| `演示计算查看()` | 遍历 `L.computes`、`L.fixes`、`L.variables` |
| `演示参数扫描()` | 不同密度下的参数扫描 |
| `演示互操作()` | 通过 `L.lmp` 访问底层实例 |

#### 运行方式

```bash
# 运行所有演示
python pylammps_demo.py

# 只运行参数扫描
python pylammps_demo.py scan
```

---

## 运行指南

### 前提条件

#### 1. 安装 LAMMPS

确保 LAMMPS 已安装并可用：

```bash
# 检查 lmp 命令
which lmp
lmp -h
```

#### 2. 安装 Python 绑定

```bash
# 方法 1：pip 安装（推荐）
pip install lammps

# 方法 2：从 LAMMPS 源码安装
cd /path/to/lammps/python
python install.py

# 验证安装
python -c "from lammps import lammps; print('OK')"
```

#### 3. 安装 Python 依赖

```bash
pip install numpy matplotlib
```

### 运行步骤

#### 步骤 1：运行模拟

```bash
cd /path/to/12-python-analysis/
python run_simulation.py
```

预期输出：

- 模拟进度和各步骤的运行信息
- 原子坐标、能量等数据的打印输出
- 参数扫描结果汇总表
- 生成 `dump.lammpstrj`（轨迹文件）和 `rdf.dat`（RDF 数据）

#### 步骤 2：分析数据

```bash
python analyze.py
```

预期输出：

- 日志解析结果
- RDF 数据读取
- MSD 计算
- 生成以下图片文件：
    - `thermo_plot.png`：热力学量变化图
    - `rdf_plot.png`：径向分布函数
    - `msd_plot.png`：均方位移
    - `velocity_dist.png`：速度分布
    - `energy_conservation.png`：能量守恒检查

#### 步骤 3：运行 PyLammps 演示

```bash
python pylammps_demo.py        # 运行所有演示
python pylammps_demo.py scan   # 只运行参数扫描
```

#### 步骤 4：查看结果

```bash
# 查看生成的图片
ls *.png

# 使用 OVITO 可视化轨迹文件（如果安装了 OVITO）
ovito dump.lammpstrj
```

### 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `ImportError: No module named lammps` | Python 绑定未安装 | `pip install lammps` |
| `lmp: command not found` | LAMMPS 未安装或不在 PATH | 检查安装或设置 PATH |
| `Segmentation fault` | LAMMPS 版本与 Python 版本不匹配 | 确保用同一 Python 编译 LAMMPS |
| 图片显示空白 | matplotlib 后端问题 | 确保使用 `Agg` 后端 |
| 数据文件不存在 | 未先运行 `run_simulation.py` | 先运行模拟脚本 |

---

## 练习题

### 练习 1：温度扫描（基础）

编写 Python 脚本，扫描 5 个不同温度（0.5, 1.0, 1.5, 2.0, 3.0）下的 LJ 液体。对每个温度：

1. 创建 4x4x4 的 FCC 体系
2. 用 NVT 平衡 3000 步
3. 记录实际温度和每原子势能
4. 绘制温度 vs 势能的曲线图

**提示**：参考 `run_simulation.py` 中的参数扫描部分。

### 练习 2：MSD 与扩散系数（进阶）

使用 Python 接口：

1. 运行一个 NVE 模拟（10000 步）
2. 每 100 步提取一次所有原子的坐标
3. 手动计算 MSD(t) = <|r(t) - r(0)|^2>
4. 绘制 MSD 曲线
5. 从曲线斜率提取扩散系数 D

**提示**：使用 `lmp.gather_atoms("x", 1, 3)` 提取坐标，注意周期性边界条件（需要展开坐标）。

### 练习 3：RDF 对比（进阶）

1. 运行模拟并使用 LAMMPS 内置的 `compute rdf` 计算 g(r)
2. 同时保存轨迹文件
3. 用 Python 从轨迹文件手动计算 g(r)
4. 将两种结果画在同一张图上对比

**提示**：手动计算 RDF 需要遍历所有原子对，对小体系可行。

### 练习 4：能量最小化自动化（综合）

编写一个 Python 函数 `minimize_crystal(lattice_type, size, potential)`：

- 参数：晶格类型（fcc/bcc/sc）、盒子大小、势函数参数
- 功能：创建体系 -> 能量最小化 -> 返回最终能量和原子位置
- 测试：对 fcc、bcc、sc 三种格子各运行一次，比较哪种最稳定

### 练习 5：完整工作流（挑战）

创建一个完整的 Python 工作流脚本：

1. 创建 FCC 铜晶体（使用 EAM 势）
2. 在中心引入一个空位缺陷
3. 进行能量最小化
4. 在 300K 下运行 NVT 平衡（10000 步）
5. 在 NVE 下运行生产模拟（50000 步）
6. 计算并绘制 RDF、MSD
7. 生成一份包含所有图表的报告

**提示**：将每个步骤封装为函数，用一个 `main()` 函数串联。

---

## 参考资料

### 官方文档

- [LAMMPS Python 接口文档](https://docs.lammps.org/Python_head.html)：底层 `lammps` 模块的完整 API 参考
- [PyLammps 文档](https://docs.lammps.org/PyLammps.html)：高级 PyLammps 接口的使用指南
- [LAMMPS Python 示例](https://github.com/lammps/lammps/tree/master/python/examples)：官方提供的 Python 示例代码

### Python 库文档

- [NumPy 文档](https://numpy.org/doc/)：数组操作、线性代数、随机数等
- [Matplotlib 文档](https://matplotlib.org/)：绑图库的完整参考
- [Python 正则表达式](https://docs.python.org/3/library/re.html)：日志文件解析需要用到

### 相关项目

- 项目 09（扩散与输运性质）：本项目的 MSD/RDF 分析方法的理论背景
- 项目 07（金属 EAM 势）：练习 5 中 EAM 势的使用方法
- 项目 08（晶体缺陷）：练习 4 和 5 中引入缺陷的方法

### 扩展阅读

- [MDAnalysis](https://www.mdanalysis.org/)：专业的 MD 轨迹分析 Python 库
- [OVITO](https://www.ovito.org/)：MD 轨迹可视化工具（也支持 Python 脚本）
- [pymatgen](https://pymatgen.org/)：材料科学 Python 库，可与 LAMMPS 配合使用
