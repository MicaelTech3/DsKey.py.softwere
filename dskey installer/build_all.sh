#!/bin/bash

echo "=== DSKEY BUILD MULTIPLATAFORMA ==="

# Limpa builds antigos
rm -rf builds dist build
mkdir -p builds/linux builds/win

# =========================
# BUILD LINUX
# =========================
echo "[1/2] Compilando para Linux..."

pyinstaller \
  --onefile \
  --windowed \
  --distpath builds/linux \
  --name dskey \
  dskey.py

# Limpeza temporária
rm -rf build dist dskey.spec

# =========================
# BUILD WINDOWS (EXE)
# =========================
echo "[2/2] Compilando para Windows (.exe)..."

wine python -m pip install --upgrade pip pyinstaller

wine pyinstaller \
  --onefile \
  --windowed \
  --icon=py.ico \
  --distpath builds/win \
  --name dskey \
  dskey.py

# Limpeza final
rm -rf build dist dskey.spec

echo "=== BUILD FINALIZADO ==="
echo "Linux  → builds/linux/dskey"
echo "Windows→ builds/win/dskey.exe"
