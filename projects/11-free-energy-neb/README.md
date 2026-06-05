# 项目 11：自由能计算与 NEB（Nudged Elastic Band）

---

## 学习目标

完成本项目后，你将能够：

1. **理解势能面的概念**：知道什么是势能面（Potential Energy Surface, PES）、反应坐标、
   过渡态（Transition State）和鞍点（Saddle Point），并能用图示解释这些概念。

2. **掌握 NEB 方法的原理**：理解"微调弹性带"（Nudged Elastic Band）方法的物理思想，
   包括弹簧力的作用、力的分解（nudge 操作）、以及为什么 NEB 能找到最小能量路径。

3. **使用 LAMMPS 执行 NEB 计算**：能够独立编写和运行 NEB 输入脚本，
   包括准备初始态和末态、设置 `fix neb` 命令、调整弹簧常数和收敛参数。

4. **分析 NEB 计算结果**：能够从输出中读取激活能、过渡态能量，
   绘制反应路径的能量剖面图，并判断计算是否收敛。

5. **了解其他自由能计算方法**：对元动力学（Metadynamics）、伞形采样（Umbrella Sampling）
   和牵引分子动力学（Steered MD）有基本认识，知道各自适用场景。

---

## 背景知识

### 势能面与反应路径

在分子模拟中，系统的势能是所有原子坐标的函数：

```
E = E(r₁, r₂, r₃, ..., rₙ)
```

其中 `rᵢ` 是第 `i` 个原子的位置向量。这个多维函数构成的"面"称为**势能面**
（Potential Energy Surface, PES）。

势能面上的特殊点：

```
能量 E
  ^
  |          TS（过渡态 / 鞍点）
  |         /  \
  |        /    \          ← 激活能 Ea
  |       /      \
  |  初始态      末态
  |  (R)         (P)
  |___|__________|__________> 反应坐标
      反应路径（MEP）
```

- **极小点（Minimum）**：所有方向上能量都上升的点。对应稳定的分子构型。
  - 局部极小（Local Minimum）：在一定范围内能量最低
  - 全局极小（Global Minimum）：在整个势能面上能量最低

- **鞍点（Saddle Point）**：在某些方向上能量上升，另一些方向上能量下降。
  - 一阶鞍点：只有一个方向是下坡的（对应一个虚频振动模式）
  - 过渡态就是反应路径上的一阶鞍点

- **最小能量路径（Minimum Energy Path, MEP）**：
  连接两个极小点的路径中，路径上每一点都是该截面上能量最低的点。
  物理上，这是最可能发生的反应路径。

- **激活能（Activation Energy, Eₐ）**：
  过渡态能量与初始态能量之差，即 `Eₐ = E(TS) - E(R)`。
  激活能越大，反应越难发生（速率越慢）。

在分子动力学中，我们常常需要回答以下问题：

> "系统从构型 A 变化到构型 B，中间经历了什么过程？能垒有多高？"

这就是 NEB 方法要解决的核心问题。

### 过渡态理论

过渡态理论（Transition State Theory, TST）是化学动力学的基石之一。
它的核心思想是：反应物在越过势能面上的鞍点（过渡态）后，就会变成产物。

**Arrhenius 方程**：

```
k = A · exp(-Eₐ / k_B T)
```

其中：
- `k` — 反应速率常数（单位：s⁻¹）
- `A` — 前因子（频率因子），与碰撞频率和熵变有关
- `Eₐ` — 激活能（单位：J 或 eV）
- `k_B` — 玻尔兹曼常数（1.380649 × 10⁻²³ J/K）
- `T` — 绝对温度（单位：K）

Arrhenius 方程告诉我们：

1. **激活能越大，反应越慢**：因为指数项 `exp(-Eₐ/k_BT)` 随 `Eₐ` 增大而急剧减小。
   例如在室温（300 K）下，`Eₐ` 增加 0.1 eV（约 9.6 kJ/mol），反应速率降低约 50 倍。

2. **温度越高，反应越快**：高温提供更多热能，帮助系统越过能垒。

3. **找到过渡态就能预测反应速率**：一旦通过 NEB 等方法获得 `Eₐ`，
   代入 Arrhenius 方程即可估算反应速率。

**为什么寻找过渡态如此重要？**

在材料科学中，许多关键过程都涉及原子跨越能垒的过程：

| 过程           | 描述                           | 典型激活能      |
|:-------------|:-----------------------------|:-----------|
| 空位扩散         | 原子跳入相邻空位                   | 0.5 ~ 2 eV |
| 位错攀移         | 刃型位错通过空位吸收/发射而垂直滑移面运动    | 1 ~ 3 eV   |
| 表面吸附/脱附     | 分子在催化剂表面结合或离开              | 0.2 ~ 2 eV |
| 相变           | 晶体结构从一种排列变为另一种             | 0.1 ~ 1 eV |
| 化学反应         | 化学键断裂和形成                    | 0.5 ~ 5 eV |

### NEB 方法详解

#### 基本思想

NEB 方法的目标是找到连接两个已知构型（初始态和末态）的**最小能量路径**（MEP）。

基本思路：

1. 在初始态和末态之间插入若干"映像"（images / replicas）
2. 用虚拟弹簧将相邻映像连接起来
3. 同时优化所有映像的位置，使整个路径收敛到 MEP

```
初始态                                          末态
  ○────弹簧────○────弹簧────○────弹簧────○────弹簧────○
 Image 0      Image 1      Image 2      Image 3      Image 4
 （固定）      （优化）      （优化）      （优化）      （固定）
```

映像（image）就是路径上的一个"快照"——一个完整的原子构型。
初始态和末态的映像在优化过程中保持不动（固定），
只有中间的映像会被优化，直到整条路径收敛到最小能量路径。

#### 为什么需要"微调"（Nudge）？

如果不做任何特殊处理，直接用弹簧把映像连起来并优化（即"弹性带方法"，
Elastic Band），会出现两个严重问题：

**问题 1：映像滑落（Sliding）**

映像倾向于滑向相邻的极小点，导致路径偏离真正的 MEP。
特别是靠近极小点的映像会被"拉"到极小点里面。

**问题 2：映像聚集（Corner Cutting）**

在高曲率区域（如过渡态附近），映像倾向于聚集在一起，
导致路径在弯曲处不够精确。

**Nudge 操作的解决方案：**

将每个映像上的力分解为两个分量，分别处理：

```
总力 F = F_真实 + F_弹簧

           ↓ 分解为两个方向

切线方向（沿路径）：
  F_切线 = F_弹簧_∥    ← 只保留弹簧力的切线分量（防止映像聚集）

法线方向（垂直路径）：
  F_法线 = F_真实_⊥    ← 只保留真实力的法线分量（推向 MEP）
```

用图示说明：

```
                    F_真实
                   ↗
                  /
       ○─────────○─────────○   ← 三个相邻映像
                  |
                  | F_弹簧
                  ↓
                  
NEB 修正后的力：
  弹簧力沿切线方向的分量  → 保持映像均匀分布
  真实力垂直切线方向的分量  → 推映像向 MEP 移动
```

- **弹簧力只保留切线分量**：确保映像沿路径均匀分布，不会聚集。
- **真实力只保留法线分量**：确保映像被推向 MEP，不会沿路径滑落。

数学表达：

```
设 τ̂ 为路径切线方向的单位向量

真实力的法线分量（垂直于路径）：
  F_⊥ = F_真实 - (F_真实 · τ̂) · τ̂

弹簧力的切线分量（沿路径）：
  F_弹簧_∥ = [k(|R_{i+1} - R_i|) - k(|R_i - R_{i-1}|)] · τ̂

NEB 修正后的总力：
  F_NEB = F_⊥ + F_弹簧_∥
```

#### Climbing Image NEB（CI-NEB）

标准 NEB 的改进版本。在标准 NEB 中，过渡态附近的映像精度受限于映像间距。
CI-NEB 解决这个问题：

1. 先执行标准 NEB 计算，初步定位过渡态区域
2. 找到能量最高的映像
3. 让该映像"爬"向真正的鞍点——修改该映像的力为：

```
F_CI = F_真实 - 2·(F_真实 · τ̂)·τ̂
```

其中 `τ̂` 是路径切线方向的单位向量。

4. 该映像沿真实力的上坡方向移动，最终精确停在鞍点上

**优势**：CI-NEB 可以获得与精确二阶鞍点搜索方法相同的精度，
但计算量更小。CI-NEB 映像不受弹簧力影响，可以自由爬到最高点。

#### 弹簧常数的选择

弹簧常数 `k` 的选择影响 NEB 计算的效率和精度：

| `k` 值      | 效果                         | 适用情况        |
|:-----------|:---------------------------|:------------|
| 太小 (< 0.1) | 映像可能聚集在极小点附近，路径不均匀      | 不推荐         |
| 适中 (1~10)  | 映像分布均匀，计算稳定              | 大多数情况       |
| 太大 (> 100) | 映像间距过于刚性，可能阻止映像到达过渡态附近 | 需要谨慎        |

经验法则：`k` 应该与势函数的力常数在同一量级。
对于 LJ 势，`k = 1.0` 通常是一个合理的起点。

### 实现细节

#### LAMMPS 中的 NEB 实现

LAMMPS 通过 `fix neb` 命令实现 NEB 方法。核心命令如下：

```lammps
# 定义 NEB fix，弹簧常数为 1.0
fix             neb_fix all neb 1.0

# 执行 NEB 最小化
minimize        0.0 1.0e-6 1000 10000
```

#### MPI 并行机制

NEB 计算使用 MPI（Message Passing Interface）实现并行：

```
mpirun -np N lmp -in in.neb
```

其中 `N` 是映像（replica）数量。

工作原理：

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  MPI 进程 0  │  │  MPI 进程 1  │  │  MPI 进程 2  │  │  MPI 进程 3  │
│             │  │             │  │             │  │             │
│  Image 0    │  │  Image 1    │  │  Image 2    │  │  Image 3    │
│  (初始态)    │  │  (插值)     │  │  (插值)     │  │  (末态)     │
│             │  │             │  │             │  │             │
│ 计算力和能量  │  │ 计算力和能量  │  │ 计算力和能量  │  │ 计算力和能量  │
│     ↓       │  │     ↓       │  │     ↓       │  │     ↓       │
│ NEB 力修正   │  │ NEB 力修正   │  │ NEB 力修正   │  │ NEB 力修正   │
│     ↓       │  │     ↓       │  │     ↓       │  │     ↓       │
│ 移动原子     │  │ 移动原子     │  │ 移动原子     │  │ 移动原子     │
│     ↓       │  │     ↓       │  │     ↓       │  │     ↓       │
│ 与邻居交换   │←→│ 与邻居交换   │←→│ 与邻居交换   │←→│ 与邻居交换   │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
     固定              优化              优化              固定
```

- 每个 MPI 进程独立计算一个映像的势能和原子力
- 相邻进程通过 MPI 通信交换信息（用于计算弹簧力和切线方向）
- 进程 0（初始态）和进程 N-1（末态）的原子坐标固定不动
- 中间的进程进行受限优化

**注意事项**：

1. 映像数 `N` 通常取 4 ~ 16，取决于反应路径的复杂程度
2. 映像太少 → 路径分辨率低，可能错过过渡态
3. 映像太多 → 计算量增大，且映像间通信开销增加
4. 每个映像中的原子数必须相同（初始态和末态原子数必须一致）

#### 收敛判据

NEB 计算的收敛标准通常基于**力的范数**而不是能量变化：
因为 MEP 上各映像的能量可以有很大差异，能量变化不适合作为收敛判据。

```
收敛条件：所有映像上的最大原子力 < F_tol
```

常用值：`F_tol = 1.0e-4 ~ 1.0e-6`（取决于精度需求）

### 其他自由能计算方法

NEB 是计算激活能和寻找反应路径的强有力工具，但它有一些限制：
- 只适用于零温（T = 0 K）的势能面
- 需要事先知道初始态和末态
- 对于高维系统，路径的初始猜测可能很差

以下是一些互补的自由能计算方法：

#### 元动力学（Metadynamics）

**基本思想**：在分子动力学模拟过程中，周期性地向势能面上"堆积"高斯势，
迫使系统逃离已经访问过的区域，最终覆盖整个自由能面。

```
自由能面：                    堆积高斯势后：
    E ↑                          E ↑
      |     /\                     |     /\
      |    /  \                    |    /  \
      |   /    \                   |   / ▲▲ \    ← 高斯势将势阱填平
      |  /      \                  |  / ▲▲▲▲ \
      | /        \                 | / ▲▲▲▲▲▲ \
      |/__________\                |/▲▲▲▲▲▲▲▲▲\___________
      A     反应坐标  B             A     反应坐标  B
```

- 优点：不需要预先知道末态，可以同时探索多个反应路径
- 缺点：需要选择合适的集体变量（Collective Variable），计算量大
- 适用：复杂系统的自由能面探索、相变研究

#### 伞形采样（Umbrella Sampling）

**基本思想**：在反应坐标的不同位置施加偏置势（通常是谐振子势），
强制系统停留在特定区域，然后通过加权直方图分析方法（WHAM）
去除偏置势的影响，重建自由能面。

```
        偏置势 U(ξ)
         ↑
         |    1     2     3     4     5
         |   /|\   /|\   /|\   /|\   /|\
         |  / | \ / | \ / | \ / | \ / | \
         | /  |  X  |  X  |  X  |  X  |  \
         |/   | / \ | / \ | / \ | / \ |   \
         +----+-----+-----+-----+-----+----→ 反应坐标 ξ
         ξ₁   ξ₂   ξ₃    ξ₄   ξ₅   ξ₆
```

- 每个窗口用一个谐振子势将系统"钉"在反应坐标的不同位置
- 收集每个窗口的采样数据
- 用 WHAM 或 MBAR 方法将所有窗口拼接起来，得到完整的自由能曲线

- 优点：精度高，方法成熟
- 缺点：需要手动选择窗口和偏置势强度，窗口数可能很多
- 适用：精确的自由能计算、溶剂化自由能

#### 牵引分子动力学（Steered MD, SMD）

**基本思想**：在原子或分子上施加一个外部力（或固定速度的"弹簧"），
将系统从一个构型强制拉到另一个构型。

```
                弹簧
固定端 ──────/\/\/\/─────○ 被牵引的原子
                              → 拉力方向
                              → 以恒定速度移动
```

- 类似于实验中的原子力显微镜（AFM）操作
- 可以测量力-距离曲线
- 通过 Jarzynski 等式或 Crooks 关系可以从非平衡功计算平衡自由能差

- 优点：直观，与实验操作类似
- 缺点：是非平衡过程，需要特殊的后处理方法才能得到平衡自由能
- 适用：分子解离、蛋白质折叠的力学性质

#### 方法比较

| 方法          | 需要已知末态？ | 零温/有限温度 | 主要输出       | 计算量  |
|:------------|:---------|:--------|:-----------|:-----|
| NEB         | 是        | 零温     | MEP 和激活能   | 中    |
| 元动力学       | 否        | 有限温度  | 自由能面       | 高    |
| 伞形采样       | 是（反应坐标）| 有限温度  | 自由能曲线      | 高    |
| 牵引 MD      | 是        | 有限温度  | 力-距离曲线     | 中    |
| 动力学积分      | 是（热力学路径）| 有限温度 | 自由能差       | 高    |

---

## 输入脚本逐行解析

### in.neb_setup — 初始态和末态准备

这个脚本执行以下步骤来准备 NEB 计算所需的两个端点构型。

**第一步：基本设置**

```lammps
units           lj
atom_style      atomic
pair_style      lj/cut 2.5
boundary        p p p
```

- `units lj`：使用 Lennard-Jones 无量纲单位（长度=σ，能量=ε，质量=m）
- `atom_style atomic`：每个原子只有位置和类型等基本属性，无电荷、无键连
- `pair_style lj/cut 2.5`：使用 LJ 势，截断半径为 2.5σ
- `boundary p p p`：三维周期性边界条件

**第二步：创建 FCC 晶体**

```lammps
lattice         fcc 1.0
region          box block 0 4 0 4 0 4
create_box      1 box
create_atoms    1 box
```

- `lattice fcc 1.0`：定义 FCC（面心立方）晶格，晶格常数为 1.0
- `region box block 0 4 0 4 0 4`：定义模拟盒子范围（4×4×4 个晶胞）
- `create_box`：在区域内创建模拟盒子
- `create_atoms`：在盒子中按晶格排列创建原子（共 4×4×4×4 = 256 个原子）

**第三步：势能参数和初始弛豫**

```lammps
pair_coeff      1 1 1.0 1.0 2.5
mass            1 1.0
min_style       cg
minimize        1.0e-6 10000 10000 1.0e-8
```

- `pair_coeff`：LJ 势参数，ε=1.0，σ=1.0，截断=2.5
- `mass`：原子质量设为 1.0（LJ 无量纲单位下）
- `min_style cg`：共轭梯度法（Conjugate Gradient），适合寻找局部极小值
- `minimize`：能量最小化，力收敛阈值 10⁻⁶，最大 10000 步

**第四步：创建空位（初始态）**

```lammps
region          vac_sphere sphere 0.5 0.5 0.5 0.1 units box
delete_atoms    region vac_sphere
```

- 在 (0.5, 0.5, 0.5) 位置（FCC 晶胞的体心位置）创建一个半径为 0.1 的小球区域
- 删除该区域内的原子，形成单空位
- 这就是 NEB 计算的**初始态**（State 1）
- 删除后再次最小化，让空位周围的原子弛豫到新的平衡位置

**第五步：空位跳跃 — 构建末态**

```lammps
region          neighbor_atom sphere 1.0 1.0 0.5 0.1 units box
group           mobile_atom region neighbor_atom
displace_atoms  mobile_atom move -0.5 -0.5 0.0 units box
```

- 选取 (1.0, 1.0, 0.5) 附近的原子——这是空位的最近邻之一
- 将该原子沿 (-0.5, -0.5, 0.0) 方向移动，到达空位位置 (0.5, 0.5, 0.5)
- 这等效于空位从 (0.5, 0.5, 0.5) 跳到 (1.0, 1.0, 0.5)
- 这就是 NEB 计算的**末态**（State 2）

**第六步：弛豫末态并输出数据文件**

```lammps
minimize        1.0e-6 10000 10000 1.0e-8
write_data      data.initial
write_data      data.final
```

- 对末态构型进行能量最小化
- `write_data` 将原子坐标、盒子信息、势能参数写入数据文件

**输出文件说明**：

| 文件                 | 内容                   | 用途             |
|:-------------------|:---------------------|:---------------|
| `data.initial`     | 初始态的原子坐标和盒子信息      | NEB 的第一个映像     |
| `data.final`       | 末态的原子坐标和盒子信息       | NEB 的最后一个映像    |
| `dump.initial.*`   | 初始态的轨迹文件            | 可视化检查          |
| `dump.final.*`     | 末态的轨迹文件             | 可视化检查          |

### in.neb — NEB 计算主脚本

**第一步：基本设置（与 neb_setup 保持一致）**

```lammps
units           lj
atom_style      atomic
pair_style      lj/cut 2.5
boundary        p p p
read_data       data.initial
pair_coeff      1 1 1.0 1.0 2.5
mass            1 1.0
```

- 必须与 `in.neb_setup` 中的设置完全一致（单位、势函数、质量等）
- `read_data data.initial`：第一个 MPI 进程读取初始态数据

**第二步：NEB 关键字设置**

```lammps
neb_keywords    final data.final
```

- 告诉 LAMMPS：末态数据文件为 `data.final`
- LAMMPS 会自动处理：
  - 第一个 replica 使用 `data.initial` 的坐标
  - 最后一个 replica 使用 `data.final` 的坐标
  - 中间 replica 使用线性插值的坐标

**第三步：定义 NEB fix**

```lammps
fix             neb_fix all neb 1.0
```

- `neb_fix`：fix 的 ID（名称），可以任意取
- `all`：作用于所有原子
- `neb`：使用 NEB 方法
- `1.0`：弹簧常数 k = 1.0（LJ 单位）

弹簧常数的物理意义：
- 连接相邻映像的虚拟弹簧的弹性系数
- k 越大 → 弹簧越硬 → 映像间距离更均匀
- k 越小 → 弹簧越软 → 映像可能聚集在能量低的区域
- 通常取 1.0 ~ 10.0，需要根据具体问题调整

**第四步：执行 NEB 最小化**

```lammps
min_style       cg
minimize        0.0 1.0e-6 1000 10000
```

- `min_style cg`：共轭梯度法，适合受限优化问题
- `minimize` 参数：
  - `0.0`：能量变化阈值（设为 0 表示不使用能量收敛判据）
  - `1.0e-6`：力的收敛阈值（所有映像的最大原子力 < 10⁻⁶ 时收敛）
  - `1000`：最大迭代步数
  - `10000`：最大函数评估次数

**运行命令**：

```bash
mpirun -np 4 lmp -in in.neb
```

- `-np 4`：使用 4 个 MPI 进程（即 4 个映像）
- 每个进程独立计算一个映像的势能和力
- 相邻进程通过 MPI 通信交换信息

---

## 运行指南

### 前置条件

确保已安装：
- LAMMPS（命令为 `lmp`）
- MPI 实现（如 OpenMPI 或 MPICH）

### 步骤 1：准备初始态和末态

```bash
cd /home/faust/vibe/lmp_learn/projects/11-free-energy-neb/
lmp -in in.neb_setup
```

运行后会生成：
- `data.initial` — 初始态数据文件
- `data.final` — 末态数据文件
- `dump.initial.lammpstrj` / `dump.final.lammpstrj` — 可视化文件

**检查输出**：查看终端中的能量值，确认空位态和末态的能量合理。

### 步骤 2：运行 NEB 计算

```bash
mpirun -np 4 lmp -in in.neb
```

**输出解读**：

NEB 计算过程中，LAMMPS 会输出每个映像的势能。关键信息包括：

```
Step   PotEng        ...
...
100    -1.23456 ...   ← 每个映像的势能
```

- 找到能量最高的映像 → 该映像对应过渡态
- 激活能 = 最高映像能量 − 初始态能量
- 如果所有映像的能量变化很小且路径光滑 → 计算已收敛

### 步骤 3：分析结果

使用 Python 绘制能量剖面图：

```python
import matplotlib.pyplot as plt

# 从 NEB 输出中提取各映像的势能
# 这里用示例数据，实际应从 LAMMPS 输出中提取
images = [0, 1, 2, 3]        # 映像编号
energies = [-1.35, -1.20, -1.15, -1.30]  # 各映像的势能（示例）

plt.figure(figsize=(8, 5))
plt.plot(images, energies, 'bo-', linewidth=2, markersize=8)
plt.xlabel('映像编号 (Image Index)', fontsize=12)
plt.ylabel('势能 (Potential Energy, epsilon)', fontsize=12)
plt.title('NEB 能量剖面图', fontsize=14)
plt.grid(True, alpha=0.3)
plt.savefig('neb_energy_profile.png', dpi=150, bbox_inches='tight')
plt.show()

# 计算激活能
E_initial = energies[0]
E_TS = max(energies)
Ea = E_TS - E_initial
print(f"激活能 Ea = {Ea:.4f} epsilon")
```

### 步骤 4：可视化

使用 OVITO 或 VMD 打开轨迹文件：

```bash
# OVITO（推荐）
ovito dump.neb.*.lammpstrj

# VMD
vmd dump.neb.0.lammpstrj dump.neb.1.lammpstrj \
    dump.neb.2.lammpstrj dump.neb.3.lammpstrj
```

在可视化软件中，你可以：
- 观察每个映像中原子的排列
- 查看空位扩散的路径
- 确认末态构型与预期一致

---

## 常见问题与调试

### Q1: NEB 计算不收敛怎么办？

可能原因和解决方案：

| 问题            | 原因                 | 解决方案                        |
|:-------------|:------------------|:----------------------------|
| 力不收敛         | 最大步数不够             | 增加 minimize 的最大步数           |
| 映像聚集         | 弹簧常数太小             | 增大 k 值（如改为 5.0 或 10.0）    |
| 映像偏离 MEP     | 弹簧常数太大             | 减小 k 值                      |
| 能量震荡         | 初始插值质量差            | 检查初始态和末态，确保构型合理           |
| 进程崩溃         | 原子重叠               | 确保初始态和末态已经过充分弛豫           |

### Q2: 如何选择映像数量？

- 路径简单（如简单的原子跳跃）：4 ~ 8 个映像足够
- 路径复杂（如涉及多个原子的重排）：8 ~ 16 个映像
- 经验法则：每个映像之间的"距离"不应超过 0.5σ（LJ 单位）

### Q3: 如何判断结果是否正确？

1. **能量剖面应光滑**：如果出现不连续或剧烈震荡，说明计算未收敛或路径有问题
2. **初始态和末态能量应相近**：空位扩散的初始态和末态是对称过程，能量差应很小
3. **过渡态位置合理**：在过渡态处，原子应位于初始格点和空位之间的"中间"位置
4. **激活能应在合理范围内**：对于 LJ 晶体的空位扩散，Eₐ 通常在 0.5 ~ 1.5ε 范围内

### Q4: `neb_keywords` 和 `fix neb` 有什么区别？

- `neb_keywords final data.final`：告诉 LAMMPS 如何生成各映像的初始构型
  （从哪个文件读末态，如何做插值）
- `fix neb`：实际的 NEB 物理引擎，负责计算弹簧力和力的 nudge 操作
- 两者缺一不可：`neb_keywords` 提供构型，`fix neb` 执行计算

### Q5: 为什么初始态和末态的原子数必须相同？

因为 NEB 计算通过线性插值在初始态和末态之间生成中间映像。
如果原子数不同，就无法建立一一对应关系，插值也就无法进行。

---

## 练习题

### 练习 1：改变映像数量

将 `mpirun -np 4` 改为 `mpirun -np 8`，使用 8 个映像重新运行 NEB 计算。

**问题**：
- 激活能是否变化？变化了多少？
- 能量剖面是否更光滑？
- 计算时间如何变化？（用 `time` 命令测量）

```bash
time mpirun -np 8 lmp -in in.neb
```

### 练习 2：调整弹簧常数

修改 `fix neb` 命令中的弹簧常数，分别使用 k = 0.1、1.0、10.0 运行计算。

```lammps
# 在 in.neb 中修改这一行：
fix             neb_fix all neb 0.1    # 先试 0.1
# 然后改为 10.0
fix             neb_fix all neb 10.0
```

**问题**：
- 弹簧常数对映像分布有何影响？
- 哪个值给出最均匀的映像间距？
- 弹簧常数对激活能有影响吗？（理论上不应该有，但实际可能有数值误差）

### 练习 3：不同方向的空位跳跃

修改 `in.neb_setup`，使末态的空位沿 [100] 方向跳跃（而非原始的 [110] 方向）。

**提示**：
- 原始方向 [110]：从 (1.0, 1.0, 0.5) 移到 (0.5, 0.5, 0.5)
- 新方向 [100]：从 (1.0, 0.5, 0.5) 移到 (0.5, 0.5, 0.5)
  即只在 x 方向移动 0.5，不移动 y 方向

需要修改的代码：

```lammps
# 原始（[110] 方向）：
region          neighbor_atom sphere 1.0 1.0 0.5 0.1 units box
group           mobile_atom region neighbor_atom
displace_atoms  mobile_atom move -0.5 -0.5 0.0 units box

# 修改为（[100] 方向）：
region          neighbor_atom sphere 1.0 0.5 0.5 0.1 units box
group           mobile_atom region neighbor_atom
displace_atoms  mobile_atom move -0.5 0.0 0.0 units box
```

**问题**：
- [100] 方向和 [110] 方向的激活能是否相同？
- 从晶体学角度解释为什么不同（提示：FCC 中不同方向的跳跃距离不同）

### 练习 4：绘制完整的能量剖面图

编写 Python 脚本，从 LAMMPS 的 NEB 输出中提取每个映像的势能，
绘制能量剖面图并计算激活能。

**要求**：
- 自动从 log 文件（log.lammps）中解析数据
- 绘制能量 vs. 映像编号的曲线
- 标注过渡态位置和激活能值
- 计算反应路径的总长度（通过原子坐标）

```python
import matplotlib.pyplot as plt
import numpy as np

# 提示：LAMMPS 日志文件格式
# 用正则表达式匹配 thermo 输出行
# 提取 Step 和 PotEng 列

# 1. 解析 LAMMPS 日志文件
# 2. 提取每个映像的势能
# 3. 绘图并标注
# 4. 计算激活能
```

### 练习 5：双空位扩散

修改 `in.neb_setup`，创建两个相邻空位（双空位），
然后进行 NEB 计算研究双空位的扩散过程。

**步骤**：
1. 在 FCC 晶体中删除两个相邻原子（形成双空位）
2. 构建末态：两个原子分别跳入两个空位
3. 运行 NEB 计算
4. 比较单空位和双空位的激活能

**问题**：
- 双空位的激活能是单空位的两倍吗？为什么？
- 双空位扩散的 MEP 形状与单空位有何不同？
- 在实际材料中，双空位扩散对扩散系数有何影响？

---

## 参考资料

### 核心文献

1. **NEB 方法原始论文**：
   Mills, G., Jonsson, H., & Schenter, G. K. (1995).
   "Revised implementation of the nudged elastic band method for finding minimum
   energy paths and saddle points."
   *Surface Science*, 324(2-3), 305-337.

2. **CI-NEB 方法**：
   Henkelman, G., Uberuaga, B. P., & Jonsson, H. (2000).
   "A climbing image nudged elastic band method for finding saddle points and
   minimum energy paths."
   *The Journal of Chemical Physics*, 113(22), 9901-9904.

3. **NEB 方法综述**：
   Jonsson, H., Mills, G., & Jacobsen, K. W. (1998).
   "Nudged elastic band method for finding minimum energy paths of transitions."
   In *Classical and quantum dynamics in condensed phase simulations*
   (pp. 385-404).

### LAMMPS 文档

- `fix neb` 命令文档：https://docs.lammps.org/fix_neb.html
- `minimize` 命令文档：https://docs.lammps.org/minimize.html
- NEB 示例：https://docs.lammps.org/Howto_neb.html

### 其他自由能方法

4. **元动力学**：
   Laio, A., & Parrinello, M. (2002).
   "Escaping free-energy minima."
   *Proceedings of the National Academy of Sciences*, 99(20), 12562-12566.

5. **伞形采样**：
   Kumar, S., et al. (1992).
   "The weighted histogram analysis method for free-energy calculations on
   biomolecules."
   *Journal of Computational Chemistry*, 13(8), 1011-1021.

6. **牵引分子动力学**：
   Park, S., et al. (2003).
   "Free energy calculation from steered molecular dynamics simulations using
   Jarzynski's equality."
   *The Journal of Chemical Physics*, 119(6), 3559-3566.

### 在线资源

- LAMMPS 官方教程：https://docs.lammps.org/Manual.html
- LAMMPS NEB 教程：https://docs.lammps.org/Howto_neb.html
- OVITO 可视化软件：https://www.ovito.org/
- VMD 可视化软件：https://www.ks.uiuc.edu/Research/vmd/

---

## 延伸阅读

### NEB 在材料科学中的应用

1. **氢在金属中的扩散**：
   研究氢原子在铁、镍等金属晶格中的跳跃路径和激活能，
   对理解氢脆现象至关重要。

2. **位错运动**：
   刃型位错和螺型位错的滑移和攀移过程，
   通过 NEB 计算获得不同滑移系的激活能。

3. **表面吸附和催化**：
   分子在催化剂表面的吸附、解离和重组过程，
   每一步都需要找到过渡态和激活能。

4. **相变形核**：
   从一种晶体结构转变为另一种时，
   形核的能垒可以通过 NEB 方法计算。

### 高级话题

- **自适应 NEB（Adaptive NEB）**：在计算过程中自动调整映像数量
- **二聚体方法（Dimer Method）**：另一种寻找鞍点的方法，只需要一个映像
- **超球面 NEB（Hypersphere NEB）**：对于大原子数系统的改进方法
- **多步 NEB**：对于复杂反应，先用粗粒度 NEB 定位区域，再用精细 NEB 精确计算

---

*本项目为 LAMMPS 学习系列的第 11 个教程。*
*完成本项目后，建议继续学习项目 12：Python 分析工具。*
