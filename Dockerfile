FROM nvidia/cuda:12.2.2-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir -e .

EXPOSE 7860 8000

ENV MODEL_SIZE="large-v3-turbo"
ENV COMPUTE_TYPE="float16"

CMD ["sh", "-c", "python3 -m interfaces.web.app & python3 -m uvicorn interfaces.api.server:app --host 0.0.0.0 --port 8000"]
