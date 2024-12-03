# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . /app/

# Set environment variables for Flask
ENV FLASK_APP=app:create_app()
ENV FLASK_RUN_HOST=0.0.0.0

# Expose the port Flask runs on
EXPOSE 5000

# Command to start the Flask app
CMD ["flask", "run"]
