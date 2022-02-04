# Kafka Replay

Pipeline created to run kafka replay (Reset offsets).

In a nutshell this pipeline get the kafka api keys from Secret Manager (AWS), and do the dry-run/ reset offset in Confluent Cloud.

Once you the trigger a build of the pipeline, following input will be asked:

1. `env`:  The environment to do the kafka replay (reset offset)
2. `Consumer-group`: the kafka consumer group to do the replay (reset offset)
3. `Topics`: Comma delimited topics to do the replay
4. `Datetime`: Datetime that you would like to set the offsets. Format: 'YYYY-MM-DDTHH:mm:SS.sss' use UTC timezone

The buildkite pipeline wil give you a dry-run option before execute the kafka reset.

Example of a dry-run command: `kafka-consumer-groups --command-config qa.properties --bootstrap-server bootstrap.url:9092 --group app-consumer-group --topic topic1,topic2 --reset-offsets --to-datetime "2022-01-25T05:00:00.000 --dry-run"`

Example of a execute command (reset the offsets properly): `kafka-consumer-groups --command-config qa.properties --bootstrap-server bootstrap.url:9092 --group app-consumer-group --topic topic1,topic2 --reset-offsets --to-datetime "2022-01-25T05:00:00.000 --execute"`

## Notes

1. Since it is used Confluent Kafka managed service, we have one of the latest kafka version, it is not necessary to pass each partition of the topics to do the replay, the kafka/command will figure out automatically.

2. Keep the `datetime` input within 7 days, that is the maximum(default) retention period for kafka messages.(This is configurable)
