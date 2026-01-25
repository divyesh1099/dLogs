# Lightweight Python image to run the dLogs installer/cli
FROM python:3.9-slim

WORKDIR /app

# Copy the package
COPY . .

# Install dependencies and the package itself
RUN pip install .

# By default, run the CLI
ENTRYPOINT ["dlogs-install"]
