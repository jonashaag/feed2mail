FROM python:2-alpine

RUN pip install feedparser html2text

COPY feed2mail.py config.py /

ENV SEEN_FILE=/seen/seen

CMD python2 feed2mail.py
