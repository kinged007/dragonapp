#python:3.10
FROM python:3.10
WORKDIR /app

# Copy your shell script and the rest of your application code into the Docker image
COPY . /app

# Install nano
RUN apt-get update && apt-get install -y nano

# Make the script executable and execute it
RUN chmod +x /app/docker_install.sh && /app/docker_install.sh

# Set the locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

EXPOSE 8080
EXPOSE 4444

# Run app.py when the container launches - MOVED to docker-compose.yml
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "3"]