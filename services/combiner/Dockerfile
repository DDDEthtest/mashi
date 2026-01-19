# Base image
FROM alpine:3.18

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV CHROME_BIN=/usr/bin/chromium-browser

# Install system dependencies including Node.js, Python, and Chromium
RUN apk add --no-cache \
    bash \
    curl \
    wget \
    python3 \
    py3-pip \
    ffmpeg \
    nss \
    freetype \
    harfbuzz \
    ttf-freefont \
    font-noto \
    udev \
    build-base \
    libffi-dev \
    zlib-dev \
    xz-dev \
    git \
    nodejs \
    npm \
    chromium \
    && python3 -m ensurepip \
    && pip3 install --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Copy Node.js dependencies first for caching
COPY package.json ./
RUN npm install --unsafe-perm

# Copy Python requirements and install
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY ../.. .

# Default command to run both Python and Node.js
# Make sure Puppeteer uses Chromium installed via apk
CMD ["bash", "-c", "python3 main.py & node Main.js"]
