# Use a slim, official Python image for smaller size, better than plain Ubuntu
FROM python:3.11-slim-bookworm

# Set environment variables for the application (useful for debugging and setup)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /usr/src/app

# Install system dependencies needed by the database driver (like PostgreSQL client)
# This is crucial for connecting to the separate database container
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY ./src/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of your application code
COPY ./src .

# Expose the port the application runs on
EXPOSE 8000

# Command to run the Python server (using Gunicorn for production-like hosting)
# NOTE: The command is a placeholder, you would use your actual entrypoint
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]