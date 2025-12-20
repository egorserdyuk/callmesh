FROM python:3.14-alpine

WORKDIR /app

# Installing system dependencies
RUN apk update && apk add --no-cache --virtual .build-deps \
    postgresql-dev \
    gcc \
    musl-dev \
    python3-dev \
    gettext \
    vim && \
    apk add --no-cache \
    postgresql-client && \
    rm -rf /var/cache/apk/*

# Copying and installing Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Additionally, install daphne if it is not in requirements.txt.
RUN pip install --no-cache-dir daphne

# Creating an unprivileged user with a specific UID/GID
RUN addgroup -r appuser -g 1000 && adduser -r -g appuser -u 1000 appuser

# Copying the source code
COPY . .

# Creating directories for static files, media, and logs with the correct permissions
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/logs

# Switch to unprivileged user
USER appuser

EXPOSE 8000

# Default command - launch via daphne to support WebSocket
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "videocall_app.asgi:application"]
