# Use a standard Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Set the command to run the app, exposing the correct port and address
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
