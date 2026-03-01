FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml ./
COPY uv.lock ./

RUN uv sync --frozen --no-dev

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY . .

# Copy Modal credentials (requires: cp ~/.modal.toml ./modal.toml before building)
COPY modal.toml /root/.modal.toml

# Copy config file (requires: cp ~/.config/cora/config.yaml ./.config/cora.yaml before building)
COPY .config/cora.yaml /root/.config/cora/config.yaml

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.fastapi.app:app", "--host", "0.0.0.0", "--port", "8000"]
