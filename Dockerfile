FROM python:3.11-slim

# ffmpeg o‘rnatish
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Ishchi papka
WORKDIR /app

# Python kutubxonalarini o‘rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kodingni container ichiga nusxalash
COPY . .

# Botni ishga tushirish
CMD ["python", "botTaxi.py"]
