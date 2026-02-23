# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables for non-interactive commands and Python behavior
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# --- Core Dependency Installation Phase (OS Level) ---

# Install Git (required by ragatouille/ColBERT metadata)
RUN apt-get update && apt-get install -y git

# **NEW LINE:** Install C/C++ compiler and build tools (required to compile ColBERT's segmented_maxsim.cpp)
RUN apt-get update && apt-get install -y build-essential

# --- Python Dependency Installation Phase (Leverages Caching) ---

# Copy requirements file to a temporary location
COPY requirements.txt /tmp/requirements.txt

# Install packages
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Clean up temporary file
RUN rm /tmp/requirements.txt

# --- Application Copy Phase ---

# Copy the core source code and configuration files
# The destination paths mirror your project structure starting from /app
COPY src /app/src
COPY config.json /app/
COPY README.md /app/

# Copy data and static assets
COPY data /app/data
COPY static /app/static

# Expose the port on which the app will run
EXPOSE 8000

# Run the uvicorn server. The path 'src.chatApp.main:app' uses Python dot notation
# to find the 'app' instance inside 'main.py' within the 'chatApp' sub-package of 'src'.
CMD ["uvicorn", "src.chatApp.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]