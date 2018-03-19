FROM python:2.7
MAINTAINER dan.leehr@duke.edu

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
ADD . /app/

# Set the django settings module to our production settings file
ENV DJANGO_SETTINGS_MODULE bespin.settings_prod

# Ensure TMP is set, workaround for https://github.com/common-workflow-language/schema_salad/issues/158
ENV TMP /tmp

WORKDIR /app/

# Collect static files.
ENV BESPIN_STATIC_ROOT /srv/static
RUN mkdir -p ${BESPIN_STATIC_ROOT}
RUN BESPIN_SECRET_KEY=DUMMY python manage.py collectstatic --noinput

EXPOSE 8000

CMD gunicorn -b 0.0.0.0:8000 bespin.wsgi:application
