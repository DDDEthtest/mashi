# 1. Use Playwright as the base (provides Node + Browser deps)
FROM mcr.microsoft.com/playwright:v1.49.0-jammy

# 2. Environment Setup
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# Ensure python3 is the default 'python'
RUN ln -s /usr/bin/python3 /usr/bin/python

# 3. Combined System Dependencies
# We include the OpenGL libs from your 2nd Dockerfile (libgl1, libglib2.0-0)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ffmpeg \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 4. Handle Node.js Dependencies
COPY package.json ./
RUN npm install

# 5. Install Chromium for Playwright
RUN npx playwright install chromium --with-deps

# 6. Handle Python Dependencies (Merged logic)
COPY requirements.txt ./
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# 7. Copy Application Code
COPY . .

# 8. Execution
# Orchestrating both services
CMD ["bash", "-c", "python3 main.py & node Main.js"]