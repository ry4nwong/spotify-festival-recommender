# Base image
FROM python:3.13

# Set working directory
WORKDIR /llm

# Install dependencies
COPY requirements.txt /llm/
RUN pip install --upgrade pip
RUN pip install -r /llm/requirements.txt

# Copy project files
COPY . /llm/

# Copy shared folder
COPY shared /shared

# Cross-folder imports
ENV PYTHONPATH="/backend"

# Set environment variables for Flask
ENV FLASK_APP=app:create_app()
ENV FLASK_RUN_HOST=0.0.0.0

# Expose the port Flask runs on
EXPOSE 5000

# Command to start the Flask app
CMD ["flask", "run"]
