FROM python:3.11-slim

# Install system packages including Go
RUN apt-get update && \
    apt-get install -y \
        curl \
        wget \
        gnupg \
        build-essential \
        ca-certificates \
        git && \
    # Install Node.js
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g n && \
    n 22.13.0 && \
    # Install Go
    wget https://golang.org/dl/go1.22.3.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.22.3.linux-amd64.tar.gz && \
    rm go1.22.3.linux-amd64.tar.gz && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment paths
ENV PATH="/usr/local/go/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy everything including goreq.go, go.mod, etc.
COPY . .

# Set up Go dependencies
RUN go mod tidy

# Optional: Build the Go binary for faster subprocess (safer in prod)
RUN go build -o goreq goreq.go

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies
RUN npm install

# Cloud Run config
ENV PORT 8080
ENV GOOGLE_APPLICATION_CREDENTIALS /app/service.json
EXPOSE 8080

CMD ["python", "main.py"]
