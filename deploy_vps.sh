#!/bin/bash
# TAD AI - VPS Deployment Script
# Transforms a fresh Ubuntu/Debian server into a TAD AI Security Engine Node

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting TAD AI Engine Deployment...${NC}"

# 1. System Updates & Dependencies
echo -e "\n${GREEN}[1/5] Updating system...${NC}"
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl git apt-transport-https ca-certificates gnupg lsb-release htop

# 2. Install Docker & Docker Compose
if ! command -v docker &> /dev/null; then
    echo -e "\n${GREEN}[2/5] Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker installed."
else
    echo -e "\n${GREEN}[2/5] Docker already installed.${NC}"
fi

# 3. Setup Environment
echo -e "\n${GREEN}[3/5] Configuring Environment...${NC}"
if [ ! -f .env ]; then
    echo "Creating .env from example..."
    cp backend/.env.example .env
    
    # Prompt for key variables if missing
    echo -e "${RED}⚠️  Action Required: We need at least one API key.${NC}"
    read -p "Enter DeepSeek API Key (or press Enter to skip): " DEEPSEEK_KEY
    if [ ! -z "$DEEPSEEK_KEY" ]; then
        sed -i "s/your_deepseek_key/$DEEPSEEK_KEY/" .env
    fi
    
    read -p "Enter Alchemy/Infura RPC URL (or press Enter to skip): " RPC_URL
    if [ ! -z "$RPC_URL" ]; then
        sed -i "s|https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY|$RPC_URL|" .env
    fi
    
    # Generate random secret key for API
    SECRET_KEY=$(openssl rand -hex 32)
    echo "SECRET_KEY=$SECRET_KEY" >> .env
else
    echo ".env already exists. Skipping configuration."
fi

# 4. Build & Launch
echo -e "\n${GREEN}[4/5] Building & Launching Engine...${NC}"
# Pull latest changes if it's a git repo
git pull origin main || true

# Build and Start
docker compose -f docker-compose.prod.yml up -d --build

# 5. Verification
echo -e "\n${GREEN}[5/5] Verifying Deployment...${NC}"
sleep 5
if docker compose -f docker-compose.prod.yml ps | grep "Up"; then
    echo -e "\n${BLUE}✅ Engine is ONLINE!${NC}"
    echo "API: http://localhost:8000"
    echo "Docs: http://localhost:8000/docs"
    echo "Monitoring: 'docker compose -f docker-compose.prod.yml logs -f'"
else
    echo -e "\n${RED}❌ Engine failed to start. Check logs.${NC}"
    docker compose -f docker-compose.prod.yml logs
    exit 1
fi
