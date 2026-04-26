# 1. Base image (Node + Playwright deps)
FROM mcr.microsoft.com/playwright:v1.49.0-jammy

# 2. Environment
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Ensure python3 is default
RUN ln -sf /usr/bin/python3 /usr/bin/python

# 3. System dependencies (WITHOUT old ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libpq-dev \
    wget \
    xz-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Install modern FFmpeg (6.x static build)
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar -xvf ffmpeg-release-amd64-static.tar.xz && \
    cp ffmpeg-*/ffmpeg /usr/local/bin/ && \
    cp ffmpeg-*/ffprobe /usr/local/bin/ && \
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe && \
    rm -rf ffmpeg-* ffmpeg-release-amd64-static.tar.xz

# 5. Set working dir
WORKDIR /app

# 6. Node dependencies
COPY package.json ./
RUN npm install

# 7. Install Chromium
RUN npx playwright install chromium --with-deps

# 8. Python dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# 9. Copy app
COPY . .

# 10. Run both services (proper process handling)
CMD ["bash", "-c", "node ./combiners/gifs/main.js & exec python3 main.py"]