#!/bin/sh
# Installs the app on a Roku in Developer Mode.
# Usage: ROKU_IP=192.168.1.50 ROKU_PASSWORD=your-dev-password scripts/install.sh
set -e
: "${ROKU_IP:?Set ROKU_IP to your Roku's IP address}"
: "${ROKU_PASSWORD:?Set ROKU_PASSWORD to your Roku developer password}"
cd "$(dirname "$0")/.."
scripts/package.sh
curl --fail --silent --show-error --digest -u "rokudev:$ROKU_PASSWORD" \
  -F "mysubmit=Install" -F "archive=@build/MohabbatTV.zip" \
  "http://$ROKU_IP/plugin_install" -o /dev/null
echo "Installed on $ROKU_IP"
