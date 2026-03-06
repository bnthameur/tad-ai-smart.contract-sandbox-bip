FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including Foundry prerequisites)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Foundry
RUN curl -L https://foundry.paradigm.xyz | bash && \
    export PATH="$HOME/.foundry/bin:$PATH" && \
    foundryup

ENV PATH="/root/.foundry/bin:${PATH}"

# Copy requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# Copy core src modules (needed for imports)
COPY src ./src
COPY prompts ./prompts

# Verify installations
RUN forge --version && cast --version && anvil --version

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
