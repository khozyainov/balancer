FROM python:alpine

RUN apk add --no-cache gcc \
                       make \
                       musl-dev

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY app /app/app
WORKDIR /app
ENV PYTHONPATH .

CMD ["pytest", "-vv", "-s"]