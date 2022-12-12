FROM python:3.10
USER root
SHELL ["/bin/bash", "-c"]
RUN mkdir /code
WORKDIR /code
ARG SITE_NAME
ENV SITE_NAME=${SITE_NAME}

RUN apt-get update && apt-get install python3 -y && apt-get install python3-pip -y &&\
    pip3 install -U --pre django-globus-portal-framework

COPY . /code/
RUN   python3 manage.py migrate
EXPOSE 8000
# todo environmental variable for globus key and secret
ENTRYPOINT  python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000