#!/bin/bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the deploy script from the scripts directory
exec "$SCRIPT_DIR/scripts/deploy.sh"

