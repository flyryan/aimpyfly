FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy aimpyfly package and install it
COPY aimpyfly/ /app/aimpyfly/
COPY setup.py README.md ./
RUN pip install -e .

# Copy the rest of the application
COPY aimbot/ /app/aimbot/

# Set Python path to include the application
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "-m", "aimbot.main"]
