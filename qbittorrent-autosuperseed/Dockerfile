# Use an official Python runtime as a base image

# Specific image
# FROM python:3.9-slim-buster

# Latest within version
# FROM python:3

# Latest for specific distibution
# FROM python:slim

# Latest
# FROM python:latest

# Use latest slim
FROM python:slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the working directory
COPY qbt_super_seed.py .

# Command to run the Python script when the container starts
CMD ["python", "-u", "qbt_super_seed.py"]
