# 项目 09：扩散与输运性质

## 学习目标

1. 理解径向分布函数（RDF）的物理意义，学会用它描述液体的局部结构
2. 掌握均方位移（MSD）的概念，理解从弹道运动到扩散运动的过渡
3. 学会从 MSD 曲线的斜率提取扩散系数 D
4. 了解 Green-Kubo 方法计算扩散系数的原理（通过速度自相关函数）
5. 掌握 LAMMPS 中 `compute msd`、`compute rdf`、`compute vacf` 及 `fix ave/time` 的使用方法

---

## 背景知识

### 径向分布函数 (RDF)

#### 定义

径向分布函数 g(r) 描述了在距离某个参考原子 r 处找到另一个原子的**相对概率**。数学上定义为：

```
               1          n(r)
g(r) = ───────────────── × ────
        理想气体的数密度      4πr²Δr
```

其中 n(r) 是在 r 到 r+Δr 壳层内找到的原子数，ρ 是体系的数密度。

简单来说：**g(r) = 在距离 r 处实际找到原子的概率 / 理想气体中找到原子的概率**。

#### 物理意义

RDF 是描述液体和非晶态固体局部结构最重要的函数之一。它告诉我们：

- 原子周围的**近邻壳层**在哪里
- 每个壳层中有多少原子（通过积分峰面积得到配位数）
- 体系的**有序程度**如何

#### RDF 的特征

对于典型的液体（LJ 液体），g(r) 的曲线大致如下：

```
g(r)
  |
2 |     *
  |    * *
  |   *   *
  |  *     *
1 |-*-------*-----------*----------  ← 长距离趋于 1
  |  *       *       * * * *
  |   *       *   *        *
  |    *       * *          *
0 |_____**__*_________________________ r/σ
  0   1   2   3   4   5
      ↑       ↑
   第一峰    第二峰
   (最近邻)  (次近邻)
```

各区域的物理含义：

| 区域 | 位置 | 含义 |
|------|------|------|
| r < σ 附近 | g(r) ≈ 0 | 原子不能重叠，硬核排斥 |
| **第一峰** | r ≈ 1.1σ | 最近邻壳层，峰最高最尖锐 |
| 第一谷 | r ≈ 1.5σ | 最近邻与次近邻之间的空隙 |
| **第二峰** | r ≈ 2.0σ | 次近邻壳层，比第一峰矮且宽 |
| 长距离 | r → ∞ | g(r) → 1，液体无长程序 |

固体 vs 液体的 RDF 区别：

```
固体:                           液体:
g(r)                            g(r)
  |                               |
  |  |   |   |   |               |   *     *
  |  |   |   |   |               |  * *   * *
  |  |   |   |   |               | *   * *   *
1 |--|---|---|---|---           1 |*-----*------*---
  |  |   |   |   |               |
  |  |   |   |   |               |
  0  1   2   3   4               0  1   2   3   4
  尖锐峰 = 长程序               宽峰衰减 = 短程序
  (布拉格峰)
```

- **固体**：有尖锐的峰，峰位置对应晶格间距，长距离仍有峰存在（长程序）
- **液体**：只有几个宽的峰，随距离增大很快衰减到 1（只有短程序）
- **气体**：g(r) ≈ 1，几乎没有结构（除了非常近的距离有排斥核效应）

#### 如何从 MD 计算 RDF

MD 中计算 RDF 使用**分箱法 (binning)**：

1. 将 r 从 0 到 r_max 分成 N 个薄壳层（bin），每个宽度 Δr
2. 对每一帧：
   - 遍历所有原子对 (i, j)
   - 计算距离 r_ij
   - 将该对计入对应的 bin 中
3. 对所有帧取平均
4. 用理想气体的期望值归一化：对每个 bin，理想气体中该壳层内的原子数为 ρ × 4πr²Δr

LAMMPS 中的命令：

```
compute rdf all rdf 100 1 1
#                     │  │ │
#                     │  │ └─ 第二个原子类型
#                     │  └─── 第一个原子类型
#                     └────── bin 数量 (100)
```

配合 `fix ave/time` 进行时间平均：

```
fix 3 all ave/time 100 10 1000 c_rdf[*] file rdf.dat mode vector
#           │     │   │    │
#           │     │   │    └─ 每 1000 步输出一次
#           │     │   └────── 每次取 10 个快照平均
#           │     └────────── 每 100 步采样一次
#           └──────────────── 输出文件
```

#### 与结构因子的关系

RDF 和结构因子 S(q) 通过傅里叶变换相关联：

```
S(q) = 1 + ρ ∫ [g(r) - 1] × sin(qr)/(qr) × 4πr² dr
```

实验上通过 X 射线衍射或中子散射测量 S(q)，再反变换得到 g(r)。MD 模拟可以直接计算 g(r)，然后预测实验可观测的衍射图样。

---

### 均方位移 (MSD)

#### 定义

均方位移（Mean Square Displacement, MSD）描述了粒子随时间扩散的平均距离：

```
MSD(t) = <|r(t) - r(0)|²>
       = (1/N) × Σᵢ |rᵢ(t) - rᵢ(0)|²
```

其中 rᵢ(t) 是第 i 个原子在时刻 t 的位置，<...> 表示系综平均（对所有原子和多个时间原点取平均）。

#### 物理意义

MSD 告诉我们：**原子从初始位置平均移动了多远的平方**。它是衡量扩散最直接的物理量。

#### 短时间 vs 长时间行为

MSD 的行为取决于观测的时间尺度：

**短时间 — 弹道运动（ballistic regime）**：

在极短的时间内（t < 几个碰撞时间），原子自由飞行，还没来得及与其他原子碰撞：

```
MSD(t) ∝ t²    (弹道运动)
```

此时原子做匀速直线运动，位移正比于时间，所以 MSD 正比于 t²。

**长时间 — 扩散运动（diffusive regime）**：

经过足够多次碰撞后，原子的运动变成随机行走：

```
MSD(t) ∝ t    (扩散运动)
```

此时 MSD 与时间成线性关系，斜率与扩散系数 D 成正比。

**MSD 的 log-log 图**：

```
log(MSD)
    |                              /
    |                            /   ← 斜率 = 1 (扩散区)
    |                          /
    |                        /
    |                     /
    |                  /
    |              ./
    |           ./   ← 斜率 = 2 (弹道区)
    |        ./
    |     ./
    |   ./
    |  /
    |/
    +-------------------------------- log(t)
         ↑
     过渡区(笼效应)
```

在液体中，弹道区和扩散区之间还有一个**亚扩散区 (sub-diffusive)**，这对应于"笼效应"——原子被困在邻居构成的笼子里短暂振荡。

#### 如何从 MSD 计算扩散系数

**爱因斯坦关系 (Einstein relation)**：

对于 d 维体系：

```
MSD(t) = 2dDt    (t → ∞)
```

因此：

| 维度 | 公式 |
|------|------|
| 3D | D = lim(t→∞) MSD(t) / (6t) |
| 2D | D = lim(t→∞) MSD(t) / (4t) |
| 1D | D = lim(t→∞) MSD(t) / (2t) |

**实际操作**：
1. 绘制 MSD vs t 曲线
2. 在扩散区（长时间、线性区）做线性拟合
3. 斜率 k = 6D（3D），因此 D = k / 6

```
MSD
  |              /  ← 线性拟合区域
  |            /
  |          /  ← 斜率 = 6D
  |        /
  |      /
  |    /
  |  ./ ← 早期非线性（弹道区）
  |./
  +------------------------ t
```

#### LAMMPS 中的 MSD 计算

```
compute msd all msd
# 输出 4 个值：
# c_msd[1] = x 方向的 MSD
# c_msd[2] = y 方向的 MSD
# c_msd[3] = z 方向的 MSD
# c_msd[4] = 总 MSD = [1] + [2] + [3]
```

**重要提示**：`compute msd` 从它被定义的那一刻起追踪位移。如果之前跑了平衡，MSD 会从平衡结束时的位置开始计算，这正是我们想要的。

---

### 扩散系数

#### Fick 定律

扩散的宏观描述由 **Fick 第一定律** 给出：

```
J = -D ∇c
```

- **J**：扩散通量（单位时间通过单位面积的物质质量）
- **D**：扩散系数（m²/s）
- **∇c**：浓度梯度

物理含义：物质从高浓度区域向低浓度区域流动，流速正比于浓度梯度。

Fick 第二定律描述浓度随时间的演化：

```
∂c/∂t = D ∇²c
```

这就是扩散方程，是一个抛物型偏微分方程。

#### 扩散系数的物理意义

扩散系数 D 衡量原子或分子在介质中迁移的快慢：

- **D 越大**：原子迁移越快，扩散越迅速
- **D 越小**：原子迁移越慢

#### 典型值

| 体系 | D (m²/s) | 说明 |
|------|----------|------|
| 气体 (N₂ 在空气中) | ~10⁻⁵ | 分子间距大，自由程长 |
| 液体 (水中分子) | ~10⁻⁹ | 有分子间作用力阻碍 |
| 液态金属 | ~10⁻⁸ - 10⁻⁹ | 金属键相对较弱 |
| 固体中的间隙扩散 | ~10⁻¹² - 10⁻¹⁵ | 受晶格约束，需要热激活 |
| 固体中的空位扩散 | ~10⁻¹⁵ - 10⁻²⁰ | 需要空位存在 |

#### 温度依赖性 — Arrhenius 关系

扩散系数强烈依赖于温度，通常遵循 **Arrhenius 关系**：

```
D = D₀ × exp(-Ea / kT)
```

- **D₀**：前指数因子（指前因子）
- **Ea**：扩散激活能
- **k**：玻尔兹曼常数
- **T**：绝对温度

对两边取对数：

```
ln(D) = ln(D₀) - Ea/(kT)
```

以 ln(D) vs 1/T 作图（**Arrhenius 图**），斜率为 -Ea/k，截距为 ln(D₀)：

```
ln(D)
  |  \
  |   \
  |    \
  |     \   ← 斜率 = -Ea/k
  |      \
  |       \
  |        \
  +------------- 1/T
```

- **液体**：Ea 较小（通常 0.1-0.5 eV），D 对温度不太敏感
- **固体**：Ea 较大（通常 0.5-3 eV），D 对温度非常敏感

#### Stokes-Einstein 关系

对于溶质在溶剂中的扩散，有 **Stokes-Einstein 关系**：

```
D = kT / (6πηr)
```

- **k**：玻尔兹曼常数
- **T**：温度
- **η**：溶剂粘度
- **r**：溶质粒子半径

这个关系将微观的扩散系数与宏观的粘度联系起来。它告诉我们：
- 温度越高，扩散越快
- 溶剂粘度越大，扩散越慢
- 粒子越大，扩散越慢

**注意**：Stokes-Einstein 关系在玻璃转变附近会失效，扩散系数和粘度脱耦。

---

### Green-Kubo 方法

#### 原理

除了 MSD 方法，还可以通过**速度自相关函数 (VACF)** 来计算扩散系数，这就是 **Green-Kubo 方法**。

速度自相关函数定义为：

```
C(t) = <v(0) · v(t)>
     = (1/N) × Σᵢ vᵢ(0) · vᵢ(t)
```

它描述了粒子在时刻 t 的速度与初始速度的关联程度。t=0 时 C(0) = <v²> = 3kT/m（均分定理），随着时间增大，C(t) 逐渐衰减到 0。

扩散系数通过对 VACF 积分得到：

```
D = (1/3) × ∫₀^∞ <v(0) · v(t)> dt
```

这就是 Green-Kubo 关系。

#### 物理理解

- VACF 衰减得越快 → 粒子"忘记"初始速度越快 → 扩散越快 → D 越大
- VACF 衰减得越慢 → 粒子长时间记住初始方向 → D 越小
- 固体中 VACF 可能振荡（声子效应），积分可能很复杂

#### LAMMPS 中的 VACF 计算

```
compute vacf all vacf
fix 4 all ave/time 1 1 100 c_vacf[*] file vacf.dat
# c_vacf[1] = vx(0)*vx(t)
# c_vacf[2] = vy(0)*vy(t)
# c_vacf[3] = vz(0)*vz(t)
# c_vacf[4] = v(0)·v(t) = [1]+[2]+[3]
```

对 vacf.dat 中的 VACF 曲线做数值积分，再除以 3，就得到 D。

#### MSD 方法 vs Green-Kubo 方法对比

| 特性 | MSD 方法 | Green-Kubo 方法 |
|------|----------|-----------------|
| 计算量 | 较小 | 较大 |
| 收敛性 | 慢（需要长轨迹） | 快（积分收敛） |
| 统计误差 | 较大（长时间尾部噪声大） | 较小 |
| 适用体系 | 各类体系 | 各类体系 |
| 直观性 | 非常直观 | 需要理解积分 |
| 困难 | 需要正确识别线性区 | VACF 振荡时积分困难 |
| 推荐场景 | 初学者，初步估计 | 高精度计算 |

**经验法则**：两种方法都做，互相验证。如果结果一致，可信度更高。

---

### 计算技巧

#### 去除质心运动

长时间模拟中，体系的质心可能缓慢漂移。这会影响 MSD 的计算。可以在生产运行开始前重置速度：

```
velocity all zero linear    # 去除线性动量
velocity all zero angular   # 去除角动量
```

#### 足够长的生产运行

- MSD 计算需要足够长的运行时间，确保进入扩散区（线性区）
- 经验法则：生产运行时间至少是扩散时间 τ_D 的几倍
- τ_D ≈ σ²/D，其中 σ 是原子直径
- 如果 MSD-t 曲线还看不到线性区，需要延长运行

#### 统计平均和误差估计

- 多次独立运行取平均，减少统计误差
- 使用不同的随机种子（`velocity create` 的 seed 参数）
- 计算标准误差：SE = σ/√N，其中 N 是独立运行次数
- 也可以在一个长轨迹中分段计算 D，看其波动

#### 周期性边界的影响

- 周期性边界条件下，原子穿越盒子边界时 LAMMPS 会更新 unwrap 坐标
- `compute msd` 自动使用 unwrap 坐标，无需额外设置
- 但如果使用 `dump` 输出的 wrapped 坐标来手动计算 MSD，需要注意"解包"处理

#### 其他注意事项

- RDF 计算不需要 unwrap 坐标（只关心瞬时距离）
- MSD 计算前最好重置 compute（重新定义 compute 即可）
- 在 NVT 中计算扩散系数时，恒温器会略微影响速度自相关，可能导致 D 偏低
- **最佳实践**：NVT 平衡 → 切换到 NVE → 计算 MSD

---

## 输入脚本逐行解析

### in.diffusion — 扩散系数计算

```
# ---- 基本设置 ----
units           lj                    # 使用 LJ 约化单位
dimension       3                     # 三维体系
boundary        p p p                 # 三个方向都使用周期性边界条件
atom_style      atomic                # 原子类型（无电荷、无键）
```

```
# ---- 创建模拟盒子 ----
lattice         fcc 0.8442            # FCC 晶格，数密度 0.8442
                                        # (LJ 液体三相点附近密度)
region          simbox block 0 5 0 5 0 5  # 定义 5×5×5 个晶胞的盒子
create_box      1 simbox              # 创建盒子，容纳 1 种原子
create_atoms    1 box                 # 在盒子中填满原子
```

使用 FCC 晶格是因为它是密排结构，将晶格常数对应到特定密度即可获得均匀的液体初始构型。

```
# ---- 势函数 ----
pair_style      lj/cut 2.5            # LJ 势，截断半径 2.5σ
pair_coeff      1 1 1.0 1.0 2.5       # ε=1.0, σ=1.0, rc=2.5
pair_modify     shift yes              # 势能在截断处平移到零
```

`shift yes` 确保势能在截断处连续地变为零，避免能量跳变。

```
# ---- 质量和初始速度 ----
mass            1 1.0                  # 原子质量 = 1.0 (LJ 单位)
velocity        all create 1.0 12345 dist gaussian
#                              │    │
#                              │    └── 随机种子
#                              └─────── 目标温度 T*=1.0
```

```
# ---- NVT 平衡 ----
fix             1 all nvt temp 1.0 1.0 0.5
#                                  │   │   │
#                                  │   │   └── 阻尼参数 (时间常数)
#                                  │   └────── 最终温度
#                                  └────────── 起始温度
run             5000               # 平衡 5000 步
unfix           1                   # 取消恒温器
```

使用 Nosé-Hoover 恒温器将体系平衡到 T*=1.0。平衡完成后取消 fix，为下一步做准备。

```
# ---- 生产运行 (NVE) ----
fix             1 all nve            # NVE 系综: 粒子数、体积、能量守恒
```

切换到 NVE 系综有两个好处：(1) 避免恒温器干扰原子速度，得到更准确的扩散系数；(2) 物理上更合理——孤立体系中粒子做自由扩散。

```
compute         msd all msd          # 定义 MSD 计算
# 输出: c_msd[1]=Δx², c_msd[2]=Δy², c_msd[3]=Δz², c_msd[4]=Δr²
```

`compute msd` 从此时开始追踪每个原子相对于当前位置的位移平方。

```
fix             2 all ave/time 100 1 100 c_msd[4] file msd.dat
#                  │     │   │    │
#                  │     │   │    └── 每 100 步输出一行
#                  │     │   └────── 每次输出取 1 个采样
#                  │     └────────── 每 100 步采样一次
#                  └──────────────── 输出 c_msd[4] (总 MSD) 到文件
```

```
dump            1 all custom 1000 dump.lammpstrj id type x y z vx vy vz
#                                        │
#                                        └── 每 1000 步输出一帧轨迹
dump_modify     1 sort id               # 按原子 ID 排序输出
```

```
run             50000                  # 生产运行 50000 步
```

### in.rdf — 径向分布函数计算

脚本结构与 `in.diffusion` 类似，主要区别在于：

```
compute         rdf all rdf 100 1 1     # RDF 计算
#                          │  │ │
#                          │  │ └─ 第二种原子类型
#                          │  └─── 第一种原子类型
#                          └────── 100 个径向 bin
```

```
fix             3 all ave/time 100 10 1000 c_rdf[*] file rdf.dat mode vector
#                  │     │   │    │     │
#                  │     │   │    │     └── 输出所有 RDF 列
#                  │     │   │    └────── 每 1000 步输出
#                  │     │   └────────── 每次取 10 个快照平均
#                  │     └────────────── 每 100 步采样
#                  └──────────────────── mode vector: 多列向量模式输出
```

`mode vector` 告诉 `fix ave/time` 输出多列数据（bin编号、r、g(r)等），而不是单个标量。

---

## 运行指南

### 运行扩散计算

```bash
lmp -in in.diffusion
```

运行完成后，当前目录会生成：
- `msd.dat` — MSD 随时间变化的数据
- `dump.lammpstrj` — 轨迹文件（可用 OVITO 可视化）

### 运行 RDF 计算

```bash
lmp -in in.rdf
```

运行完成后生成：
- `rdf.dat` — RDF 数据
- `dump.rdf.lammpstrj` — 轨迹文件

### 用 Python 分析 MSD 数据

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# 读取 MSD 数据
data = np.loadtxt('msd.dat', skiprows=2)  # 跳过 LAMMPS 注释行
t = data[:, 0]      # 时间步 (或时间，取决于输出设置)
msd = data[:, 1]    # 总 MSD

# 确定线性拟合区间 (取后半段)
n = len(t)
start = n // 3      # 从 1/3 处开始拟合
slope, intercept, r_value, p_value, std_err = linregress(t[start:], msd[start:])

# 计算扩散系数 (3D: D = slope / 6)
D = slope / 6.0
print(f"扩散系数 D* = {D:.6f} (LJ 单位)")

# 绘图
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# MSD vs t
ax1.plot(t, msd, 'b-', label='MSD')
ax1.plot(t, slope * t + intercept, 'r--', label=f'线性拟合 (D={D:.4f})')
ax1.set_xlabel('时间步')
ax1.set_ylabel('MSD (σ²)')
ax1.set_title('均方位移')
ax1.legend()
ax1.grid(True)

# log-log 图区分弹道和扩散区
ax2.loglog(t[1:], msd[1:], 'b-')
ax2.set_xlabel('log(时间步)')
ax2.set_ylabel('log(MSD)')
ax2.set_title('MSD log-log 图')
ax2.grid(True)
ax2.axhline(y=1, color='gray', linestyle=':')

plt.tight_layout()
plt.savefig('msd_analysis.png', dpi=150)
plt.show()
```

### 用 Python 分析 RDF 数据

```python
import numpy as np
import matplotlib.pyplot as plt

# 读取 RDF 数据
# rdf.dat 格式: 第1列=bin编号, 第2列=r距离, 第3列=g(r)
data = np.loadtxt('rdf.dat', skiprows=4)
r = data[:, 1]
g_r = data[:, 2]

# 绘图
plt.figure(figsize=(8, 5))
plt.plot(r, g_r, 'b-', linewidth=2)
plt.axhline(y=1, color='gray', linestyle='--', label='g(r) = 1 (理想气体)')
plt.xlabel('r / σ')
plt.ylabel('g(r)')
plt.title('径向分布函数 — LJ 液体 (T*=1.0, ρ*=0.8442)')
plt.legend()
plt.grid(True)
plt.xlim(0, 4)
plt.savefig('rdf_plot.png', dpi=150)
plt.show()

# 计算配位数: 对第一峰积分
# N_coord = ρ × ∫₀^r_min g(r) × 4πr² dr
r_min_idx = np.argmin(g_r[r < 2.0])  # 第一峰后的第一个极小值
rho = 0.8442
r_int = r[:r_min_idx+1]
g_int = g_r[:r_min_idx+1]
N_coord = rho * np.trapz(g_int * 4 * np.pi * r_int**2, r_int)
print(f"第一配位数 ≈ {N_coord:.1f}")
```

---

## 预期输出

### MSD 曲线特征

对于 LJ 液体在 T*=1.0, ρ*=0.8442 条件下：

```
MSD (σ²)
  |
  |                                    /
  |                                  /
  |                                /   ← 线性区 (扩散运动)
  |                              /
  |                           /
  |                        /
  |                     /
  |                  /
  |              .. /  ← 曲线过渡 (笼效应 → 扩散)
  |           ..
  |        ..   ← 上凹区 (弹道运动 → 笼效应)
  |     ..
  | ..
  +-------------------------------- t (时间步)
  0    10000   20000   30000   40000   50000
```

- **早期（t < ~500 步）**：MSD ∝ t²，弹道运动
- **过渡区（~500 - ~2000 步）**：亚扩散，笼效应
- **扩散区（t > ~2000 步）**：MSD ∝ t，线性增长

### 扩散系数预期值

在 LJ 液体的三相点附近（T*=1.0, ρ*=0.8442），文献报道的扩散系数约为：

```
D* ≈ 0.03 - 0.05 (LJ 约化单位)
```

具体数值取决于运行长度、平衡质量等因素。

### RDF 曲线特征

```
g(r)
  |
2.5|
   |
2.0|   *
   |  * *
1.5| *   *
   |*     *
1.0|*------*----*--*--*----------  ← g(r) → 1
0.5|
   |
0.0|___*___*____*__*__*__________ r/σ
   0  0.5  1  1.5  2  2.5  3  3.5  4
```

预期特征：
- **r < 0.95σ**：g(r) ≈ 0（硬核排斥）
- **第一峰**：r ≈ 1.09σ，g(r) ≈ 2.5-3.0
- **第一谷**：r ≈ 1.5σ，g(r) ≈ 0.6-0.7
- **第二峰**：r ≈ 2.0σ，g(r) ≈ 1.2-1.3
- **r > 3σ**：g(r) → 1，基本无结构

通过第一峰积分可得配位数约 10-12（FCC 的配位数为 12，液态略有减少）。

---

## 练习题

### 练习 1：计算不同温度下的扩散系数，绘制 Arrhenius 图

在 5 个不同温度下（T* = 0.7, 0.8, 1.0, 1.2, 1.5）分别运行扩散计算：
- 修改 `velocity create` 和 `fix nvt` 中的温度参数
- 对每个温度提取扩散系数 D
- 绘制 ln(D) vs 1/T 的 Arrhenius 图
- 从斜率提取扩散激活能 Ea
- 思考：Arrhenius 图是否完美线性？什么情况下会偏离？

### 练习 2：对比固相和液相的 RDF 差异

分别在液态（T*=1.0, ρ*=0.8442）和固态（T*=0.5, ρ*=1.0）条件下计算 RDF：
- 观察峰的位置、宽度和数量
- 固态 RDF 的峰为什么更尖锐？
- 如何用 RDF 判断体系是固体还是液体？
- 尝试绘制两者在同一张图上进行对比

### 练习 3：使用 Green-Kubo 方法计算扩散系数

在 `in.diffusion` 的生产运行部分添加 VACF 计算：

```
compute vacf all vacf
fix 4 all ave/time 1 1 100 c_vacf[*] file vacf.dat
```

- 运行后读取 vacf.dat
- 绘制 VACF vs t 曲线，观察衰减行为
- 对 VACF 做数值积分：D = (1/3) × ∫₀^∞ C(t) dt
- 与 MSD 方法得到的 D 进行对比
- 思考：两种方法的结果是否一致？哪个更准确？

### 练习 4：计算不同密度下的扩散系数

固定温度 T*=1.0，改变密度（ρ* = 0.6, 0.7, 0.8442, 0.9, 1.0）：
- 计算每个密度下的扩散系数
- 绘制 D vs ρ* 曲线
- 密度增大时 D 如何变化？为什么？
- 思考：密度达到什么程度时体系可能不再是液体？

### 练习 5：分析 VACF（速度自相关函数）

```
compute vacf all vacf
fix 4 all ave/time 1 1 1 c_vacf[*] file vacf.dat
run 10000
```

- 绘制 VACF 的 4 个分量 vs t
- VACF 从什么值开始？为什么？（提示：均分定理）
- VACF 如何衰减？衰减时间尺度是多少？
- VACF 的衰减时间与扩散系数有什么关系？
- （进阶）在固态中运行，观察 VACF 是否出现振荡？振荡的物理含义是什么？

---

## 参考资料

- LAMMPS compute msd 文档：https://docs.lammps.org/stable/compute_msd.html
- LAMMPS compute rdf 文档：https://docs.lammps.org/stable/compute_rdf.html
- LAMMPS compute vacf 文档：https://docs.lammps.org/stable/compute_vacf.html
- LAMMPS fix ave/time 文档：https://docs.lammps.org/stable/fix_ave_time.html
- Allen & Tildesley, *Computer Simulation of Liquids*, 第2版 (经典教材)
- Frenkel & Smit, *Understanding Molecular Simulation*, 第2版
- 维基百科 - 径向分布函数：https://en.wikipedia.org/wiki/Radial_distribution_function
- 维基百科 - 扩散方程：https://en.wikipedia.org/wiki/Diffusion_equation
