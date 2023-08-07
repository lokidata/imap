FROM python:alpine

LABEL Maintainer="lokidata"

RUN pip install schedule

RUN mkdir -p /app && mkdir -p /config

WORKDIR /app

COPY imap.py ./
COPY config.json ./

VOLUME [ "/config" ]

CMD [ "python", "./imap.py"]