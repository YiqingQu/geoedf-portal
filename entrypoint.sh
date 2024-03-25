#!/bin/bash
python3 manage.py makemigrations
python3 manage.py migrate

if ! [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  export DJANGO_SUPERUSER_USERNAME=admin
  export DJANGO_SUPERUSER_EMAIL=default@email.com
  export DJANGO_SUPERUSER_PASSWORD=defaultpswd
fi

python manage.py createsuperuser \
  --noinput \
  --username $DJANGO_SUPERUSER_USERNAME \
  --email $DJANGO_SUPERUSER_EMAIL

python3 manage.py runserver 0.0.0.0:8000

exec "$@"
