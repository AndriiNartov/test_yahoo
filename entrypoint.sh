#! /bin/bash

#python manage.py makemigrations --no-input
#
#python manage.py migrate --no-input
#
#python manage.py collectstatic --no-input

exec uvicorn db.main:app --host 0.0.0.0 --port 8000 --reload

