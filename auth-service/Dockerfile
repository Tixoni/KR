FROM python:3.11-slim AS builder

WORKDIR /app

# Create virtual env so we can copy only dependencies to final image
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy dependencies from builder layer
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]