FROM python:3.10

WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your code
COPY . .

# Expose port 7860 (Hugging Face expects this)
EXPOSE 7860

# Set environment variable for model name (can be defaulted or overridden in Spaces UI)
ENV MODEL all-MiniLM-L12-v2

# Start FastAPI app
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
