FROM python:alpine

RUN apk add --no-cache gcc \
                       make \
                       musl-dev

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY app /app
ENV PYTHONPATH .

CMD ["python", "/app/main.py"]