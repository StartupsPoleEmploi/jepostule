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
echo "Kafka is up, let's continue..."

exit
# Consume topics to send mails. Then store its process id in a temporary file.
./manage.py consumetopics all --settings=config.settings.test_e2e &
CONSUMETOPIC_PID=$!
echo $CONSUMETOPIC_PID > e2e_server_pid.txt
echo "Background consumetopic process started with PID $CONSUMETOPIC_PID..."

# Run Django end to end tests without creating a database.
# FIXME This freezes without any output :-(
# ./manage.py test jepostule.tests.end_to_end --settings=config.settings.test_e2e
./manage.py test -v 2 jepostule.tests.end_to_end --settings=config.settings.test_e2e

# ./manage.py test -v 2 jepostule.tests.end_to_end --settings=config.settings.test_e2e
# Skipping setup of unused database(s): TEST.
# System check identified no issues (0 silenced).
# test_candidate_can_apply (jepostule.tests.end_to_end.test_candidate_can_apply.TestCandidateCanApply) ...
# urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='127.0.0.1', port=49850): Max retries exceeded with url: /session/17e2861eb6a9f735da6198aeecbe7c85/element (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x104dc9940>: Failed to establish a new connection: [Errno 61] Connection refused',))
# File "/Users/vermeer/docs/autonomo/lbb/jepostule/jepostule/tests/end_to_end/test_candidate_can_apply.py", line 69, in test_candidate_can_apply
# EC.visibility_of_element_located((By.LINK_TEXT, "C'est parti !"))

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

# Wait for the process to end.
while kill -0 $CONSUMETOPIC_PID 2> /dev/null; do \
    echo 'Waiting for consumetopic background process to quit...'; \
    kill $CONSUMETOPIC_PID
    sleep 2
    # Hard kill if regular kill was not enough, it happens.
    kill -9 $CONSUMETOPIC_PID
    sleep 2; \
done

rm e2e_server_pid.txt

# Delete 'jepostule' group
make delete-kafka-group

# Stop third services and delete containers
make stop
make clean