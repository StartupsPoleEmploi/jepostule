FROM ubuntu:18.04

RUN apt update -y && \
    apt install -y python3 python3-pip postgresql-client-common npm
RUN ln -s /usr/bin/python3 /usr/local/bin/python
RUN ln -s /usr/bin/pip3 /usr/local/bin/pip

COPY . /jepostule
WORKDIR /jepostule

RUN pip install -r requirements/prod.txt
RUN npm install

ENV PATH /jepostule/node_modules/.bin/:${PATH}
ENV DJANGO_SETTINGS_MODULE config.settings.local
EXPOSE 8000

RUN rm -rf static/ && ./manage.py collectstatic --no-input
VOLUME /jepostule/static

CMD uwsgi --module=config.wsgi:application \
    --master \
    --http=0.0.0.0:8000 \
    --processes=8 \
    --max-requests=5000 \
    --enable-threads
