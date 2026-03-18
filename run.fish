#!/usr/bin/env fish
set SCRIPT_DIR (cd (dirname (status --current-filename)); and pwd)
cd $SCRIPT_DIR
echo ""
echo -e "\033[1m\033[36m  ⚙  Arxis başlatılıyor...\033[0m"
echo -e "\033[2m  Arch Linux Paket Yöneticisi\033[0m"
echo ""
if not test -d venv
    echo -e "\033[31m  ✗  Sanal ortam bulunamadı!\033[0m"
    echo -e "\033[33m  →  Önce: \033[1mbash install.sh\033[0m"
    echo ""; exit 1
end
source venv/bin/activate.fish
set PY_VER (python --version 2>&1 | string split ' ' | tail -1)
echo -e "\033[32m  ✓\033[0m  venv aktif — Python: $PY_VER"
echo -e "\033[32m  ✓\033[0m  Dizin: $SCRIPT_DIR"
echo -e "\033[2m  ──────────────────────────────────────────\033[0m"
echo ""
python main.py $argv
