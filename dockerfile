# Use Python base image
FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

# Install system dependencies


# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Expose port 8000
EXPOSE 8000

# Run migrations and start Django server
CMD ["sh", "-c", "python manage.py migrate && echo 'Migrations applied' && gunicorn --bind 0.0.0.0:8000 movies.wsgi:application"]
