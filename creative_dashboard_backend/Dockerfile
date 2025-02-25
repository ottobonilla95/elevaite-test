# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install dependencies
# Copy only requirements files first to leverage Docker cache
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create static directory inside the container (if it doesn't exist)
RUN mkdir -p /app/static

# Copy the rest of the application code
COPY . .

# Expose port 8000 (or any port your app uses)
EXPOSE 8000

# Set the command to run the application
CMD ["python", "app/main.py"]
