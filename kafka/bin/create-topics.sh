#!/bin/bash

# send-application: 5 days retention, 11 Mb messages
/kafka/bin/kafka-topics.sh --zookeeper=$ZOOKEEPER_CONNECT --create --if-not-exists \
		--partitions=1 --replication-factor=1 --topic=send-application
/kafka/bin/kafka-configs.sh --zookeeper=$ZOOKEEPER_CONNECT --alter --entity-type=topics \
    --entity-name=send-application --add-config 'cleanup.policy=delete,retention.ms=432000000,max.message.bytes=11534336'

# send-confirmation: 5 days retention, 1 Mb messages
/kafka/bin/kafka-topics.sh --zookeeper=$ZOOKEEPER_CONNECT --create --if-not-exists \
    --partitions=1 --replication-factor=1 --topic=send-confirmation
/kafka/bin/kafka-configs.sh --zookeeper=$ZOOKEEPER_CONNECT --alter --entity-type=topics \
    --entity-name=send-confirmation --add-config 'cleanup.policy=delete,retention.ms=432000000,max.message.bytes=1048576'

# send-answer: 5 days retention, 1 Mb messages
/kafka/bin/kafka-topics.sh --zookeeper=$ZOOKEEPER_CONNECT --create --if-not-exists \
    --partitions=1 --replication-factor=1 --topic=send-answer
/kafka/bin/kafka-configs.sh --zookeeper=$ZOOKEEPER_CONNECT --alter --entity-type=topics \
    --entity-name=send-answer --add-config 'cleanup.policy=delete,retention.ms=432000000,max.message.bytes=1048576'
