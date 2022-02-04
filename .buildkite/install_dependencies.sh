#!/usr/bin/env bash

echo "Installing kafka cli.."

curl -O http://packages.confluent.io/archive/7.0/confluent-7.0.1.tar.gz

tar -xzf confluent-7.0.1.tar.gz && mv confluent-7.0.1 $HOME/kafka/

echo "Installation complete"
