#!/bin/bash
# LAMMPS 教程 - 批量运行所有示例脚本
# 用法: bash scripts/run_all.sh [项目编号]
# 示例: bash scripts/run_all.sh 01    (只运行项目01)
#       bash scripts/run_all.sh       (运行所有项目)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")/projects"
LMP_CMD="lmp"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LAMMPS 新手学习教程 - 批量运行${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 LAMMPS 是否可用
if ! command -v $LMP_CMD &> /dev/null; then
    echo -e "${RED}错误: 找不到 LAMMPS 命令 '$LMP_CMD'${NC}"
    echo "请确保 LAMMPS 已安装并添加到 PATH 中"
    exit 1
fi

echo -e "${GREEN}✓ 找到 LAMMPS: $(which $LMP_CMD)${NC}"
echo ""

# 定义每个项目的输入文件
declare -A PROJECT_SCRIPTS
PROJECT_SCRIPTS=(
    ["01"]="in.melt"
    ["02"]="in.lj_units in.real_units in.metal_units"
    ["03"]="in.minimize in.min_compare"
    ["04"]="in.nvt in.nvt_compare"
    ["05"]="in.npt in.npt_aniso"
    ["06"]="in.ethane"
    ["07"]="in.cu_crystal in.cu_thermal"
    ["08"]="in.vacancy in.tensile"
    ["09"]="in.diffusion in.rdf"
    ["10"]="in.shear in.viscosity_gk"
    ["11"]="in.neb_setup in.neb"
    ["12"]="run_simulation.py"
)

# 项目目录名
declare -A PROJECT_DIRS
PROJECT_DIRS=(
    ["01"]="01-first-simulation"
    ["02"]="02-units-and-boxes"
    ["03"]="03-energy-minimization"
    ["04"]="04-thermostat-nvt"
    ["05"]="05-barostat-npt"
    ["06"]="06-molecular-simulation"
    ["07"]="07-metal-eam"
    ["08"]="08-crystal-defects"
    ["09"]="09-diffusion-transport"
    ["10"]="10-non-equilibrium-md"
    ["11"]="11-free-energy-neb"
    ["12"]="12-python-analysis"
)

run_project() {
    local num=$1
    local dir="${PROJECT_DIRS[$num]}"
    local scripts="${PROJECT_SCRIPTS[$num]}"
    local work_dir="$PROJECT_DIR/$dir"

    echo -e "${YELLOW}━━━ 项目 $num: $dir ━━━${NC}"

    if [ ! -d "$work_dir" ]; then
        echo -e "${RED}  ✗ 目录不存在: $work_dir${NC}"
        return 1
    fi

    cd "$work_dir"

    for script in $scripts; do
        if [ ! -f "$script" ]; then
            echo -e "${RED}  ✗ 脚本不存在: $script${NC}"
            continue
        fi

        echo -e "${BLUE}  运行: $LMP_CMD -in $script${NC}"

        if [[ "$script" == *.py ]]; then
            # Python 脚本
            python3 "$script" 2>&1 | tail -5
        else
            # LAMMPS 输入脚本
            $LMP_CMD -in "$script" 2>&1 | tail -5
        fi

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ $script 完成${NC}"
        else
            echo -e "${RED}  ✗ $script 失败${NC}"
        fi
        echo ""
    done

    cd "$PROJECT_DIR"
}

# 运行指定项目或所有项目
if [ -n "$1" ]; then
    # 运行指定项目
    num=$(printf "%02d" "$1" 2>/dev/null || echo "$1")
    if [ -n "${PROJECT_SCRIPTS[$num]}" ]; then
        run_project "$num"
    else
        echo -e "${RED}未知项目: $1${NC}"
        echo "可用项目: 01-12"
        exit 1
    fi
else
    # 运行所有项目
    FAILED=0
    for num in $(echo "${!PROJECT_SCRIPTS[@]}" | tr ' ' '\n' | sort); do
        run_project "$num" || ((FAILED++))
        echo ""
    done

    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}全部完成!${NC}"
    if [ $FAILED -gt 0 ]; then
        echo -e "${YELLOW}警告: $FAILED 个项目有错误${NC}"
    fi
fi

echo ""
echo -e "${BLUE}启动 Web 教程界面:${NC}"
echo "  python3 -m http.server 8080 -d $(dirname "$PROJECT_DIR")/web"
echo ""
