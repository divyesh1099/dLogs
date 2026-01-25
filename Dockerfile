FROM python:3.11-slim

# Install docker CLI (so container can control host docker via socket mount)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy package
COPY . /app

RUN pip install --no-cache-dir .

ENTRYPOINT ["dlogs"]
CMD ["--help"]
