# --------------------------------------------------
# Base image (Playwright + Ubuntu 22.04)
# --------------------------------------------------
FROM mcr.microsoft.com/playwright:v1.60.0-jammy

# --------------------------------------------------
# Environment
# --------------------------------------------------
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN ln -sf /usr/bin/python3 /usr/bin/python

# --------------------------------------------------
# System dependencies
# --------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    python3-pip \
    build-essential \
    pkg-config \
    libgl1 \
    libglib2.0-0 \
    libpq-dev \
    libwebp-dev \
    imagemagick \
    libmagickwand-dev \
    librsvg2-bin \
    fontconfig \
    fonts-dejavu-core \
    wget \
    curl \
    xz-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Install FFmpeg 6.x
# --------------------------------------------------
RUN wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar -xf ffmpeg-release-amd64-static.tar.xz && \
    cp ffmpeg-*/ffmpeg /usr/local/bin/ && \
    cp ffmpeg-*/ffprobe /usr/local/bin/ && \
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe && \
    rm -rf ffmpeg-* ffmpeg-release-amd64-static.tar.xz

# --------------------------------------------------
# Verify system tools
# --------------------------------------------------
RUN python3 --version
RUN pip3 --version
RUN ffmpeg -version
RUN convert -version

# --------------------------------------------------
# Working directory
# --------------------------------------------------
WORKDIR /app

# --------------------------------------------------
# Node dependencies
# --------------------------------------------------
COPY package.json ./
COPY package-lock.json* ./

RUN npm install

# --------------------------------------------------
# Install Chromium
# --------------------------------------------------
RUN npx playwright install chromium --with-deps

# --------------------------------------------------
# Python dependencies
# --------------------------------------------------
COPY requirements.txt ./

RUN pip3 install --upgrade pip setuptools wheel

RUN pip3 install --no-cache-dir -r requirements.txt

# --------------------------------------------------
# Verify Wand AFTER installation
# --------------------------------------------------
RUN python3 -c "from wand.image import Image; print('Wand OK')"

# --------------------------------------------------
# Copy application
# --------------------------------------------------
COPY . .

# --------------------------------------------------
# Run application
# --------------------------------------------------
CMD ["bash", "-c", "node ./combiners/gifs/main.js & exec python3 main.py"]