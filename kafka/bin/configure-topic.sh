#!/bin/bash

/kafka/bin/kafka-configs.sh --zookeeper=$ZOOKEEPER_CONNECT --alter --entity-type=topics $@
