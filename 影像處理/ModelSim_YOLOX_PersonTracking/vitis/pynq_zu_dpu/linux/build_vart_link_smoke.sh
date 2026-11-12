#!/usr/bin/env bash
# Build only: source the matching PetaLinux SDK environment before calling.
set -euo pipefail

: "${CXX:?source the matching SDK environment before running this script}"

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
output_path=${1:-"${script_dir}/vart_link_smoke.elf"}

# The SDK's CXX contains both compiler name and required target flags.
# Intentional shell splitting preserves that documented SDK contract.
# shellcheck disable=SC2086
${CXX} -std=c++14 -Wall -Wextra -Werror \
  "${script_dir}/vart_link_smoke.cpp" \
  -o "${output_path}" \
  -lvart-runner -lxir -lunilog

echo "PYNQ_ZU_VART_LINK_SMOKE_PASS output=${output_path}"
