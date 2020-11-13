FROM ubuntu:18.04

# Environment variables
ENV NODE_VERSION 8.10.0
ENV NPM_VERSION 3.5.2
ENV NVM_DIR /usr/local/nvm
ENV NVM_VERSION 0.34.0
ENV PYTHON_VERSION 3.6.7-1~18.04
ENV PATH /jepostule/node_modules/.bin/:${PATH}
ENV DJANGO_SETTINGS_MODULE config.settings.local
ENV LANG C.UTF-8

RUN apt-get update -y && \
    apt-get install -y  \
        python3=$PYTHON_VERSION \
        python3-pip \
        postgresql-client-common \
        curl \
        npm=$NPM_VERSION-0ubuntu4
RUN ln -s /usr/bin/python3 /usr/local/bin/python
RUN ln -s /usr/bin/pip3 /usr/local/bin/pip

# Install NVM
RUN mkdir $NVM_DIR
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v$NVM_VERSION/install.sh | bash

# Install NodeJS with NVM
RUN /bin/bash -c "source $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm use $NODE_VERSION"

WORKDIR /jepostule

# Install python requirements
COPY ./requirements/ ./requirements/
RUN pip install -r requirements/prod.txt

COPY . /jepostule

# Install frontend requirements
RUN npm install --unsafe-perm

EXPOSE 8000


RUN mkdir -p /var/log/uwsgi
CMD uwsgi --module=config.wsgi:application \
    --master \
    --http=0.0.0.0:8000 \
    --processes=8 \
    --max-requests=5000 \
    --enable-threads \
    --logto /var/log/uwsgi/uwsgi.log \
    --log-date \
    --buffer-size 32000
