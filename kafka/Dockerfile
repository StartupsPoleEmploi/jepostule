FROM openjdk:11-jre-slim

RUN apt update && \
    apt install -y wget curl jq

RUN mkdir /kafka
WORKDIR /kafka

# download kafka
COPY download.sh /kafka
RUN /kafka/download.sh "/kafka/kafka.tgz"
RUN tar xzf /kafka/kafka.tgz --strip-components=1

VOLUME /tmp/kafka-logs

ENV BROKER_ID 0
ENV ZOOKEEPER_CONNECT zookeeper:2181
ENV LISTENERS localhost
EXPOSE 9092
COPY ./bin/create-topics.sh /usr/local/bin/
CMD ./bin/kafka-server-start.sh ./config/server.properties \
    --override broker.id=$BROKER_ID \
    --override zookeeper.connect=$ZOOKEEPER_CONNECT \
    --override advertised.listeners=PLAINTEXT://$LISTENERS:9092
