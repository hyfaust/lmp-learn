# 项目 04：温度控制与 NVT 系综

## 学习目标

通过本项目的学习，你将能够：

1. **理解统计力学中的系综概念** —— 知道 NVE、NVT、NPT 等系综的物理含义及其适用场景
2. **掌握温度的微观本质** —— 理解温度与原子动能的关系，以及为什么瞬时温度会波动
3. **学会使用 Nosé-Hoover 恒温器** —— 能正确设置 `fix nvt` 命令并理解其参数的物理意义
4. **比较不同恒温器的特点** —— 了解 Nosé-Hoover、Langevin、Berendsen 三种恒温器的原理和适用场景
5. **实现温度斜坡模拟** —— 学会用 NVT 进行升温/降温过程，观察系统的热力学响应

---

## 背景知识

### 统计力学基础

#### 什么是系综 (Ensemble)？

在分子动力学（MD）模拟中，我们追踪每个原子的运动轨迹。但在统计力学中，描述一个宏观系统的方式不是追踪单个轨迹，而是考虑**所有可能状态的集合** —— 这就是**系综**。

可以把系综想象成：如果你能同时运行无穷多次相同的实验，每次从不同的初始条件开始，那么这无穷多次实验在某一时刻的状态集合就是一个系综。

##### 常见的系综类型

| 系综名称 | 守恒量 | 控制量 | 典型用途 |
|---------|--------|--------|---------|
| 微正则系综 (NVE) | 粒子数 N、体积 V、能量 E | 无 | 验证能量守恒、绝热过程 |
| 正则系综 (NVT) | 粒子数 N、体积 V、温度 T | 恒温器 | 等温条件下的模拟 |
| 等温等压系综 (NPT) | 粒子数 N、压强 P、温度 T | 恒温器 + 恒压器 | 最常用的实验条件模拟 |
| 大正则系综 (μVT) | 化学势 μ、体积 V、温度 T | 粒子数可变 | 吸附、蒸发等开体系 |

**微正则系综 (NVE)**：系统的粒子数 N、体积 V 和能量 E 都严格守恒。这是最"自然"的系综 —— 如果你对一组原子只施加牛顿力学，不做任何人为干预，系统就自动处于 NVE 系综。在 LAMMPS 中，使用 `fix nve` 就是 NVE 模拟。

**正则系综 (NVT)**：系统的粒子数 N、体积 V 和温度 T 保持恒定，但能量可以波动。温度通过"恒温器"（thermostat）来控制。恒温器的作用就像一个虚拟的"热浴"，在原子速度上施加额外的力，使系统的平均温度维持在目标值。

**等温等压系综 (NPT)**：同时控制温度和压强。这是最接近真实实验条件的系综 —— 大多数实验都在恒温恒压下进行。

**为什么需要不同的系综？**

实际实验中，我们通常控制的是温度和压强（比如在室温和大气压下做实验），而不是能量。因此 NVT 和 NPT 系综更接近实验条件。但 NVE 系综在验证模拟正确性时非常重要 —— 如果一个系统在 NVE 下总能量不守恒，说明模拟参数有问题。

#### 温度的微观含义

在日常生活中，温度是一个很直观的概念 —— 水烧开了是 100°C，冰水混合物是 0°C。但在分子层面，温度到底是什么？

##### 温度与动能的关系

在经典统计力学中，温度与原子的平均动能直接相关：

$$\frac{3}{2} N k_B T = \sum_{i=1}^{N} \frac{1}{2} m_i v_i^2$$

其中：
- N 是原子数
- k_B 是玻尔兹曼常数（在 LJ 单位下 k_B = 1）
- T 是温度
- m_i 是第 i 个原子的质量
- v_i 是第 i 个原子的速度

也就是说，**温度本质上是原子无序运动剧烈程度的度量**。原子运动越快，温度越高。

##### 温度是统计量

这一点非常重要：**温度只有在原子数足够多时才有意义**。

单个原子没有"温度"这个概念 —— 它只有速度。温度是大量原子速度分布的统计平均。在模拟中，LAMMPS 计算瞬时温度的公式是：

$$T_{inst} = \frac{2}{3 N k_B} \sum_{i=1}^{N} \frac{1}{2} m_i v_i^2$$

##### 温度涨落

即使系统处于热平衡状态，瞬时温度也不会恒定 —— 它会围绕目标温度上下波动。这是正常的物理现象，不是模拟的错误。

对于 N 个原子的系统，温度的相对涨落约为：

$$\frac{\Delta T}{T} \sim \frac{1}{\sqrt{N}}$$

这意味着：
- 100 个原子：相对涨落约 10%，温度波动剧烈
- 1000 个原子：相对涨落约 3%，波动明显
- 100000 个原子：相对涨落约 0.3%，波动很小

这就是为什么小系统的温度看起来很"嘈杂"，而大系统的温度曲线更平滑。

---

### 温度控制方法

在 NVT 和 NPT 系综中，我们需要使用"恒温器"来控制温度。LAMMPS 提供了多种恒温器实现，它们的物理原理和行为各有不同。

#### Nosé-Hoover 恒温器

Nosé-Hoover 是最经典、最广泛使用的恒温器，由日本物理学家 Shūichi Nosé 和美国物理学家 William G. Hoover 在 1980 年代提出。

##### 工作原理

Nosé-Hoover 恒温器的基本思想是：在系统的拉格朗日量中引入一个额外的"热浴"自由度 ζ（读作"zeta"）。这个 ζ 可以理解为一个与系统耦合的虚拟粒子，它会自动调节所有原子的速度。

当系统温度高于目标值时，ζ 为正，相当于给原子施加一个"减速"的摩擦力；当温度低于目标值时，ζ 为负，相当于给原子"加速"。

运动方程变为：

$$\frac{dv_i}{dt} = \frac{F_i}{m_i} - \zeta \cdot v_i$$

$$\frac{d\zeta}{dt} = \frac{1}{Q} \left( \sum_{i} m_i v_i^2 - 3Nk_BT_{target} \right)$$

其中 Q 是"热浴质量"，控制热浴响应的速度。Q 越大，热浴响应越慢，温度调节越温和。

##### LAMMPS 中的使用

```lammps
fix ID group-ID nvt temp T_start T_stop T_damp
```

- **T_start**：初始目标温度
- **T_stop**：最终目标温度（如果与 T_start 不同，温度会线性变化）
- **T_damp**：热浴弛豫时间，与 Q 相关。它是温度调节的特征时间尺度

##### 优点与缺点

- **优点**：能产生正确的正则系综分布，即时间平均等于系综平均
- **优点**：不影响长期动力学性质
- **缺点**：对于非平衡系统，温度振荡可能较大
- **缺点**：不能用于刚体或带有约束的系统（需要使用 Nosé-Hoover 链）

##### LAMMPS 命令

```lammps
# 等温模拟：T = 1.0 保持不变，弛豫时间 0.5
fix 1 all nvt temp 1.0 1.0 0.5

# 温度斜坡：从 0.5 线性升温到 2.0
fix 1 all nvt temp 0.5 2.0 0.5
```

#### Langevin 恒温器

Langevin 恒温器基于朗之万方程（Langevin equation），它模拟的是一个在粘性介质中运动的粒子受到随机撞击的情况。

##### 工作原理

在 Langevin 恒温器中，每个原子的运动方程变为：

$$\frac{dv_i}{dt} = \frac{F_i}{m_i} - \gamma v_i + \frac{R_i}{m_i}$$

其中：
- **F_i / m_i**：来自原子间相互作用的加速度（正常力）
- **-γ v_i**：摩擦力（阻尼项），与速度成正比，γ 是阻尼系数
- **R_i / m_i**：随机力（涨落项），模拟热浴分子的随机撞击

摩擦力和随机力通过**涨落-耗散定理**（fluctuation-dissipation theorem）联系起来：

$$\langle R_i(t) \cdot R_j(t') \rangle = 6 m_i \gamma k_B T \delta_{ij} \delta(t - t')$$

这意味着随机力的强度由阻尼系数 γ 和温度 T 共同决定。两者必须精确匹配，才能产生正确的热平衡。

##### LAMMPS 中的使用

Langevin 恒温器需要与 `fix nve` 配合使用：

```lammps
fix 1 all nve                     # Velocity-Verlet 积分
fix 2 all langevin 1.0 1.0 0.5 12345  # Langevin 力
```

参数说明：
- **T_start, T_stop**：目标温度（与 Nosé-Hoover 含义相同）
- **damping_coefficient**：阻尼系数 γ，单位是 1/时间。典型值 0.1 ~ 10
- **random_seed**：随机数种子，用于生成随机力

##### 优点与缺点

- **优点**：实现简单，数值稳定，不容易出错
- **优点**：温度控制非常"鲁棒"，适用于各种复杂系统
- **缺点**：不是严格的正则系综采样（在有限时间步长下）
- **缺点**：阻尼力会影响动力学性质（如扩散系数、粘度），不适合计算传输性质
- **缺点**：随机力引入额外的噪声

#### Berendsen 恒温器

Berendsen 恒温器由 Herman Berendsen 在 1984 年提出，是最早的恒温方法之一。

##### 工作原理

Berendsen 恒温器的原理非常简单直接：每一步将所有原子的速度乘以一个缩放因子 λ：

$$\lambda = \sqrt{1 + \frac{\Delta t}{\tau_T} \left( \frac{T_{target}}{T_{current}} - 1 \right)}$$

其中：
- Δt 是时间步长
- τ_T 是温度弛豫时间（T_damp 参数）
- T_target 是目标温度
- T_current 是当前瞬时温度

当 T_current > T_target 时，λ < 1，速度被缩小（降温）；当 T_current < T_target 时，λ > 1，速度被放大（升温）。弛豫时间 τ_T 越小，缩放越"激进"，温度收敛越快。

##### LAMMPS 中的使用

Berendsen 恒温器也需要与 `fix nve` 配合使用：

```lammps
fix 1 all nve                          # Velocity-Verlet 积分
fix 2 all temp/berendsen 1.0 1.0 0.5   # Berendsen 温度缩放
```

##### 优点与缺点

- **优点**：温度收敛快且平滑，不会有大振荡
- **优点**：实现简单，计算开销小
- **重大缺点**：**不产生正确的正则系综分布**！系统最终的构型分布不满足 Boltzmann 分布
- **原因**：速度缩放是一个确定性的操作，不引入涨落，破坏了统计力学的基本要求
- **适用场景**：仅用于平衡阶段快速达到目标温度，**不应用于正式数据采集**

---

### fix 命令详解

`fix` 是 LAMMPS 中最重要的命令之一。它用于在模拟过程中对原子施加各种操作 —— 从最基本的运动方程积分，到温度/压强控制，再到数据采集。

#### 基本语法

```lammps
fix ID group-ID style args
```

- **ID**：用户为这个 fix 取的名字（字符串），用于后续引用或删除
- **group-ID**：作用的原子组（`all` 表示所有原子，也可以用 `group` 命令定义子集）
- **style**：fix 的类型（如 `nve`、`nvt`、`langevin`、`temp/berendsen` 等）
- **args**：该 fix 类型特有的参数

#### 多个 fix 同时作用

LAMMPS 允许同时设置多个 fix，它们会按定义顺序依次执行。例如：

```lammps
fix 1 all nve                  # 第一步：积分运动方程
fix 2 all nvt temp 1.0 1.0 0.5 # 第二步：温度控制
fix 3 all ave/time ...          # 第三步：数据采集
```

注意：**一个原子组上不能同时使用两个互相矛盾的 fix**。例如，不能同时使用 `fix nve` 和 `fix nvt`（因为 `fix nvt` 内部已经包含了运动方程积分）。

但 `fix nve` + `fix langevin` 可以同时使用，因为 `fix langevin` 只施加额外的力，不执行积分。

#### 取消 fix

```lammps
unfix ID    # 移除指定的 fix
```

---

## 输入脚本逐行解析

### `in.nvt` 脚本解析

以下是 `in.nvt` 脚本的逐行详细说明：

```lammps
# --- 第一部分：系统初始化和建模 ---

units           lj          # 使用 LJ 约化单位（m=σ=ε=kB=1）
atom_style      atomic      # 原子样式：点粒子，无电荷/键接

# 创建 FCC 晶格，密度 0.8442（LJ 液态标准密度）
lattice         fcc 0.8442

# 建立 8×8×8 的模拟盒子（约 2048 个原子）
region          box block 0 8 0 8 0 8
create_box      1 box       # 创建盒子（1 种原子类型）
create_atoms    1 box       # 在盒子中填充原子

# LJ 势函数，截断半径 2.5σ
pair_style      lj/cut 2.5
pair_coeff      1 1 1.0 1.0 2.5
mass            1 1.0       # 原子质量 = 1
```

**解释**：这部分建立了模拟系统。使用 FCC 晶格和 0.8442 的密度是 LJ 液体模拟中的经典设置，对应液态三相点附近的条件。

```lammps
# --- 第二部分：速度初始化 ---

velocity all create 1.0 54321 mom yes rot yes
```

**解释**：给所有原子分配初始速度。
- `create 1.0` —— 按照温度 T=1.0 的 Maxwell-Boltzmann 分布采样
- `54321` —— 随机数种子
- `mom yes` —— 移除总动量（避免系统整体漂移）
- `rot yes` —— 移除总角动量

为什么需要初始化速度？因为原子初始位置是完美的晶格（势能最低），但速度是随机的。如果不初始化速度，所有原子速度为零，模拟无法开始。

```lammps
# --- 第三部分：NVE 预平衡 ---

timestep        0.005       # 时间步长 0.005 LJ 时间单位
fix             1 all nve   # NVE 积分
thermo          10          # 每 10 步输出
thermo_style    custom step temp pe ke etotal press
run             1000        # 跑 1000 步
unfix           1           # 移除 NVE fix
```

**解释**：先用 NVE 跑 1000 步进行预平衡。这是因为初始速度（随机）和初始位置（完美晶格）不自洽 —— 完美晶格中每个原子的力为零，但随机速度会导致原子偏离平衡位置。短暂的 NVE 运行让系统"自我调节"。

```lammps
# --- 第四部分：NVT 恒温模拟 ---

fix 1 all nvt temp 1.0 1.0 0.5
```

**解释**：这是核心命令！设置 Nosé-Hoover NVT 恒温器。
- `temp 1.0 1.0` —— 目标温度从 1.0 到 1.0（恒温）
- `0.5` —— T_damp 参数（热浴弛豫时间）

```lammps
thermo          100         # 每 100 步输出一次
run             20000       # 跑 20000 步
```

**解释**：每 100 步输出一次温度等热力学量。20000 步的总模拟时间为 20000 × 0.005 = 100 τ。

```lammps
# --- 第五部分：温度斜坡 ---

fix 1 all nvt temp 0.5 2.0 0.5
run             30000
```

**解释**：当 T_start ≠ T_stop 时，恒温器会在整个运行过程中将目标温度从 T_start 线性变化到 T_stop。这里是 30000 步内从 0.5 升温到 2.0，可以观察系统随温度升高的变化（如密度变化、原子排列无序化等）。

---

## 温度控制参数详解

### T_damp 参数

T_damp（热浴弛豫时间）是恒温器中最重要的参数之一，它控制温度调节的速度。

#### 物理意义

T_damp 是温度偏离目标值后，回归到目标值的特征时间。类似于：

- 小 T_damp：像一个"急躁"的控制器，发现温度偏差就大力纠正
- 大 T_damp：像一个"温和"的控制器，缓慢地将温度引向目标值

#### 太小的 T_damp（如 0.01）

```
温度
  ^
  |   /\    /\    /\
  |  /  \  /  \  /  \
  | /    \/    \/    \___    → 温度剧烈振荡
  +-------------------------→ 时间
```

温度会围绕目标值大幅振荡。这是因为恒温器过度反应 —— 每次温度稍有偏离就强力修正，导致"矫枉过正"。

#### 太大的 T_damp（如 100）

```
温度
  ^
  |                         ___  → 最终到达目标
  |                    ___/
  |               ___/
  |          ___/
  |     ___/
  |____/                    → 温度收敛非常慢
  +-------------------------→ 时间
```

温度需要很长时间才能收敛到目标值。在有限的模拟时间内，系统可能始终没有达到平衡。

#### 合适的 T_damp

```
温度
  ^
  |         _______________  → 平稳收敛
  |     ___/
  |    /
  |___/
  +-------------------------→ 时间
```

#### 经验法则

T_damp 的推荐值是 **100 × dt 到 1000 × dt**，其中 dt 是时间步长。

| 时间步长 dt | 推荐 T_damp 范围 | 在 LJ 单位下的典型值 |
|------------|-----------------|-------------------|
| 0.001 | 0.1 ~ 1.0 | 0.1 |
| 0.005 | 0.5 ~ 5.0 | 0.5 |
| 0.002 | 0.2 ~ 2.0 | 0.2 |

对于本项目（dt = 0.005），T_damp = 0.5 是一个合理的选择（= 100 × dt）。

### 温度初始化

#### 为什么需要初始化速度？

模拟开始时，原子通常放在规则的晶格位置上。如果没有初始速度：

1. 所有原子静止 → 温度为零
2. 晶格位置上力为零 → 原子永远不会运动
3. 模拟毫无意义

`velocity create` 命令按照 Maxwell-Boltzmann 分布为每个原子随机分配速度，使系统的初始温度为目标值。

#### velocity create 命令

```lammps
velocity all create T_target random_seed mom yes rot yes
```

- `all`：作用于所有原子
- `create`：从零开始创建速度（覆盖已有速度）
- `T_target`：目标温度
- `random_seed`：随机数种子。相同的种子产生相同的初始速度
  - 不同的种子 → 不同的初始条件 → 温度涨落的细节不同
  - 但统计平均性质（如温度均值）应该相同
  - 这就是为什么多次模拟用不同种子可以验证结果的可靠性
- `mom yes`：移除总动量。不移除的话，整个系统可能有质心运动
- `rot yes`：移除总角动量。类似地，避免系统整体旋转
- `loop geom`（可选）：几何循环方式分配速度，确保每个原子的速度大小合理

#### `loop geom` 参数

当不使用 `loop geom` 时，速度直接从 Maxwell-Boltzmann 分布采样。使用 `loop geom` 时，LAMMPS 通过多次循环调整，使每个原子的速度分量更精确地满足目标温度分布。对于大多数应用，差异很小，不加也可以。

---

## 运行指南

### 环境要求

- 已安装 LAMMPS（命令行可用 `lmp`）
- 可选：OVITO 或 VMD 用于可视化轨迹

### 运行命令

```bash
# 运行 NVT 模拟（含 NVE 预平衡和温度斜坡）
lmp -in in.nvt

# 运行三种恒温器比较
lmp -in in.nvt_compare
```

### 查看输出

模拟完成后，会生成以下文件：

**`in.nvt` 产生的文件：**
- `dump.nvt.lammpstrj` — NVT 恒温阶段的轨迹（T=1.0，20000 步）
- `dump.ramp.lammpstrj` — 温度斜坡阶段的轨迹（0.5→2.0，30000 步）
- `restart.nvt` — 二进制重启文件

**`in.nvt_compare` 产生的文件：**
- `temp_nose_hoover.dat` — Nosé-Hoover 恒温器的温度数据
- `temp_langevin.dat` — Langevin 恒温器的温度数据
- `temp_berendsen.dat` — Berendsen 恒温器的温度数据
- `log.nose_hoover` / `log.langevin` / `log.berendsen` — 各自的完整 LAMMPS 日志

### 可视化轨迹

用 OVITO 打开 `.lammpstrj` 文件：

```bash
ovito dump.nvt.lammpstrj
```

### 绘制温度比较图

使用 Python + matplotlib 绘制三种恒温器的温度对比：

```python
import numpy as np
import matplotlib.pyplot as plt

# 加载数据（跳过前几行注释）
nh = np.loadtxt('temp_nose_hoover.dat', skiprows=3)
la = np.loadtxt('temp_langevin.dat', skiprows=3)
be = np.loadtxt('temp_berendsen.dat', skiprows=3)

fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(nh[:, 0] * 0.005, nh[:, 1], label='Nosé-Hoover', alpha=0.8)
ax.plot(la[:, 0] * 0.005, la[:, 1], label='Langevin', alpha=0.8)
ax.plot(be[:, 0] * 0.005, be[:, 1], label='Berendsen', alpha=0.8)

ax.axhline(y=1.0, color='k', linestyle='--', label='目标温度 T=1.0')
ax.set_xlabel('模拟时间 (LJ 单位)')
ax.set_ylabel('温度 (LJ 单位)')
ax.set_title('三种恒温器的温度控制行为对比')
ax.legend()
plt.tight_layout()
plt.savefig('thermostat_comparison.png', dpi=150)
plt.show()
```

---

## 预期输出

### NVT 恒温阶段

运行 `in.nvt` 后，你应该观察到：

1. **温度收敛**：初始温度可能偏离 1.0（因为 NVE 预平衡会改变温度），但经过约 1000-2000 步 NVT 运行后，温度会收敛到 1.0 附近
2. **温度涨落**：收敛后，温度在 1.0 附近波动，波动幅度约为 ±0.05 ~ ±0.1（对于 ~2048 个原子的系统）
3. **能量变化**：
   - 势能（PE）：逐渐趋于稳定
   - 动能（KE）：围绕 (3/2)NkT = 1.5 × T 波动
   - 总能量（E_total）：在 NVT 下不守恒（恒温器会注入/抽取能量）

### 温度斜坡阶段

运行温度斜坡（0.5 → 2.0）时：

1. **温度线性上升**：温度跟随目标温度从 0.5 线性增加到 2.0
2. **势能增加**：温度升高，原子运动加剧，平均原子间距增大，势能变得更正（更接近零）
3. **密度变化**：如果盒子可变（NPT），密度会下降。本项目是固定盒子（NVT），所以密度不变，但压强会显著增加

### 恒温器比较

运行 `in.nvt_compare` 后，你应该观察到：

| 特征 | Nosé-Hoover | Langevin | Berendsen |
|------|------------|----------|-----------|
| 收敛速度 | 中等 | 快 | 最快 |
| 温度振荡 | 有周期性振荡 | 有随机噪声 | 平滑无振荡 |
| 平衡时涨落 | 正确的统计涨落 | 偏大的涨落 | 偏小的涨落 |
| 物理正确性 | 正确 | 近似正确 | **不正确** |
| 能量守恒 | 总能量波动 | 总能量波动大 | 总能量平稳 |

---

## 练习题

### 练习 1：探索 T_damp 的影响

修改 `in.nvt` 中的 T_damp 参数，分别使用 T_damp = 0.01, 0.1, 1.0, 10.0 运行模拟。观察并记录：

1. 温度收敛的速度有何不同？
2. 温度振荡的幅度有何不同？
3. 哪个值给你"最好"的温度控制？为什么？

```lammps
# 尝试不同的 T_damp
fix 1 all nvt temp 1.0 1.0 0.01   # 极小值
fix 1 all nvt temp 1.0 1.0 0.1    # 较小值
fix 1 all nvt temp 1.0 1.0 1.0    # 较大值
fix 1 all nvt temp 1.0 1.0 10.0   # 极大值
```

### 练习 2：观察相变现象

将目标温度从 1.0 改为很低的值（如 0.1）或很高的值（如 3.0），观察：

1. 低温时：原子是否会排列成更有序的结构？（可能结晶）
2. 高温时：系统是否呈现更"气态"的行为？
3. 用 OVITO 可视化不同温度下的原子构型

```lammps
# 降温到 0.1，观察结晶
fix 1 all nvt temp 1.0 0.1 0.5
run 50000

# 升温到 3.0，观察汽化
fix 1 all nvt temp 1.0 3.0 0.5
run 50000
```

### 练习 3：对比 NVE 和 NVT 的能量行为

分别运行 NVE 和 NVT 模拟（各 10000 步），对比：

1. NVE 下总能量是否守恒？波动有多大？
2. NVT 下总能量是否守恒？为什么？
3. NVT 下温度和势能之间有什么关联？

```lammps
# NVE 模拟
fix 1 all nve
thermo_style custom step temp pe ke etotal
run 10000

# NVT 模拟
unfix 1
fix 1 all nvt temp 1.0 1.0 0.5
run 10000
```

### 练习 4：分组温度控制

将原子分为两组，分别施加不同的温度，创建温度梯度：

```lammps
# 将原子按 x 坐标分为两组
group left  region left_half
group right region right_half

region left_half  block 0 4 INF INF INF INF
region right_half block 4 8 INF INF INF INF

# 左半部分：低温 T = 0.5
fix 1 left  nvt temp 0.5 0.5 0.5
# 右半部分：高温 T = 2.0
fix 2 right nvt temp 2.0 2.0 0.5

run 20000
```

观察热量如何从高温区流向低温区。这模拟了一个基本的热传导实验。

### 练习 5：验证温度的统计性质

运行一个较长的 NVT 模拟（50000 步），在平衡后（丢弃前 10000 步）计算：

1. 温度的均值 `<T>`：应该接近 1.0
2. 温度的标准差 `σ_T`：应该约为 `T * sqrt(2 / (3N))`
3. 对于 N ≈ 2048 个原子，σ_T ≈ 1.0 × sqrt(2/6144) ≈ 0.018

```python
import numpy as np
data = np.loadtxt('temp_nose_hoover.dat', skiprows=3)
# 丢弃前 2000 个数据点（前 10000 步的平衡阶段）
temp_equil = data[2000:, 1]
print(f"温度均值: {np.mean(temp_equil):.4f}")
print(f"温度标准差: {np.std(temp_equil):.4f}")
N = 2048
print(f"理论标准差: {1.0 * np.sqrt(2/(3*N)):.4f}")
```

---

## 参考资料

- [Nosé-Hoover 恒温器 (fix nvt) 官方文档](https://docs.lammps.org/stable/fix_nh.html)
- [Langevin 恒温器 (fix langevin) 官方文档](https://docs.lammps.org/stable/fix_langevin.html)
- [Berendsen 恒温器 (fix temp/berendsen) 官方文档](https://docs.lammps.org/stable/fix_temp_berendsen.html)
- [LAMMPS fix 命令总览](https://docs.lammps.org/stable/fix.html)
- Nosé, S. (1984). "A unified formulation of the constant temperature molecular dynamics methods." *Journal of Chemical Physics*, 81(1), 511-519.
- Hoover, W. G. (1985). "Canonical dynamics: Equilibrium phase-space distributions." *Physical Review A*, 31(3), 1695-1697.
- Berendsen, H. J. C. et al. (1984). "Molecular dynamics with coupling to an external bath." *Journal of Chemical Physics*, 81(8), 3684-3690.
- Frenkel, D. & Smit, B. *Understanding Molecular Simulation*, Chapter 5 — 系综与恒温器的经典教材
