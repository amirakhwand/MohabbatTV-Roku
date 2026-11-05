#!/bin/sh
# Builds the installable app at build/MohabbatTV.zip.
set -e
cd "$(dirname "$0")/.."
mkdir -p build
rm -f build/MohabbatTV.zip
zip -qr build/MohabbatTV.zip manifest source components images data -x '*.DS_Store'
echo "Built build/MohabbatTV.zip"
