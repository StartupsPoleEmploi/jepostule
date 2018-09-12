#!/bin/bash

/kafka/bin/kafka-topics.sh --zookeeper=$ZOOKEEPER_CONNECT --create --if-not-exists $@
