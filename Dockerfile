FROM python:alpine

ENV APP /app
ENV PYTHONPATH .
WORKDIR $APP

RUN apk add --no-cache gcc \
                       make \
                       musl-dev

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY /app $APP

CMD ["python", "main.py"]