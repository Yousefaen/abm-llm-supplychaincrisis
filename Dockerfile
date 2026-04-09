FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Railway sets PORT automatically
ENV PORT=8010
ENV HOST=0.0.0.0

EXPOSE ${PORT}

CMD uvicorn server:app --host 0.0.0.0 --port ${PORT}
