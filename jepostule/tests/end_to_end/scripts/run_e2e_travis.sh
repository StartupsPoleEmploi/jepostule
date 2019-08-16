#!/bin/bash

export INSPECT_KAFKA_CONSUMERS="docker-compose exec kafka bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group jepostule"

make build-kafka
KAFKA_LISTENERS=localhost docker-compose up --detach kafka
./manage.py migrate --settings=config.settings.test_e2e

until $INSPECT_KAFKA_CONSUMERS | grep "Consumer group 'jepostule' does not exist.";\
do \
  sleep 5; \
  echo "Waiting for Kafka to be up...";\
done

{ nohup ./manage.py consumetopics all --settings=config.settings.test_e2e & echo $! > e2e_server_pid.txt; }
./manage.py test jepostule.tests.end_to_end --settings=config.settings.test_e2e
$INSPECT_KAFKA_CONSUMERS