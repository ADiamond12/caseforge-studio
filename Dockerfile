FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN python -m pip install --upgrade pip && \
    python -m pip install .

# The process binds to the container interface. For local-only use, publish with:
# docker run -p 127.0.0.1:8127:8127 ...
EXPOSE 8127

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8127/health', timeout=3).read()"

CMD ["python", "-m", "caseforge", "serve", "--host", "0.0.0.0", "--port", "8127"]
