# TAD AI Smart Contract Security Sandbox
# Phase 1: Environment Setup

FROM ubuntu:22.04

LABEL maintainer="The Algerian Developer"
LABEL description="AI-Powered Smart Contract Security Sandbox"

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install base dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    build-essential \
    libssl-dev \
    pkg-config \
    jq \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install Foundry (forge, cast, anvil)
RUN curl -L https://foundry.paradigm.xyz | bash \
    && export PATH="$HOME/.foundry/bin:$PATH" \
    && foundryup

# Add Foundry to PATH permanently
ENV PATH="/root/.foundry/bin:${PATH}"

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Create workspace directories
WORKDIR /app
RUN mkdir -p \
    /app/contracts \
    /app/scripts \
    /app/tests \
    /app/forks \
    /app/reports \
    /app/data

# Copy project files
COPY . /app/

# Verify installations
RUN forge --version && cast --version && anvil --version

# Expose Anvil port
EXPOSE 8545

# Default command - interactive shell
CMD ["/bin/bash"]
