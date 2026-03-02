FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

COPY src/ ./src/

# Copy configuration files from build context
RUN mkdir -p /root/.config/cora
COPY .docker_stage/modal.toml /root/.modal.toml
COPY .docker_stage/config.yaml /root/.config/cora/config.yaml

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.fastapi.app:app", "--host", "0.0.0.0", "--port", "8000"]
