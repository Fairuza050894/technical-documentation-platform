#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIN_FREE_KB=$((6 * 1024 * 1024))
WARN_FREE_KB=$((12 * 1024 * 1024))

free_kb="$(df -Pk "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')"
if [ "${free_kb}" -lt "${MIN_FREE_KB}" ]; then
  printf 'Bootstrap dihentikan: ruang kosong kurang dari 6 GiB.\n' >&2
  exit 1
fi

if [ "${free_kb}" -lt "${WARN_FREE_KB}" ]; then
  printf 'Peringatan: ruang kosong kurang dari 12 GiB. Docker dan database lokal belum akan dipasang.\n'
fi

if ! command -v brew >/dev/null 2>&1; then
  printf 'Homebrew tidak ditemukan. Pasang Homebrew terlebih dahulu lalu jalankan kembali.\n' >&2
  exit 1
fi

if ! brew list python@3.12 >/dev/null 2>&1; then
  brew install python@3.12
fi

if ! command -v uv >/dev/null 2>&1; then
  brew install uv
fi

python_bin="$(brew --prefix python@3.12)/bin/python3.12"
if [ ! -x "${python_bin}" ]; then
  printf 'Python 3.12 tidak ditemukan setelah instalasi.\n' >&2
  exit 1
fi

node_version="$(node --version 2>/dev/null || true)"
if [ "${node_version}" != "v22.17.1" ]; then
  printf 'Peringatan: versi Node aktif adalah %s; baseline repository adalah v22.17.1.\n' "${node_version:-tidak tersedia}"
fi

cd "${PROJECT_ROOT}"
uv sync --project backend --all-groups
npm --prefix frontend install

printf 'Bootstrap selesai.\n'
printf 'Backend : make dev-backend\n'
printf 'Frontend: make dev-frontend\n'
printf 'Verify  : make verify\n'
