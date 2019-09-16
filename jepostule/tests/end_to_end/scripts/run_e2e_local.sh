#!/bin/bash

export INSPECT_KAFKA_CONSUMERS="docker-compose exec kafka bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group jepostule"

# Start Postgres, Redis and Kafka
make services

# Delete jepostule group just in case it already exists. Do not display an error message.
docker-compose exec kafka bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --delete --group jepostule > /dev/null

# Create a test database and run migrations.
# We can't use DB created automatically by Django
# as we need Kafka to access it.
docker-compose exec postgres createdb test_jepostule -U jepostule
./manage.py migrate --settings=config.settings.test_e2e

# Wait for Kafka to be up.
until $INSPECT_KAFKA_CONSUMERS | grep -q "Consumer group 'jepostule' does not exist.";\
do \
  sleep 5; \
  echo "Waiting for Kafka to be up...";\
done

# Consume topics to send mails. Then store its process id in a temporary file.
{ nohup ./manage.py consumetopics all --settings=config.settings.test_e2e & echo $! > e2e_server_pid.txt; }

# Run Django end to end tests without creating a database.
./manage.py test jepostule.tests.end_to_end --settings=config.settings.test_e2e

# Inspect Kafka topics
$INSPECT_KAFKA_CONSUMERS
# It should show something like that (make sure current_offset and log_end_offset are equal):
# TOPIC               PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG   CONSUMER-ID     HOST            CLIENT-ID
# send-answer         0          3               3               0     kafka-python-id /172.21.0.1     kafka-python-1.4.6
# send-confirmation   0          1               1               0     kafka-python-id /172.21.0.1     kafka-python-1.4.6
# send-application    0          1               1               0     kafka-python-id /172.21.0.1     kafka-python-1.4.6
# forward-to-memo     0          1               1               0     kafka-python-id /172.21.0.1     kafka-python-1.4.6
# forward-to-ami      0          1               1               0     kafka-python-id /172.21.0.1     kafka-python-1.4.6
# process-email-event 0          -               0               -     kafka-python-id /172.21.0.1     kafka-python-1.4.6


# Kill `consumetopics` process. Only works with -9.
# Theoretically we should use -2 (equals to ctrl +C)
# but theory is for fairy tales, and we live in the real world.
kill -9 `cat e2e_server_pid.txt`

# Wait for the process to end.
while kill -0 `cat e2e_server_pid.txt` 2> /dev/null; do \
    sleep 1; \
    echo 'Waiting for Consumers to quit...'; \
done

rm e2e_server_pid.txt

# Delete 'jepostule' group
make delete-kafka-group

# Stop third services and delete containers
make stop
make clean