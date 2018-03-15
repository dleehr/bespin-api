ARG BASE_IMAGE
FROM ${BASE_IMAGE}
MAINTAINER dan.leehr@duke.edu

RUN apt-get update && apt-get install -y \
  apache2 \
  libapache2-mod-wsgi

# Globally set DJANGO_SETTINGS_MODULE to settings_prod so we don't have to override it individually
ENV DJANGO_SETTINGS_MODULE bespin.settings_prod
ENV BESPIN_STATIC_ROOT /srv/static

RUN mkdir -p ${BESPIN_STATIC_ROOT}

# Collect the static files

# BESPIN_SECRET_KEY must be set for any manage.py tasks
# So we set it to a dummy value to run collectstatic, even though it is not used
RUN BESPIN_SECRET_KEY=DUMMY python manage.py collectstatic --noinput

COPY bespin-web.conf /etc/apache2/sites-available/
COPY ports.conf /etc/apache2/ports.conf

RUN a2ensite bespin-web
RUN a2dissite 000-default
RUN a2enmod rewrite
RUN a2enmod ssl
RUN a2disconf other-vhosts-access-log

COPY scripts /scripts

# Mark /srv/ui as a volume

VOLUME /srv/ui
COPY index.html /srv/ui/index.html

EXPOSE 8080
EXPOSE 8443

# Add /scripts to the PATH
ENV PATH ${PATH}:/scripts/

# Ensure TMP is set, workaround for https://github.com/common-workflow-language/schema_salad/issues/158
ENV TMP /tmp

# set the command to start apache
ENTRYPOINT ["/scripts/wait-for-postgres.sh"]
CMD ["/scripts/start-apache.sh"]
