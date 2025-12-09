FROM python:3.11-slim AS builder

WORKDIR /app

# Create virtual env so we can copy only dependencies to final image
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Make pip faster and avoid external configs enforcing hashes
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_COLOR=1 \
    PIP_REQUIRE_HASHES=0

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy dependencies from builder layer
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]