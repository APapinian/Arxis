#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
GREEN='\033[0;32m'; CYAN='\033[0;36m'; RED='\033[0;31m'
YELLOW='\033[1;33m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
echo ""
echo -e "${BOLD}${CYAN}  ⚙  Arxis başlatılıyor...${NC}"
echo -e "${DIM}  Arch Linux Paket Yöneticisi${NC}"
echo ""
if [ ! -d "venv" ]; then
    echo -e "  ${RED}✗${NC}  Sanal ortam bulunamadı!"
    echo -e "  ${YELLOW}→${NC}  Önce: ${BOLD}bash install.sh${NC}"
    echo ""; exit 1
fi
source venv/bin/activate
echo -e "  ${GREEN}✓${NC}  venv aktif — Python: $(python --version 2>&1 | cut -d' ' -f2)"
echo -e "  ${GREEN}✓${NC}  Dizin: $SCRIPT_DIR"
echo -e "${DIM}  ──────────────────────────────────────────${NC}"
echo ""
python main.py "$@"
