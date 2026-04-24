FROM python:3.10

RUN apt update && apt install -y chromium chromium-driver

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "uy.py"]
