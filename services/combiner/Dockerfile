# 1. Use the official Playwright base image (Node.js + Browser Deps included)
FROM mcr.microsoft.com/playwright:v1.49.0-jammy

# 2. Set environment variables
ENV PYTHONUNBUFFERED=1
# Ensure Playwright looks for browsers in a standard location
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 3. Install Python, FFmpeg, and essential build tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Set working directory
WORKDIR /app

# 5. Handle Node.js dependencies
# We copy package.json first to leverage Docker layer caching
COPY package.json ./
RUN npm install

# 6. Install ONLY the Chromium browser and its system dependencies
# This is the "Use its own" part
RUN npx playwright install chromium --with-deps

# 7. Handle Python dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# 8. Copy the rest of the application
# Ensure your .dockerignore excludes node_modules to avoid conflicts
COPY . .

# 9. Final execution command
# We use bash to orchestrate the parallel execution of your Python and Node services
CMD ["bash", "-c", "python3 main.py & node Main.js"]