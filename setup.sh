#!/bin/bash
# Workspace setup script

echo "Installing dependencies..."

# Check for package manager
if command -v bun &> /dev/null; then
    echo "Using bun..."
    bun install
elif command -v pnpm &> /dev/null; then
    echo "Using pnpm..."
    pnpm install
elif command -v yarn &> /dev/null; then
    echo "Using yarn..."
    yarn install
elif command -v npm &> /dev/null; then
    echo "Using npm..."
    npm install
elif command -v pip &> /dev/null; then
    echo "Using pip..."
    pip install -r requirements.txt
fi

echo "Done!"
