FROM ubuntu:18.04

RUN apt update -y && \
    apt install -y python3 python3-pip postgresql-client-common npm
RUN ln -s /usr/bin/python3 /usr/local/bin/python
RUN ln -s /usr/bin/pip3 /usr/local/bin/pip

WORKDIR /jepostule

# Install python requirements
COPY ./requirements/ ./requirements/
RUN pip install -r requirements/prod.txt

# Install node requirements
COPY ./package.json .
RUN mkdir -p ./jepostule/static/vendor
RUN npm install --unsafe-perm

COPY . /jepostule
ENV PATH /jepostule/node_modules/.bin/:${PATH}
ENV DJANGO_SETTINGS_MODULE config.settings.local
ENV LANG C.UTF-8
EXPOSE 8000

RUN mkdir -p /var/log/uwsgi
CMD uwsgi --module=config.wsgi:application \
    --master \
    --http=0.0.0.0:8000 \
    --processes=8 \
    --max-requests=5000 \
    --enable-threads \
    --logto /var/log/uwsgi/uwsgi.log \
    --log-date
