# LAMMPS 新手学习教程

[English](README.md) | [简体中文](README_zh.md)

---

[![GitHub License](https://img.shields.io/github/license/hyfaust/lmp-learn)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)]()
[![LAMMPS](https://img.shields.io/badge/LAMMPS-2024+-blue.svg)](https://www.lammps.org/)
[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blueviolet)](https://hyfaust.github.io/lmp-learn/)

> 从零开始学习分子动力学模拟 — 12个循序渐进的实战项目

## 目录

- [简介](#简介)
- [环境要求](#环境要求)
- [安装指南](#安装指南)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [课程大纲](#课程大纲)
- [Web 界面](#web-界面)
- [部署指南](#部署指南)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)
- [致谢](#致谢)

## 简介

本教程为 LAMMPS（大规模原子/分子大规模并行模拟器）提供了一个结构化的学习路径。通过 12 个循序渐进的项目，你将学到：

- **分子动力学基础** — 力场、积分器、边界条件
- **热力学系综** — NVE、NVT、NPT 及其实现方式
- **材料建模** — LJ 流体、金属（EAM）、分子体系（OPLS）
- **高级技术** — 非平衡 MD、自由能计算、NEB
- **数据分析** — MSD、RDF、Green-Kubo、Python 后处理

每个项目包含：
- 可直接运行的 LAMMPS 输入脚本
- 每个命令的详细解释
- 概念背景和物理含义
- 动手练习题

## 环境要求

| 依赖项 | 版本 | 是否必需 | 用途 |
|--------|------|----------|------|
| LAMMPS | >= 2024 | 是 | 分子动力学模拟引擎 |
| Python | >= 3.9 | 是 | 数据分析脚本（项目 12） |
| Conda | 任意 | 否 | Python 环境管理 |
| MPI | 任意 | 否 | 并行执行（项目 11 NEB） |

## 安装指南

### 安装 LAMMPS

```bash
# Ubuntu/Debian
sudo apt-get install lammps

# macOS (Homebrew)
brew install lammps

# Conda（跨平台）
conda install -c conda-forge lammps
```

### 配置 Python 环境（项目 12 需要）

```bash
conda create -n lmp-learn python=3.10 -y
conda activate lmp-learn
conda install -c conda-forge lammps matplotlib numpy -y
```

## 快速开始

### 运行单个示例

```bash
cd projects/01-first-simulation
lmp -in in.melt
```

### 运行所有示例

```bash
bash scripts/run_all.sh
```

### 启动 Web 教程界面

```bash
cd docs
python3 -m http.server 8080
# 在浏览器中打开 http://localhost:8080
```

## 项目结构

```
lmp-learn/
├── projects/                    # 12 个教程项目
│   ├── 01-first-simulation/     # Level 1：入门基础
│   ├── 02-units-and-boxes/
│   ├── 03-energy-minimization/
│   ├── 04-thermostat-nvt/       # Level 2：基础操作
│   ├── 05-barostat-npt/
│   ├── 06-molecular-simulation/
│   ├── 07-metal-eam/            # Level 3：中级应用
│   ├── 08-crystal-defects/
│   ├── 09-diffusion-transport/
│   ├── 10-non-equilibrium-md/   # Level 4：高级应用
│   ├── 11-free-energy-neb/
│   └── 12-python-analysis/
├── docs/                        # Web 教程界面
│   ├── index.html               # SPA 入口文件
│   ├── css/style.css            # 样式文件
│   ├── js/app.js                # 应用逻辑
│   └── projects/                # 符号链接到 ../projects
├── scripts/
│   └── run_all.sh               # 批量运行脚本
├── LICENSE                      # GPL v3 许可证
└── README.md                    # 英文说明文档
```

## 课程大纲

### 🟢 Level 1 — 入门基础

| # | 项目 | 核心内容 |
|---|------|----------|
| 01 | [第一个模拟：LJ 熔化](projects/01-first-simulation/) | input script 结构、原子创建、LJ 势、基本运行 |
| 02 | [单位制与模拟盒子](projects/02-units-and-boxes/) | units 命令、边界条件、lattice、read_data |
| 03 | [能量最小化](projects/03-energy-minimization/) | minimize、共轭梯度法、势能面优化 |

### 🟡 Level 2 — 基础操作

| # | 项目 | 核心内容 |
|---|------|----------|
| 04 | [温度控制与 NVT 系综](projects/04-thermostat-nvt/) | 系综概念、Nosé-Hoover 恒温器、温度弛豫 |
| 05 | [压力控制与 NPT 系综](projects/05-barostat-npt/) | 恒压器、NPT 系综、密度自洽 |
| 06 | [分子模拟入门](projects/06-molecular-simulation/) | 分子拓扑、力场参数、TIP3P 水模型 |

### 🟠 Level 3 — 中级应用

| # | 项目 | 核心内容 |
|---|------|----------|
| 07 | [金属体系与 EAM 势](projects/07-metal-eam/) | 多体势、EAM 势函数、Cu 晶体模拟 |
| 08 | [晶体缺陷与力学性质](projects/08-crystal-defects/) | 点缺陷、应力-应变、弹性常数 |
| 09 | [扩散与输运性质](projects/09-diffusion-transport/) | MSD、Green-Kubo、扩散系数、RDF |

### 🔴 Level 4 — 高级应用

| # | 项目 | 核心内容 |
|---|------|----------|
| 10 | [非平衡分子动力学](projects/10-non-equilibrium-md/) | NEMD、剪切流、粘度计算 |
| 11 | [自由能计算与 NEB](projects/11-free-energy-neb/) | 最小能量路径、鞍点搜索、过渡态 |
| 12 | [Python 接口与数据分析](projects/12-python-analysis/) | LAMMPS Python 模块、数据后处理、可视化 |

## Web 界面

本教程包含一个基于 Web 的阅读界面，具有以下功能：

- **Markdown 渲染**，支持语法高亮
- **LaTeX 数学公式**，通过 MathJax 渲染
- **目录导航**（可手动显示/隐藏）
- **学习进度跟踪**，基于 localStorage
- **暗色/亮色主题**切换
- **响应式设计**，支持移动端和桌面端

在线访问：**https://hyfaust.github.io/lmp-learn/**

## 部署指南

### GitHub Pages

本项目已配置为从 `docs/` 目录部署到 GitHub Pages：

1. Fork 或克隆本仓库
2. 进入 **Settings → Pages**
3. 设置 **Source** 为 "Deploy from a branch"
4. 选择 **branch: main**，**folder: /docs**
5. 保存并等待部署完成

### 本地开发

```bash
# 启动本地服务器
cd docs
python3 -m http.server 8080

# 或使用 Node.js
npx serve docs -p 8080
```

## 常见问题

**Q：需要什么版本的 LAMMPS？**
A：本教程基于 LAMMPS 稳定版（2024+）测试。较早版本可能适用于大多数项目，但部分命令可能有所不同。

**Q：能否并行运行示例？**
A：可以！使用 `mpirun -np 4 lmp -in in.melt` 进行并行执行。项目 11（NEB）需要 MPI 支持。

**Q：如何验证 LAMMPS 安装是否正确？**
A：运行 `lmp -h` 检查版本和可用包。

**Q：项目 12 的 Python 脚本无法运行怎么办？**
A：确保使用 conda 环境：`conda activate lmp-learn`。脚本需要 LAMMPS Python 绑定和 matplotlib。

## 贡献指南

欢迎贡献！请随时提交 issue 或 pull request。

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/amazing-feature`）
3. 提交更改（`git commit -m 'Add amazing feature'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 创建 Pull Request

## 许可证

本项目基于 GNU 通用公共许可证 v3.0 发布 — 详见 [LICENSE](LICENSE) 文件。

## 致谢

- [LAMMPS](https://www.lammps.org/) — Sandia 国家实验室
- [LAMMPS 文档](https://docs.lammps.org/) — 官方参考手册
- [lammps-tutorials](https://lammpstutorials.github.io/) — 社区教程
