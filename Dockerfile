FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest
COPY . .

RUN chmod +x scripts/*.sh

CMD ["./scripts/run_evaluation.sh"]
