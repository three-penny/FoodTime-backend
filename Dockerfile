FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir gunicorn==23.0.0

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/canteen_img data/stall_img data/dish_img data/submission_img data/default_img instance

EXPOSE 5000

ENV APP_ENV=production
ENV FLASK_RUN_HOST=0.0.0.0

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/ping')" || exit 1

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
