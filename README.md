# LAMMPS Beginner Tutorial

[English](README.md) | [简体中文](README_zh.md)

---

[![GitHub License](https://img.shields.io/github/license/hyfaust/lmp-learn)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)]()
[![LAMMPS](https://img.shields.io/badge/LAMMPS-2024+-blue.svg)](https://www.lammps.org/)
[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blueviolet)](https://hyfaust.github.io/lmp-learn/)

> A hands-on molecular dynamics tutorial with 12 progressive projects — from first simulation to advanced analysis.

## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Course Outline](#course-outline)
- [Web Interface](#web-interface)
- [Deployment](#deployment)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Introduction

This tutorial provides a structured, hands-on learning path for LAMMPS (Large-scale Atomic/Molecular Massively Parallel Simulator). Through 12 progressive projects, you will learn:

- **Molecular dynamics fundamentals** — force fields, integrators, boundary conditions
- **Thermodynamic ensembles** — NVE, NVT, NPT and their implementations
- **Material modeling** — LJ fluids, metals (EAM), molecular systems (OPLS)
- **Advanced techniques** — non-equilibrium MD, free energy calculations, NEB
- **Data analysis** — MSD, RDF, Green-Kubo, Python post-processing

Each project includes:
- Ready-to-run LAMMPS input scripts
- Detailed explanations of every command
- Conceptual background and physical meaning
- Hands-on exercises for practice

## Prerequisites

| Dependency | Version | Required | Purpose |
|------------|---------|----------|---------|
| LAMMPS     | >= 2024 | Yes      | MD simulation engine |
| Python     | >= 3.9  | Yes      | Analysis scripts (Project 12) |
| Conda      | any     | No       | Python environment management |
| MPI        | any     | No       | Parallel execution (Project 11 NEB) |

## Installation

### Install LAMMPS

```bash
# Ubuntu/Debian
sudo apt-get install lammps

# macOS (Homebrew)
brew install lammps

# Conda (cross-platform)
conda install -c conda-forge lammps
```

### Set Up Python Environment (for Project 12)

```bash
conda create -n lmp-learn python=3.10 -y
conda activate lmp-learn
conda install -c conda-forge lammps matplotlib numpy -y
```

## Quick Start

### Run a Single Example

```bash
cd projects/01-first-simulation
lmp -in in.melt
```

### Run All Examples

```bash
bash scripts/run_all.sh
```

### Launch Web Interface

```bash
cd docs
python3 -m http.server 8080
# Open http://localhost:8080 in your browser
```

## Project Structure

```
lmp-learn/
├── projects/                    # 12 tutorial projects
│   ├── 01-first-simulation/     # Level 1: Beginners
│   ├── 02-units-and-boxes/
│   ├── 03-energy-minimization/
│   ├── 04-thermostat-nvt/       # Level 2: Fundamentals
│   ├── 05-barostat-npt/
│   ├── 06-molecular-simulation/
│   ├── 07-metal-eam/            # Level 3: Intermediate
│   ├── 08-crystal-defects/
│   ├── 09-diffusion-transport/
│   ├── 10-non-equilibrium-md/   # Level 4: Advanced
│   ├── 11-free-energy-neb/
│   └── 12-python-analysis/
├── docs/                        # Web tutorial interface
│   ├── index.html               # SPA entry point
│   ├── css/style.css            # Styles
│   ├── js/app.js                # Application logic
│   └── projects/                # Symlink to ../projects
├── scripts/
│   └── run_all.sh               # Batch run script
├── LICENSE                      # GPL v3
└── README.md                    # This file
```

## Course Outline

### 🟢 Level 1 — Getting Started

| # | Project | Core Topics |
|---|---------|-------------|
| 01 | [First Simulation: LJ Melting](projects/01-first-simulation/) | Input script structure, atom creation, LJ potential, basic run |
| 02 | [Units and Simulation Box](projects/02-units-and-boxes/) | units command, boundary conditions, lattice, read_data |
| 03 | [Energy Minimization](projects/03-energy-minimization/) | minimize, conjugate gradient, potential energy surface |

### 🟡 Level 2 — Core Techniques

| # | Project | Core Topics |
|---|---------|-------------|
| 04 | [Temperature Control: NVT](projects/04-thermostat-nvt/) | Ensemble concepts, Nosé-Hoover thermostat, temperature relaxation |
| 05 | [Pressure Control: NPT](projects/05-barostat-npt/) | Barostat, NPT ensemble, density self-consistency |
| 06 | [Molecular Simulation](projects/06-molecular-simulation/) | Molecular topology, force field parameters, TIP3P water |

### 🟠 Level 3 — Intermediate Applications

| # | Project | Core Topics |
|---|---------|-------------|
| 07 | [Metal Systems with EAM](projects/07-metal-eam/) | Many-body potentials, EAM potential, Cu crystal simulation |
| 08 | [Crystal Defects and Mechanics](projects/08-crystal-defects/) | Point defects, stress-strain, elastic constants |
| 09 | [Diffusion and Transport](projects/09-diffusion-transport/) | MSD, Green-Kubo, diffusion coefficient, RDF |

### 🔴 Level 4 — Advanced Applications

| # | Project | Core Topics |
|---|---------|-------------|
| 10 | [Non-Equilibrium MD](projects/10-non-equilibrium-md/) | NEMD, shear flow, viscosity calculation |
| 11 | [Free Energy and NEB](projects/11-free-energy-neb/) | Minimum energy path, saddle point search, transition state |
| 12 | [Python Interface and Analysis](projects/12-python-analysis/) | LAMMPS Python module, data post-processing, visualization |

## Web Interface

The tutorial includes a web-based reading interface with:

- **Markdown rendering** with syntax highlighting
- **LaTeX math support** via MathJax
- **Table of contents** (togglable) for each project
- **Learning progress tracking** with localStorage
- **Dark/light theme** toggle
- **Responsive design** for mobile and desktop

Access the live version at: **https://hyfaust.github.io/lmp-learn/**

## Deployment

### GitHub Pages

This project is configured for GitHub Pages deployment from the `docs/` directory:

1. Fork or clone this repository
2. Go to **Settings → Pages**
3. Set **Source** to "Deploy from a branch"
4. Select **branch: main**, **folder: /docs**
5. Save and wait for deployment

### Local Development

```bash
# Start local server
cd docs
python3 -m http.server 8080

# Or with Node.js
npx serve docs -p 8080
```

## FAQ

**Q: What version of LAMMPS do I need?**
A: This tutorial was tested with LAMMPS stable release (2024+). Earlier versions may work for most projects but some commands might differ.

**Q: Can I run the examples in parallel?**
A: Yes! Use `mpirun -np 4 lmp -in in.melt` for parallel execution. Project 11 (NEB) requires MPI.

**Q: How do I verify my LAMMPS installation?**
A: Run `lmp -h` to check the version and available packages.

**Q: The Python scripts in Project 12 don't work.**
A: Make sure you're using the conda environment: `conda activate lmp-learn`. The scripts require LAMMPS Python bindings and matplotlib.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [LAMMPS](https://www.lammps.org/) — Sandia National Laboratories
- [LAMMPS Documentation](https://docs.lammps.org/) — Official reference
- [lammps-tutorials](https://lammpstutorials.github.io/) — Community tutorials
