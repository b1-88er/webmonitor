FROM ubuntu:12.04.5

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y python-pip python-dev

WORKDIR app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY webmonitor webmonitor
COPY tests tests

COPY run_tests.sh .
RUN find . -name "*pyc" | xargs rm
