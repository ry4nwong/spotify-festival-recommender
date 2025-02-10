# Base image
FROM python:3.13

# Set working directory
WORKDIR /backend

# Install dependencies
COPY requirements.txt /backend/
RUN pip install --upgrade pip
RUN pip install -r /backend/requirements.txt

### Install CHROMIUM-DRIVER, MIGHT NEED TO CHANGE ###
RUN apt-get update && apt-get install -y chromium-driver 

# Copy project files
COPY . /backend/

# Expose port
EXPOSE 8000

# Start App
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--reload", "--port", "8000"]

