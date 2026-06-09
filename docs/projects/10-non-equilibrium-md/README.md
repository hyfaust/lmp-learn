# 项目 10：非平衡分子动力学

## 学习目标

完成本项目后，你将能够：

1. **理解非平衡分子动力学（NEMD）的基本原理**：知道 NEMD 与平衡态 MD 的区别，以及何时需要使用 NEMD
2. **实现 Couette 剪切流模拟**：使用 `fix deform` 命令和 Lees-Edwards 边界条件对流体施加剪切
3. **分析速度剖面**：使用 `compute chunk/atom` 将原子分层，计算各层的平均速度，验证线性速度分布
4. **通过 NEMD 方法计算粘度**：从剪切应力和剪切速率的关系 η = σ_xy / γ̇ 得到粘度
5. **通过 Green-Kubo 方法计算粘度**：利用平衡态应力涨落的自相关函数，积分得到粘度，并与 NEMD 结果对比

---

## 背景知识

### 平衡 vs 非平衡 MD

分子动力学模拟可以分为两大类：

**平衡态 MD（Equilibrium MD, EMD）**：
- 系统处于热力学平衡状态，没有外部驱动力
- 计算的是平衡态性质：密度、扩散系数、径向分布函数等
- 系统的宏观性质不随时间变化（涨落围绕平均值波动）
- 适用于计算"静态"热力学量

**非平衡态 MD（Non-Equilibrium MD, NEMD）**：
- 对系统施加外部扰动（如剪切力、温度梯度、压力梯度等）
- 研究系统对外部扰动的响应
- 系统处于稳态（不是平衡态），但宏观性质不再随时间变化
- 适用于计算"输运"性质：粘度、热导率、电导率等

**一个直观的类比**：
- 平衡态 MD 就像观察一盆静止的水面——水面只有微小的热涨落
- NEMD 就像用搅拌棒搅动水面——你会看到有组织的流动模式

**NEMD 的优势**：
- 可以直接"看到"流体的流动行为（速度剖面、流场）
- 计算结果通常比 Green-Kubo 方法更快收敛
- 物理图像直观，便于理解

**NEMD 的局限**：
- 施加的扰动是人为的，可能偏离真实物理条件
- 剪切速率太大时，系统远离平衡态，结果不准确
- 需要在多个剪切速率下计算，再外推到零剪切速率

---

### 流体力学基础

#### 什么是粘度？

粘度（viscosity）是流体抵抗剪切变形的能力。想象两种液体：水和蜂蜜。用勺子搅动它们时，蜂蜜更难搅动——这就是因为蜂蜜的粘度更高。

粘度是流体最重要的输运性质之一，它决定了流体在管道中的流动阻力、润滑效果、混合效率等。

#### 牛顿流体

对于大多数简单流体（如水、空气、液态金属），剪切应力与剪切速率成正比：

```
τ = η × (dv/dy)
```

其中：
- **τ**（tau）：剪切应力（单位面积上的切向力，Pa）
- **η**（eta）：动力粘度（Pa·s）
- **dv/dy**：速度梯度（也叫剪切速率 γ̇，单位 s⁻¹）

满足这个线性关系的流体称为**牛顿流体**。

注意：许多复杂流体（如聚合物溶液、血液）是非牛顿流体，它们的粘度会随剪切速率变化（剪切变稀或剪切变稠）。

#### 层流与湍流

- **层流（Laminar flow）**：流体分层流动，各层互不混合，流动有序
- **湍流（Turbulent flow）**：流体运动混乱，充满涡旋和涨落

在 MD 模拟中，由于模拟尺度极小（纳米量级），几乎总是处于层流状态。湍流需要在宏观尺度才能出现。

#### 雷诺数（Reynolds Number）

雷诺数 Re 是判断流动状态的无量纲数：

```
Re = ρ × v × L / η
```

其中 ρ 是密度，v 是流速，L 是特征长度，η 是粘度。

- Re < ~2000：层流
- Re > ~4000：湍流
- 2000 < Re < 4000：过渡区

在 MD 模拟中，由于 L 极小（纳米级），Re 通常远小于 1，流动总是层流。

---

### Couette 流

Couette 流是最简单的剪切流模型：两块无限大的平行平板之间充满流体，上板以恒定速度 U 移动，下板静止不动。

```
    ──────────────→  U (上板速度)
    ═══════════════  上板
    ─ ─ ─ ─ ─ ─ ─   流体层（速度从 U 线性减小到 0）
    ─ ─ ─ ─ ─ ─ ─
    ─ ─ ─ ─ ─ ─ ─
    ═══════════════  下板（静止）
```

**速度分布**：

对于牛顿流体的 Couette 流，速度在两板之间线性分布：

```
vx(y) = U × (y / H)
```

其中 H 是两板之间的距离。这意味着：
- 在下板处（y=0）：vx = 0（无滑移边界条件）
- 在上板处（y=H）：vx = U
- 中间各处：vx 随 y 线性增加

**剪切速率**：

```
γ̇ = dvx/dy = U / H （常数）
```

整个流场中的剪切速率是均匀的，这使得 Couette 流非常适合用来测量粘度。

**在 MD 中如何实现 Couette 流**：

在 MD 模拟中没有真正的"板"，我们使用 **Lees-Edwards 边界条件**来实现剪切。详见下一节。

---

### Lees-Edwards 边界条件

#### 为什么普通周期性边界不能产生剪切？

在普通周期性边界条件中，盒子的顶部和底部之间没有相对运动。如果一个粒子从顶部飞出，它会从底部以相同速度飞入——这不可能产生剪切流。

#### Lees-Edwards 的核心思想

Lees-Edwards 边界条件通过让盒子的上下边界产生持续的相对位移来模拟剪切。想象把一叠扑克牌放在桌上，推动最上面一张牌——每张牌都会相对下一张发生位移，整叠牌形成剪切变形。

```
    普通周期性边界:          Lees-Edwards 边界:
    ┌─────────────┐         ┌─────────────┐
    │  ───→       │         │    ───→      │→ (+Δx)
    │  ───→       │         │   ───→       │
    │  ───→       │         │  ───→        │
    │  (无流动)    │         │ ───→         │→ (-Δx)
    └─────────────┘         └─────────────┘
```

#### 在 LAMMPS 中的实现

LAMMPS 通过 `fix deform` 命令实现 Lees-Edwards 边界条件：

```lammps
fix 2 all deform 1 xy erate 0.01 remap v
```

参数解释：
- `1`：每 1 步执行一次变形
- `xy`：在 xy 平面施加剪切（盒子在 x 方向的偏移量随 y 线性变化）
- `erate 0.01`：恒定剪切应变率 γ̇ = 0.01（每 LJ 时间单位）
- `remap v`：原子速度随盒子变形重新映射（不是重新映射位置）

#### 剪切速率的选择

剪切速率 γ̇ 的选择很重要：
- **太小**（如 γ̇ = 0.0001）：信号（剪切应力涨落）太弱，需要极长的模拟时间才能获得可靠的结果
- **太大**（如 γ̇ = 1.0）：系统远离平衡态，流动可能变得不稳定，产生非物理效应（如粘性加热）
- **推荐范围**：γ̇ = 0.001 ~ 0.05（对于 LJ 液体）

最终的零剪切粘度需要通过在多个剪切速率下计算，然后外推到 γ̇ = 0 来获得。

---

### 粘度计算方法

分子动力学中有两种主要的方法来计算剪切粘度：

#### 方法 1：NEMD（非平衡方法）

**基本原理**：施加一个已知的剪切速率 γ̇，测量系统产生的剪切应力 σ_xy，然后用牛顿粘性定律计算粘度：

```
η = σ_xy / γ̇
```

**步骤**：
1. 建立一个液态系统
2. 使用 `fix deform` 施加恒定剪切速率
3. 运行足够长时间，等待系统达到稳态
4. 收集剪切应力 σ_xy 的时间平均值
5. 计算 η = <σ_xy> / γ̇

**注意事项**：
- 需要在稳态下采集数据（开始的几千步应丢弃）
- 需要在多个剪切速率下计算
- 将 η 对 γ̇ 作图，外推到 γ̇ = 0 得到零剪切粘度 η₀

```
η(γ̇)
│
│  ×
│    ×
│      ×
│        ×
│          ×  ×  ×
│──────────────────→ γ̇
η₀ (外推值)
```

#### 方法 2：Green-Kubo（平衡态方法）

**基本原理**：基于涨落-耗散定理（Fluctuation-Dissipation Theorem），剪切粘度可以通过平衡态下应力涨落的自相关函数来计算：

```
η = (V / kBT) × ∫₀^∞ <σxy(0) · σxy(t)> dt
```

其中：
- V = 体系体积
- kB = 玻尔兹曼常数
- T = 温度
- σxy(t) = 时刻 t 的剪切应力分量
- <σxy(0) · σxy(t)> = 应力自相关函数（SACF）

**物理直觉**：
- 平衡态中，应力 σxy 会随机涨落（有时正，有时负）
- 涨落的"记忆"（自相关函数的衰减速率）与粘度有关
- 粘度大的流体，应力涨落衰减慢（"记忆"长）
- 粘度小的流体，应力涨落衰减快（"记忆"短）

**步骤**：
1. 建立一个液态系统，充分平衡
2. 切换到 NVE 系综（重要！恒温器会干扰应力涨落）
3. 使用 `fix ave/correlate` 计算 σxy 的自相关函数
4. 对自相关函数做数值积分
5. 乘以前因子 V/(kBT) 得到粘度

**注意事项**：
- 必须在 NVE 系综下运行（恒温器会人为修改应力）
- 统计噪声大，需要很长的运行时间（通常 > 100,000 步）
- 可以同时使用 σxy、σxz、σyz 三个分量取平均来减少噪声
- 积分结果应达到一个平台值；如果还在增长，说明模拟时间不够

#### 两种方法的对比

| 特征 | NEMD | Green-Kubo |
|------|------|------------|
| 是否施加外部扰动 | 是（剪切流） | 否（平衡态） |
| 需要的模拟时间 | 较短 | 较长 |
| 统计噪声 | 较小 | 较大 |
| 物理图像 | 直观（看到流动） | 抽象（统计涨落） |
| 是否需要外推 | 需要（外推到 γ̇=0） | 不需要 |
| 可计算的性质 | 仅零剪切粘度 | 仅零剪切粘度 |
| 实现复杂度 | 简单 | 稍复杂 |

**建议**：对于初学者，NEMD 方法更直观，推荐先学习 NEMD。Green-Kubo 方法是验证 NEMD 结果的好工具。

---

### 速度剖面分析

#### 如何将原子分层

在模拟中，我们需要将原子按位置分成若干"层"（slab），计算每层的平均速度。LAMMPS 提供了 `compute chunk/atom` 来完成这个任务：

```lammps
compute layers all chunk/atom bin/1d y lower 1.0 units box
```

这行命令的含义：
- 将所有原子按 y 坐标分组
- `bin/1d y`：沿 y 方向做一维分箱
- `lower 1.0`：从盒子底部开始，每层宽度 1.0σ
- `units box`：使用真实长度单位（而非晶格单位）

然后用 `fix ave/chunk` 计算每层的时间平均速度：

```lammps
fix 4 all ave/chunk 10 10 100 layers vx file velocity_profile.dat
```

参数含义：
- `10 10 100`：每 10 步采样一次，每 10 次采样取平均，每 100 步输出一次
- `layers`：使用前面定义的分层方案
- `vx`：计算每层的 x 方向速度分量

#### 验证线性速度分布

对于 Couette 流，速度剖面应为线性分布：

```
vx
│       /
│      /
│     /
│    /
│   /
│  /
│ /
│/______________→ y
```

如果你绘制出的速度分布偏离线性，可能的原因：
1. **尚未达到稳态**：模拟运行时间不够
2. **剪切速率太大**：产生了非线性效应
3. **统计不足**：每层的原子数太少，涨落大
4. **壁面滑移**：在特殊情况下可能出现

#### 非线性效应

当剪切速率很大时，可能出现：
- **剪切变稀（Shear thinning）**：表观粘度随 γ̇ 增大而减小
- **剪切增稠（Shear thickening）**：表观粘度随 γ̇ 增大而增大
- **速度剖面非线性**：不再是直线

---

## 输入脚本逐行解析

### `in.shear` — Couette 剪切流

这个脚本模拟 LJ 液体在剪切作用下的行为，计算速度剖面和粘度。

#### 第 1 部分：初始化和模型搭建

```lammps
clear
units           lj
atom_style      atomic
```

- `clear`：清除所有旧定义，确保干净的开始
- `units lj`：使用 LJ 约化单位（长度 σ，能量 ε，质量 m，时间 τ = σ√(m/ε)）
- `atom_style atomic`：最基本的原子样式，每原子只有位置和速度

```lammps
lattice         fcc 0.8442
region          box block 0 20 0 40 0 10
create_box      1 box
create_atoms    1 box
```

- `lattice fcc 0.8442`：创建 FCC 晶格，密度 ρ* = 0.8442（这是 LJ 液体在 T*=1.4 的平衡密度）
- `region box block 0 20 0 40 0 10`：定义模拟盒子
  - x 方向：20σ（剪切方向）
  - y 方向：40σ（速度梯度方向，较长以获得好的速度剖面分辨率）
  - z 方向：10σ（较薄，接近 2D 行为）
- `create_box`/`create_atoms`：创建盒子并在其中填充原子

```lammps
mass            1 1.0
pair_style      lj/cut 2.5
pair_coeff      1 1 1.0 1.0 2.5
```

- `mass 1 1.0`：原子质量 = 1.0（LJ 单位）
- `pair_style lj/cut 2.5`：标准 LJ 势，截断半径 2.5σ
- `pair_coeff 1 1 1.0 1.0 2.5`：ε=1.0，σ=1.0，rc=2.5

#### 第 2 部分：初始平衡

```lammps
velocity        all create 1.4 12345
fix             1 all nvt temp 1.4 1.4 0.5
run             10000
unfix           1
```

- 用随机速度初始化温度为 T*=1.4
- 用 NVT 系综运行 10000 步进行平衡
- 这一步很重要：让系统先达到平衡态，再施加剪切
- `unfix 1`：解除平衡阶段的 NVT 约束

#### 第 3 部分：施加剪切

```lammps
reset_timestep  0
fix             2 all deform 1 xy erate 0.01 remap v
fix             3 all nvt temp 1.4 1.4 0.5
```

- `reset_timestep 0`：重置时间步计数器
- `fix 2 all deform 1 xy erate 0.01 remap v`：**这是 NEMD 的核心命令**
  - 施加 xy 平面的剪切，剪切速率 γ̇ = 0.01
  - `remap v`：原子速度随盒子变形重新映射
- `fix 3 all nvt`：用 NVT 系综控制温度（NEMD 中需要恒温器，因为剪切会产生热量）

#### 第 4 部分：计算速度剖面

```lammps
compute         layers all chunk/atom bin/1d y lower 1.0 units box
fix             4 all ave/chunk 10 10 100 layers vx file velocity_profile.dat
```

- 将原子沿 y 方向分成 40 层（每层 1σ 宽）
- 计算每层的 x 方向平均速度，每 100 步输出一次
- 结果保存在 `velocity_profile.dat`

#### 第 5 部分：计算应力

```lammps
compute         stress all stress/atom NULL
variable        sxy equal c_stress[4]
fix             5 all ave/time 1 1 100 v_sxy file stress.dat
```

- `compute stress/atom`：计算每个原子的应力张量
- `c_stress[4]`：提取 xy 分量（第 4 个分量）
- `fix ave/time`：做时间平均，输出到 `stress.dat`

#### 第 6 部分：运行

```lammps
run             50000
```

运行 50000 步（在 LJ 时间单位下约为 250τ，足够达到稳态）。

#### 第 7 部分：计算粘度

最终的粘度计算：η = <σ_xy> / γ̇ = <σ_xy> / 0.01

你需要从 `stress.dat` 中读取 σ_xy 的时间平均值，代入公式计算。

---

### `in.viscosity_gk` — Green-Kubo 粘度

这个脚本通过平衡态应力涨落来计算粘度，不施加任何外部扰动。

#### 第 1 部分：初始化

与 `in.shear` 类似，但使用正方体盒子（各边 10σ），因为不需要速度梯度方向有特殊尺寸。

#### 第 2 部分：NVT 平衡

运行 20000 步 NVT 平衡，让系统充分弛豫。

#### 第 3 部分：切换到 NVE

```lammps
reset_timestep  0
fix             2 all nve
```

**关键点**：必须使用 NVE 系综！恒温器会人为修改原子速度，从而"污染"应力涨落，导致自相关函数不准确。这就像你在测量水面的自然波动时，却用机器在不断搅动水面——你测到的就不是真正的自然波动了。

#### 第 4 部分：应力计算

```lammps
compute         myPress all pressure NULL
variable        pxy equal c_myPress[4]
variable        pxz equal c_myPress[5]
variable        pyz equal c_myPress[6]
```

计算全局压力张量（压力 = -应力/体积），提取三个剪切分量。

注意：LAMMPS 中 `compute pressure` 输出的是压力而非应力，但在自相关函数中两者的符号差异会被抵消（因为是两个相乘）。

#### 第 5 部分：自相关函数

```lammps
fix sacf all ave/correlate 1 1 100 &
    v_pxy v_pxz v_pyz &
    type auto file sacf.dat overwrite ave running
```

这是 Green-Kubo 方法的核心：
- 每步采样，每 100 步输出一次自相关函数
- 同时计算三个剪切分量的自相关（后续取平均以降低噪声）
- `ave running`：做累积平均，随时间推移统计会越来越精确
- 输出到 `sacf.dat`，格式为：时间延迟、三个分量的自相关值、采样次数

#### 第 6-7 部分：运行和后处理

运行 100000 步。脚本最后给出了 Python 后处理的伪代码。

---

## 运行指南

### 前置条件

- 已安装 LAMMPS，且 `lmp` 命令可用

### 运行 NEMD 剪切模拟

```bash
cd /home/faust/vibe/lmp_learn/projects/10-non-equilibrium-md/
lmp -in in.shear
```

运行完成后会生成：
- `velocity_profile.dat`：速度剖面数据
- `stress.dat`：剪切应力时间序列
- `final_shear.dat`：最终原子构型

### 运行 Green-Kubo 粘度计算

```bash
lmp -in in.viscosity_gk
```

运行完成后会生成：
- `sacf.dat`：应力自相关函数数据
- `final_equilibrium.dat`：最终原子构型

### 结果分析（Python）

#### 绘制速度剖面

```python
import numpy as np
import matplotlib.pyplot as plt

# 读取速度剖面数据
# 跳过前 3 行注释行
# 列：Chunk_ID | Coord | Ncount | vx
data = np.loadtxt('velocity_profile.dat', skiprows=3)

y = data[:, 1]    # y 坐标（层的中心位置）
vx = data[:, 3]   # x 方向平均速度

plt.figure(figsize=(8, 6))
plt.plot(y, vx, 'bo-', markersize=4)
plt.xlabel('y (σ)')
plt.ylabel('vx (σ/τ)')
plt.title('Couette Flow Velocity Profile')
plt.grid(True)
plt.savefig('velocity_profile.png', dpi=150)
plt.show()

# 拟合线性关系：vx = a * y + b
coeffs = np.polyfit(y, vx, 1)
print(f"速度梯度 (dvx/dy) = {coeffs[0]:.4f} σ/τ per σ")
print(f"预期剪切速率 γ̇ = 0.01")
```

#### 计算 NEMD 粘度

```python
import numpy as np

# 读取应力数据
data = np.loadtxt('stress.dat', skiprows=2)
# 列：TimeStep | sxy | sxx | syy

sxy = data[:, 1]   # 剪切应力 σ_xy

# 计算时间平均（丢弃前 20% 作为弛豫期）
n_discard = len(sxy) // 5
sxy_avg = np.mean(sxy[n_discard:])

shear_rate = 0.01   # 设定的剪切速率
viscosity = sxy_avg / shear_rate

print(f"平均剪切应力 <σ_xy> = {sxy_avg:.6f}")
print(f"剪切速率 γ̇ = {shear_rate}")
print(f"粘度 η = <σ_xy> / γ̇ = {viscosity:.4f}")
```

#### 计算 Green-Kubo 粘度

```python
import numpy as np
import matplotlib.pyplot as plt

# 读取自相关函数数据
data = np.loadtxt('sacf.dat', skiprows=3)
# 列：TimeDelay | Cxy | Cxz | Cyz | Ncount

t = data[:, 0]              # 时间延迟（步数）
Cxy = data[:, 1]            # σxy 的自相关
Cxz = data[:, 2]            # σxz 的自相关
Cyz = data[:, 3]            # σyz 的自相关

# 取三个分量的平均值（降低噪声）
C = (Cxy + Cxz + Cyz) / 3.0

# 时间步长和模拟参数
dt = 0.005          # LJ 单位的时间步长
T = 1.4             # 温度
V = 10**3           # 体积（10σ 的立方体）
kB = 1.0            # LJ 单位中 kB = 1

# 数值积分（梯形法则）
I = np.cumsum(C) * dt

# 计算粘度
eta = (V / (kB * T)) * I

# 绘制粘度随积分时间的变化
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.plot(t * dt, C)
plt.xlabel('Time (τ)')
plt.ylabel('SACF')
plt.title('Stress Autocorrelation Function')
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(t * dt, eta)
plt.xlabel('Integration time (τ)')
plt.ylabel('Viscosity (ε/σ³·τ)')
plt.title('Green-Kubo Viscosity (look for plateau)')
plt.grid(True)

plt.tight_layout()
plt.savefig('green_kubo_viscosity.png', dpi=150)
plt.show()

# 取平台值作为最终粘度
# 平台通常出现在积分时间的中间区域
plateau_start = len(eta) // 4
plateau_end = len(eta) * 3 // 4
viscosity_gk = np.mean(eta[plateau_start:plateau_end])
print(f"Green-Kubo 粘度 η = {viscosity_gk:.4f}")
```

---

## 练习题

### 练习 1：改变剪切速率——观察剪切变稀/变稠行为

**任务**：在 γ̇ = 0.001, 0.005, 0.01, 0.02, 0.05 五个剪切速率下分别运行 `in.shear`，计算每个速率下的粘度。

**要点**：
- 修改脚本中 `fix deform` 的 `erate` 参数
- 每次运行后从 `stress.dat` 计算粘度
- 绘制 η vs γ̇ 的关系图
- 讨论是否观察到剪切变稀或剪切增稠现象

**提示**：
```lammps
# 只需修改这一行中的 erate 值
fix 2 all deform 1 xy erate 0.001 remap v   # 改为其他值
```

### 练习 2：计算不同温度下的粘度

**任务**：在 T* = 0.8, 1.0, 1.2, 1.4, 1.6 五个温度下运行 NEMD 模拟，计算每个温度下的粘度。

**要点**：
- 修改初始化温度、平衡阶段的温度、以及 NEMD 阶段的温度
- 密度保持不变（ρ* = 0.8442）
- 绘制 η vs T 的关系图
- 讨论粘度随温度的变化趋势

**物理预期**：
- 对于简单液体，粘度通常随温度升高而降低（类似水在高温下更容易流动）
- 这与气体相反（气体粘度随温度升高而增大）

### 练习 3：对比 NEMD 和 Green-Kubo 方法

**任务**：在相同条件下（T*=1.4, ρ*=0.8442），分别用 NEMD 和 Green-Kubo 方法计算粘度，比较结果是否一致。

**要点**：
- NEMD：用最小的剪切速率（如 γ̇ = 0.001），减少远离平衡态的效应
- Green-Kubo：运行足够长时间，确保自相关函数积分达到平台
- 两种方法的结果应在误差范围内一致
- 讨论两种方法各自的优缺点

### 练习 4：研究密度对粘度的影响

**任务**：在 ρ* = 0.5, 0.6, 0.7, 0.8, 0.9 五个密度下运行模拟，计算粘度。

**要点**：
- 修改 `lattice` 命令中的密度参数
- 密度越高，粘度越大（更稠密的液体更难流动）
- 绘制 η vs ρ 的关系图
- 可以用幂律拟合：η ∝ ρ^α

**提示**：
```lammps
# 修改密度参数
lattice         fcc 0.5    # 改为其他密度值
```

注意：密度很低时（如 0.3 以下）系统可能是气态而非液态。

### 练习 5：实现 Poiseuille 流（压力驱动流）

**任务**：修改脚本，用外力驱动流体在两个固定壁面之间流动，模拟 Poiseuille 流。

**要点**：
- 不再使用 `fix deform`，而是用 `fix addforce` 施加体积力
- 在盒子的顶部和底部创建固定壁面（冻结原子）
- 速度剖面应为抛物线型（而非 Couette 流的线性）
- Poiseuille 流的理论速度分布：vx(y) ∝ y(H-y)

**实现思路**：
```lammps
# 定义流动区域（排除壁面原子）
region  flow block INF INF 2.0 38.0 INF INF
group   mobile region flow

# 施加体积力（模拟压力梯度）
# 力沿 x 方向，大小 f = ΔP/(ρL)
fix drive mobile addforce 0.1 0.0 0.0

# 壁面原子不动
group   wall subtract all mobile
velocity wall set 0.0 0.0 0.0
fix     freeze wall setforce 0.0 0.0 0.0
```

预期的速度剖面：
```
vx
│    ╱  ╲        (抛物线)
│   ╱    ╲
│  ╱      ╲
│ ╱        ╲
│╱──────────╲___→ y
壁面          壁面
```

---

## 参考资料

- [fix deform 命令文档](https://docs.lammps.org/stable/fix_deform.html)
- [compute viscosity 命令文档](https://docs.lammps.org/stable/compute_viscosity.html)
- [Howto: Viscosity 计算指南](https://docs.lammps.org/stable/Howto_viscosity.html)
- [fix ave/correlate 命令文档](https://docs.lammps.org/stable/fix_ave_correlate.html)
- [compute stress/atom 命令文档](https://docs.lammps.org/stable/compute_stress_atom.html)
- [compute chunk/atom 命令文档](https://docs.lammps.org/stable/compute_chunk_atom.html)
