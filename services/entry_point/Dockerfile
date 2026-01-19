# Base image
FROM alpine:3.18

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install only the bare essentials for Python and Discord.py
RUN apk add --no-cache \
    bash \
    python3 \
    py3-pip \
    libffi-dev \
    && python3 -m ensurepip \
    && pip3 install --upgrade pip

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Default command
CMD ["python3", "main.py"]