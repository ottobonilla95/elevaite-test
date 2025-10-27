#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
  echo -e "${BLUE}Usage: $0 [OPTIONS]${NC}"
  echo -e "${BLUE}Options:${NC}"
  echo -e "  ${GREEN}--skip-dev${NC}    Skip development and testing dependencies"
  echo -e "  ${GREEN}--help${NC}        Display this help message"
  exit 0
}

SKIP_DEV=false
for arg in "$@"; do
  case $arg in
    --skip-dev)
      SKIP_DEV=true
      shift
      ;;
    --help)
      show_help
      ;;
    *)
      ;;
  esac
done

echo -e "${GREEN}Starting backend dependencies installation...${NC}"

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

if ! command_exists uv; then
  echo -e "${YELLOW}uv is not installed. Attempting to install it...${NC}"

  if command_exists curl; then
    echo -e "${GREEN}Installing uv using curl...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
  elif command_exists wget; then
    echo -e "${YELLOW}curl not found. Installing uv using wget...${NC}"
    wget -qO- https://astral.sh/uv/install.sh | sh
  else
    echo -e "${RED}Error: Neither curl nor wget is installed. Please install one of them to continue or install uv manually https://docs.astral.sh/uv/getting-started/installation/ ${NC}"
    exit 1
  fi

  # Source the shell configuration to make uv available in the current session
  if [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc"
  elif [ -f "$HOME/.bash_profile" ]; then
    source "$HOME/.bash_profile"
  elif [ -f "$HOME/.zshrc" ]; then
    source "$HOME/.zshrc"
  fi

  if ! command_exists uv; then
    echo -e "${YELLOW}uv installation may have succeeded, but the command is not available in the current shell.${NC}"
    echo -e "${YELLOW}Please open a new terminal and run this script again.${NC}"
    exit 1
  fi
fi

echo -e "${GREEN}uv is installed. Installing backend dependencies...${NC}"

if [ "$SKIP_DEV" = true ]; then
  echo -e "${BLUE}Skipping development dependencies (--skip-dev flag detected)...${NC}"
  echo -e "${GREEN}Running uv sync with production dependencies only...${NC}"
  uv sync --all-packages
  echo -e "${YELLOW}Skipped testing and development dependencies.${NC}"
else
  echo -e "${GREEN}Running uv sync with all extras and packages (including development dependencies)...${NC}"
  uv sync --all-extras --all-packages
  echo -e "${YELLOW}Note: Use --skip-dev flag to skip testing and development dependencies.${NC}"
fi

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Backend dependencies installed successfully!${NC}"
else
  echo -e "${RED}Error: Failed to install backend dependencies.${NC}"
  exit 1
fi

echo -e "${GREEN}Installation complete!${NC}"
