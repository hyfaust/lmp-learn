# 项目 08：晶体缺陷与力学性质

## 学习目标

1. **理解晶体缺陷的分类**：掌握点缺陷（空位、间隙原子、替代原子）、线缺陷（位错）和面缺陷（晶界、表面、层错）的物理本质及其对材料性质的影响
2. **掌握空位形成能的计算方法**：学会使用 LAMMPS 删除原子创建缺陷，并通过能量差计算空位形成能
3. **理解应力与应变的微观本质**：了解维里应力（Virial stress）的物理意义，掌握 `compute stress/atom` 的使用方法
4. **模拟单轴拉伸测试**：学会使用 `fix deform` 施加应变，输出应力-应变曲线，分析弹性模量和屈服强度
5. **运用共邻分析（CNA）识别晶体结构**：学会使用 `compute cna/atom` 识别 FCC、HCP、BCC 等结构，用于可视化缺陷

---

## 背景知识

### 晶体缺陷分类

在真实晶体中，原子排列并非完美无缺。各种类型的缺陷对材料的力学、电学、热学性质有决定性影响。下面我们按维度分类介绍。

#### 点缺陷

点缺陷是最简单的晶体缺陷，只涉及一个或几个原子位置的偏差。

**空位 (Vacancy)**
空位是指晶格格点上缺少一个原子。空位是热力学平衡缺陷——在任何有限温度下，晶体中都存在一定浓度的空位，因为空位的引入虽然增加了内能（形成能），但也增加了构型熵，降低了自由能。

```
完美晶格:              含空位晶格:
● ● ● ●               ● ● ● ●
● ● ● ●               ● ○ ● ●    ← ○ 表示空位
● ● ● ●               ● ● ● ●
● ● ● ●               ● ● ● ●
```

空位浓度随温度呈指数增长：
```
n_v = N * exp(-E_f / k_B T)
```
其中 `E_f` 是空位形成能，`k_B` 是玻尔兹曼常数，`T` 是温度。

**间隙原子 (Interstitial)**
间隙原子是指额外的原子挤入晶格的间隙位置。在 FCC 晶体中，典型的间隙位置有：
- **八面体间隙**：位于立方体面心和棱中心
- **四面体间隙**：位于由四个原子围成的四面体中心

间隙原子的形成能通常比空位高很多（约 2-4 倍），因此在热平衡状态下浓度较低。

```
● ● ● ●               ● ● ● ●
● ● ● ●               ● ●● ● ●    ← ● 额外挤入的原子
● ● ● ●               ● ● ● ●
● ● ● ●               ● ● ● ●
```

**替代原子 (Substitution)**
杂质原子替代了基体原子占据晶格位置。这是合金的基本组成方式。

```
纯金属:                 含替代原子:
● ● ● ●               ● ● ● ●
● ● ● ●               ● ◆ ● ●    ← ◆ 杂质原子
● ● ● ●               ● ● ● ●
● ● ● ●               ● ● ● ●
```

**点缺陷对性质的影响**：
- **扩散**：空位机制是固体中原子扩散的主要途径，原子跳入邻近空位实现迁移
- **力学强度**：点缺陷阻碍位错运动（固溶强化），提高材料强度
- **电阻**：点缺陷散射传导电子，增加电阻率

#### 线缺陷（位错）

位错是晶体中的一维线状缺陷，是塑性变形的基本载体。

**刃型位错 (Edge Dislocation)**
想象在晶体中插入了半个额外的原子面。位错线垂直于滑移方向。可以用柏氏矢量 (Burgers vector) **b** 来描述位错的特征。

```
刃型位错示意图 (截面):
● ● ● ● ● ● ● ●
● ● ● ● ● ● ● ●
● ● ● ● ● ● ● ●
● ● ● ▲ ● ● ● ●   ← 位错线 (半原子面的边缘)
● ● ● │ ● ● ● ●
● ● ● ● ● ● ● ●
```

**螺型位错 (Screw Dislocation)**
原子面围绕位错线呈螺旋状排列，柏氏矢量平行于位错线。

**位错运动与塑性变形**：
- 位错在切应力作用下滑移（glide），造成宏观塑性变形
- 位错密度越高，材料塑性越好（但强度变化复杂）
- 位错与位错、位错与其他缺陷的相互作用决定了材料的加工硬化行为

#### 面缺陷

**晶界 (Grain Boundary)**
多晶材料中不同取向晶粒之间的界面。晶界阻碍位错运动（Hall-Petch 关系），细化晶粒可提高材料强度。

**表面 (Surface)**
晶体外表面是原子排列突然中断形成的面缺陷。表面原子配位数不足，具有较高的能量（表面能）。

**层错 (Stacking Fault)**
FCC 晶体中原子层的堆垛顺序偏离正常的 ABCABC... 序列。例如 ABAB... 序列就是 HCP 结构的堆垛方式。层错能是材料的重要参数，影响位错扩展和变形机制。

---

### 应力与应变

#### 应变 (Strain)

应变描述材料的变形程度，是一个无量纲量。

**工程应变 (Engineering Strain)**：
```
ε_eng = ΔL / L₀ = (L - L₀) / L₀
```
- `L₀` = 原始长度
- `L` = 变形后的长度
- 优点：简单直观
- 缺点：大变形时不准确（未考虑长度的连续变化）

**真应变 (True Strain)**：
```
ε_true = ln(L / L₀)
```
- 考虑了变形过程中参考长度的连续变化
- 小变形时与工程应变近似相等
- 大变形时真应变更准确

**在 MD 中施加应变**：
- 使用 `fix deform` 命令改变模拟盒子的尺寸
- 可以用恒定应变速率 (`erate`) 或每步固定变形量 (`delta`)
- 原子坐标可以用 `remap x` 选项随盒子一起移动

```
# 例：z 方向以 0.001/tau 的应变速率拉伸
fix  deform all deform 1 z erate 0.001 remap x units box
```

#### 应力 (Stress)

应力描述材料内部单位面积上的力，单位为 Pa（帕斯卡）。

**应力张量**：
应力是二阶张量，有 9 个分量（对称后 6 个独立分量）：

```
σ = | σ_xx  σ_xy  σ_xz |
    | σ_yx  σ_yy  σ_yz |
    | σ_zx  σ_zy  σ_zz |
```

- **正应力 (Normal stress)**：σ_xx, σ_yy, σ_zz —— 垂直于面的力分量
- **剪应力 (Shear stress)**：σ_xy, σ_xz, σ_yz —— 平行于面的力分量
- 由于角动量守恒，σ_xy = σ_yx 等，独立分量为 6 个

**维里应力 (Virial Stress)**：
在分子动力学中，宏观应力通过维里定理（Virial theorem）从原子尺度计算：

```
σ_αβ = 1/V * [ Σ_i m_i * v_iα * v_iβ + Σ_i Σ_{j>i} r_ijα * f_ijβ ]
```

- 第一项：动能贡献（速度的关联）
- 第二项：维里项（力与距离的乘积）
- `V` = 体积
- `α, β` = 方向分量 (x, y, z)
- `r_ijα` = 原子 i 和 j 之间的距离在 α 方向的分量
- `f_ijβ` = 原子 j 对原子 i 的力在 β 方向的分量

**`compute stress/atom` 命令**：
```lammps
compute  stress all stress/atom NULL
```
- 输出每个原子的 6 个应力分量：xx, yy, zz, xy, xz, yz
- 参数 `NULL` 表示不计入 bond、angle 等贡献（此处只有 pair 势）
- 输出的单位是 `压力 × 体积`（不是纯压力）
- 要得到宏观应力，需对所有原子求和后除以体积

**体应力 vs 原子应力**：
- **体应力 (Bulk stress)**：对所有原子的应力求平均，得到宏观应力
- **原子应力 (Atomic stress)**：每个原子的局部应力，可用于分析应力集中
- 使用 `compute reduce` 将原子应力聚合成体应力

---

### 弹性常数

#### 胡克定律

在弹性范围内，应力与应变成线性关系（广义胡克定律）：

```
σ_i = C_ij * ε_j    (i, j = 1, 2, ..., 6)
```

其中使用 **Voigt 记法** 将 6 个独立分量编号：
```
1 → xx,  2 → yy,  3 → zz,  4 → yz,  5 → xz,  6 → xy
```

**弹性常数矩阵**：
```
C = | C11  C12  C13  C14  C15  C16 |
    | C12  C22  C23  C24  C25  C26 |
    | C13  C23  C33  C34  C35  C36 |
    | C14  C24  C34  C44  C45  C46 |
    | C15  C25  C35  C45  C55  C56 |
    | C16  C26  C36  C46  C56  C66 |
```

#### FCC 晶体的独立弹性常数

FCC 晶体具有立方对称性，只需 **3 个独立弹性常数**：

| 弹性常数 | 物理意义 |
|---------|---------|
| **C11** | 沿晶轴方向的单轴刚度 |
| **C12** | 横向耦合（泊松效应）|
| **C44** | 剪切刚度 |

FCC 的弹性常数矩阵简化为：
```
C = | C11  C12  C12   0    0    0  |
    | C12  C11  C12   0    0    0  |
    | C12  C12  C11   0    0    0  |
    |  0    0    0   C44   0    0  |
    |  0    0    0    0   C44   0  |
    |  0    0    0    0    0   C44 |
```

#### 宏观弹性模量

从弹性常数可以推导出常用的宏观模量：

**杨氏模量 (Young's modulus)**：
```
E = (C11 + 2*C12)(C11 - C12) / (C11 + C12)    (Voigt 平均近似)
```
或简单地从应力-应变曲线初始斜率获得：`E ≈ σ / ε`（线性区）

**泊松比 (Poisson's ratio)**：
```
ν = C12 / (C11 + C12)    (各向同性近似)
```
描述横向收缩与纵向伸长之比。

**体积模量 (Bulk modulus)**：
```
K = (C11 + 2*C12) / 3
```
描述材料抵抗均匀压缩的能力。

**剪切模量 (Shear modulus)**：
```
G = C44    (各向同性近似 G ≈ (C11 - C12)/2 或 C44)
```

---

### 共邻分析 (CNA)

**什么是 CNA？**

共邻分析（Common Neighbor Analysis）是一种基于拓扑的局部结构识别方法。它分析每对近邻原子周围的共同邻居的连接拓扑，从而判断该区域属于哪种晶体结构。

**基本原理**：
1. 对每个原子，找出所有近邻原子（在截断半径内）
2. 对每对近邻原子 (i, j)，找出它们的共同邻居
3. 分析共同邻居之间的键连方式（链长、键数）
4. 根据特征签名 (signature) 判断结构类型

**CNA 识别的结构类型**：

| CNA 值 | 结构类型 | 特征 |
|--------|---------|------|
| 1 | FCC (面心立方) | 堆垛序 ABCABC... |
| 2 | HCP (密排六方) | 堆垛序 ABAB... |
| 3 | BCC (体心立方) | 配位数 8 |
| 4 | ICOS (二十面体) | 非晶/准晶结构 |
| 5 | 未知/无序 | 缺陷区域、表面 |

**`compute cna/atom` 命令**：
```lammps
compute  cna all cna/atom 1.5
```
- 参数 `1.5` 是邻居截断半径（sigma 单位）
- 对于 FCC LJ 系统，最近邻距离约为 `sqrt(2)/2 * a ≈ 1.094`
- 截断半径应略大于最近邻距离

**CNA 的可视化应用**：
- 用 OVITO 或 VMD 打开轨迹文件
- 按 CNA 值着色：FCC = 绿色，HCP = 红色，无序 = 白色
- 空位周围会出现无序原子环
- 位错核心显示为无序区域
- 层错显示为 HCP 区域

---

### 空位形成能

**定义**：
空位形成能 (E_vac) 是在完美晶体中移走一个原子并将其放到晶体表面（或无穷远处）所需的能量。

**计算公式**：
```
E_vac = E(N-1) - (N-1)/N × E(N)
```

- `E(N)` = 完美晶体（N 个原子）的总势能
- `E(N-1)` = 含一个空位的晶体（N-1 个原子）的总势能
- `(N-1)/N × E(N)` = N-1 个原子在完美晶体中的参考能量
- 这个公式假设移走的原子放到晶体表面（参考态）

**典型值**：

| 金属 | E_vac (eV) | 实验值 (eV) |
|------|-----------|------------|
| Al   | ~0.68     | 0.67       |
| Cu   | ~1.28     | 1.30       |
| Au   | ~0.90     | 0.94       |
| Fe   | ~1.60     | 1.60       |

**LJ 约化单位下**：
对于 LJ 系统（fcc 结构），空位形成能约为 `1.0 ~ 1.5 ε`（epsilon 单位）。

**影响因素**：
- 温度升高会略微降低形成能（热膨胀效应）
- 晶体结构不同，形成能不同
- 表面附近的空位形成能低于体相
- 空位形成能决定了平衡空位浓度

---

## 输入脚本逐行解析

### in.vacancy（空位缺陷模拟）

```
# 第 1 步：初始化
clear                        # 清除所有之前的设置
units    lj                  # 使用 LJ 约化单位
atom_style   atomic          # 原子类型样式
boundary     p p p           # 三维周期性边界
```
> `clear` 确保脚本可重复运行。`units lj` 意味着长度单位为 σ，能量单位为 ε。

```
# 第 2 步：创建完美 FCC 晶体
lattice   fcc 1.5476         # FCC 晶格，常数 1.5476σ
region    box block 0 6 0 6 0 6 units box   # 定义长方体区域
create_box   1 box           # 创建盒子 (1 种原子类型)
create_atoms 1 box           # 在晶格格点放置原子
```
> `lattice fcc 1.5476` 中 1.5476 是 LJ FCC 在 T=0 时的平衡晶格常数（由势能最小化得到）。`0 6` 表示每个方向 6 个晶格常数长度，产生约 3456 个原子（6×6×6×4）。

```
# 第 3 步：设置力场
pair_style   lj/cut 2.5      # LJ 势，截断半径 2.5σ
pair_coeff   1 1 1.0 1.0      # ε=1.0, σ=1.0
mass         1 1.0             # 质量 = 1
```
> 标准 LJ 参数。截断半径 2.5σ 是学术界通用的约定，平衡了精度和效率。

```
# 第 4 步：能量最小化
minimize  1.0e-4 1.0e-6 1000 10000
```
> 4 个参数分别是：力收敛标准、能量收敛标准、最大步数、最大评估次数。最小化使晶格达到力学平衡。

```
# 第 5 步：获取完美晶体能量
run  0                       # 只计算热力学量，不做 MD
variable E_perfect equal pe  # 保存总势能
```
> `run 0` 是一个重要技巧：只计算当前构型的热力学量，不推进时间。

```
# 第 6 步：创建空位
region  vacancy_region sphere 4.6428 4.6428 4.6428 0.5 units box
group   vacancy_atoms region vacancy_region
delete_atoms group vacancy_atoms compress yes
```
> 球心坐标 `4.6428 = 3 × 1.5476`，刚好在一个晶格位置上。半径 `0.5` 只包含该位置的原子。`compress yes` 在删除后重新编号原子。

```
# 第 7 步：空位晶体能量最小化
minimize  1.0e-4 1.0e-6 1000 10000
variable  E_defect equal pe
```
> 让空位周围的原子弛豫到新的平衡位置。空位周围原子会略微向空位移动。

```
# 第 8 步：计算空位形成能
variable E_vacancy equal v_E_defect - (v_N_defect/v_N_perfect)*v_E_perfect
variable e_vacancy_form equal v_E_vacancy / v_N_vacancy
```
> 核心公式：`E_vac = E(N-1) - (N-1)/N × E(N)`。除以空位数得到每个空位的形成能。

```
# 第 9 步：CNA 分析
compute  cna_all all cna/atom 1.5
dump     cna_dump all custom 1 dump.vacancy_cna.lammpstrj id type x y z c_cna_all
```
> CNA 值：1=FCC(绿色), 2=HCP(红色), 5=无序(白色)。空位周围会出现无序环。

```
# 第 10 步：NVT 弛豫
fix  nvt_fix all nvt temp 0.5 0.5 0.5
timestep   0.002
run        20000
```
> NVT 系综在 T=0.5（约化单位）下弛豫。低温让缺陷清晰可见。热弛豫时间 0.5 约为 250 个时间步。

---

### in.tensile（拉伸测试模拟）

```
# 第 1 步：初始化
boundary  p p f               # z 方向非周期（固定边界）
```
> z 方向使用固定边界 `f` 是因为拉伸在 z 方向进行，避免周期像的影响。

```
# 第 2 步：创建 slab
region  slab block 0 4 0 4 0 20 units box
```
> z 方向更长（20 vs 4），这是拉伸方向。更长的 slab 有利于观察断裂过程和应力分布。

```
# 第 3 步：NVT 预平衡
fix  nvt_prep all nvt temp 0.1 0.1 0.5
run  10000
unfix  nvt_prep
```
> 在开始拉伸前进行预平衡，消除初始构型的残余应力。T=0.1 很低，近似 0K 拉伸。

```
# 第 4 步：NPT 控压 + 拉伸
fix  npt_fix all npt/aniso temp 0.1 0.1 0.5 &
     x 0.0 0.0 1.0  y 0.0 0.0 1.0  z 0.0 0.0 1.0
fix  deform_fix all deform 1 z erate v_erate remap x units box
```
> 关键设置：`npt/aniso` 允许 x, y 方向自由侧向变形（泊松效应），z 方向压力控制被 `fix deform` 覆盖。`erate 0.001` 是应变速率，`remap x` 让原子随盒子移动。

```
# 第 5 步：应力计算
compute  stress all stress/atom NULL
compute  stress_zz all reduce sum c_stress[3]
variable sig_zz equal -c_stress_zz/(3*v_vol)
```
> `stress/atom NULL` 只计算 pair 势贡献的原子应力。`reduce sum` 求和。除以体积得到宏观应力。负号是因为 LAMMPS 的符号约定（压应力为正）。

```
# 第 6 步：应变计算
variable strain equal (lz - v_Lz0) / v_Lz0
```
> 工程应变 = (当前长度 - 初始长度) / 初始长度。`Lz0` 在拉伸开始前保存。

```
# 第 7 步：应力-应变数据输出
fix output_stress all print 50 "${strain} ${sig_zz} ..." file stress_strain.dat
```
> 每 50 步输出一行应力-应变数据，形成完整曲线。用 gnuplot 或 matplotlib 绘图。

---

## 运行指南

### 运行空位模拟

```bash
cd /home/faust/vibe/lmp_learn/projects/08-crystal-defects

# 运行空位模拟
lmp -in in.vacancy

# 查看输出
cat log.lammps | grep "空位形成能"
```

### 运行拉伸模拟

```bash
# 运行拉伸测试
lmp -in in.tensile

# 绘制应力-应变曲线 (使用 gnuplot)
gnuplot <<EOF
set xlabel "工程应变"
set ylabel "应力 (σ_zz)"
set title "单轴拉伸应力-应变曲线"
plot "stress_strain.dat" using 1:2 with lines linewidth 2 title "σ_zz"
EOF
```

### 使用 OVITO 可视化

1. 打开 OVITO
2. 导入 `dump.vacancy_cna.lammpstrj` 或 `dump.tensile.lammpstrj`
3. 添加 Color Coding modifier，选择 `c_cna_all` 属性
4. 设置颜色映射：
   - 1 (FCC) → 绿色
   - 2 (HCP) → 红色
   - 5 (无序) → 白色/灰色
5. 空位周围会出现白色/灰色环（无序区域）
6. 拉伸断裂区域显示为无序区域

---

## 练习题

### 练习 1：双空位和三空位的形成能

**任务**：修改 `in.vacancy`，分别创建含有 2 个和 3 个空位的晶体，计算总形成能，并与单空位形成能比较。

**提示**：
- 可以删除相邻位置的原子来创建多空位
- 双空位形成能不一定等于单空位形成能的 2 倍（空位之间有相互作用）
- 双空位结合能 = 2×E_vac(单) - E_vac(双)

```lammps
# 删除两个相邻位置的原子
region  vac1 sphere 4.6428 4.6428 4.6428 0.5 units box
region  vac2 sphere 6.1904 4.6428 4.6428 0.5 units box
region  double_vac union 2 vac1 vac2
group   double_vac_atoms region double_vac
delete_atoms group double_vac_atoms compress yes
```

### 练习 2：各向异性拉伸

**任务**：修改 `in.tensile`，分别在 x, y, z 三个方向进行拉伸，比较应力-应变曲线。分析弹性模量是否相同。

**提示**：
- 修改 `boundary` 为 `f p p`（x 方向拉伸时 x 非周期）
- 修改 `fix deform` 为 `x erate ...`
- 计算各方向的杨氏模量 `E = σ/ε`
- FCC 晶体是各向同性的立方晶体，三个方向的 E 应该相同（在 Voigt 平均意义上）

### 练习 3：含空位晶体的拉伸

**任务**：创建一个含有空位的晶体，然后进行拉伸测试。与完美晶体的应力-应变曲线比较。

**提示**：
- 先创建完美晶体，删除一个原子，再做拉伸
- 比较两条应力-应变曲线
- 含空位晶体的屈服应力通常更低
- 空位可能成为断裂的裂纹源

### 练习 4：CNA 识别位错核心

**任务**：在拉伸模拟中，使用 CNA 识别塑性变形区域（位错发射和运动）。

**提示**：
- 在较高的应变下（超过弹性极限），位错开始形核和运动
- 位错核心区域 CNA 值为 5（无序）
- HCP 区域（CNA=2）对应层错
- 可以统计各 CNA 类型的原子数随应变的变化

```lammps
# 统计各结构类型的原子数
compute  cna all cna/atom 1.5
variable n_fcc  equal count(all,c_cna_all,1)   # CNA=1: FCC
variable n_hcp  equal count(all,c_cna_all,2)   # CNA=2: HCP
variable n_bcc  equal count(all,c_cna_all,3)   # CNA=3: BCC
variable n_icos equal count(all,c_cna_all,4)   # CNA=4: ICOS
variable n_other equal count(all,c_cna_all,5)  # CNA=5: 无序
```

### 练习 5：计算弹性常数 C11, C12, C44

**任务**：通过施加微小应变并测量应力响应，计算 FCC 晶体的三个独立弹性常数。

**方法**：
1. **C11**：在 x 方向施加微小单轴应变 ε_xx，测量 σ_xx，计算 `C11 = σ_xx / ε_xx`
2. **C11 - C12**：施加纯剪切应变，测量剪切应力响应
3. **C44**：施加剪切应变 ε_xy，测量 σ_xy，计算 `C44 = σ_xy / ε_xy`

**步骤**：
```lammps
# 1. 计算 C11：单轴应变
#    施加 ε_xx = 0.001 (很小的应变，确保在线性区)
#    测量 σ_xx
#    C11 = σ_xx / ε_xx

# 2. 计算 C11 - C12
#    施加 ε_xx = ε, ε_yy = -ε (纯剪切)
#    C11 - C12 = σ_xx / (2ε)

# 3. 计算 C44
#    施加 xy 剪切应变
#    C44 = σ_xy / ε_xy
```

**参考值**（LJ FCC，约化单位）：
- C11 ≈ 15 ~ 20
- C12 ≈ 8 ~ 12
- C44 ≈ 5 ~ 8

---

## 参考资料

- [compute cna/atom 文档](https://docs.lammps.org/stable/compute_cna_atom.html) — 共邻分析命令的详细说明
- [compute stress/atom 文档](https://docs.lammps.org/stable/compute_stress_atom.html) — 原子应力计算命令
- [fix deform 文档](https://docs.lammps.org/stable/fix_deform.html) — 施加变形的命令
- [compute reduce 文档](https://docs.lammps.org/stable/compute_reduce.html) — 对原子量进行统计操作
- [LAMMPS Units 文档](https://docs.lammps.org/stable/units.html) — 约化单位的详细说明
