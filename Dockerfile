FROM --platform=$BUILDPLATFORM python:3.10
USER root
SHELL ["/bin/bash", "-c"]
RUN mkdir /code
WORKDIR /code
# ARG SITE_NAME
# ENV SITE_NAME=${SITE_NAME}

COPY . /code/

RUN apt-get update && apt-get install python3-pip -y &&\
    pip3 install -U --pre django-globus-portal-framework &&\
    pip3 install drf-yasg &&\
    pip3 install django-allauth &&\
    pip3 install pika &&\
    pip3 install -r requirements.txt


# todo environmental variable for globus key and secret
#ENTRYPOINT  python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000

RUN chmod +x entrypoint.sh
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]