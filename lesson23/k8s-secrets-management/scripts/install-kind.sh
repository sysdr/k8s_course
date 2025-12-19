#!/bin/bash
set -euo pipefail

echo "Installing kind..."

# Create ~/.local/bin if it doesn't exist
mkdir -p ~/.local/bin

# Download kind
echo "Downloading kind..."
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64

# Make it executable
chmod +x ./kind

# Move to ~/.local/bin (no sudo required)
echo "Installing kind to ~/.local/bin..."
mv ./kind ~/.local/bin/kind

# Add ~/.local/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "Adding ~/.local/bin to PATH..."
    echo "Please add the following line to your ~/.bashrc or ~/.zshrc:"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "Or run this command to add it to current session:"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    # Add to current session
    export PATH="$HOME/.local/bin:$PATH"
fi

# Verify installation
if command -v kind &> /dev/null; then
    echo "kind installed successfully!"
    kind version
else
    echo "Installation completed, but kind is not in PATH."
    echo "Please run: export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "Or restart your terminal."
    exit 1
fi

