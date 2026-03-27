FROM python:3.11-slim

# open3d is skipped on linux/aarch64 via environment marker in requirements.txt.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["bash"]
