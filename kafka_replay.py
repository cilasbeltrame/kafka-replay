import boto3
import base64
from botocore.exceptions import ClientError
import os
import subprocess
import json
import argparse


def run_command(command, error_msg):
    ret = subprocess.call(command)
    if ret > 0:
        exit(error_msg)


def get_bk_metadata(key: str):
    env_key = os.environ.get(key.upper().replace("-", "_"))
    if env_key:
        return env_key

    run_command(['buildkite-agent', 'meta-data', 'exists', key],
                "Buildkite key missing, make sure all inputs are filled in. Missing key: " + key)
    val = subprocess.check_output(
        ['buildkite-agent', 'meta-data', 'get', key]).decode('ascii')
    return val

# APP_ENV= os.environ.get('APP_ENV','')


APP_ENV = get_bk_metadata("env")

if APP_ENV == "qa":
    bootstrap_server = "change_me:9092"
elif APP_ENV == "staging":
    bootstrap_server = "change_me:9092"
elif APP_ENV == "prod" or APP_ENV == "production":
    bootstrap_server = "change_me:9092"    
else:
    print("invalid environment")
CMD = "/root/kafka/bin/kafka-consumer-groups"

# Create a Secrets Manager client


def get_secret():
    if APP_ENV == "prod" or APP_ENV == "production":
        secret_name = "kafka-replay-production"
    secret_name = f"kafka-replay-{APP_ENV}"
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS key.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = json.loads(get_secret_value_response['SecretString'])
            kafka_api_key = secret['KAFKA_API_KEY']
            kafka_api_secret = secret['KAFKA_API_SECRET']
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response['SecretBinary'])
    return kafka_api_key, kafka_api_secret

# Create kafka flle properties


def write_kafka_properties():
    kafka_api_key = get_secret()[0]
    kafka_api_secret = get_secret()[1]
    kafka_properties_file = f"""
bootstrap.servers={bootstrap_server}
ssl.endpoint.identification.algorithm=https
security.protocol=SASL_SSL
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="{kafka_api_key}" password="{kafka_api_secret}";
request.timeout.ms=30000
"""
    with open(f"{APP_ENV}.properties", "a") as f:
        f.write(kafka_properties_file)


# Parse command to execute dry-run and execute for kafka cli


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action='store_true',
                        help="Runs kafka reset-offsets as dry run")
    parser.add_argument('-e', action='store_true',
                        help="Runs kafka reset-offset execution")
    args = parser.parse_args()

    print("Getting kafka secrets..")

    write_kafka_properties()

    # get input from the user
    datetime = get_bk_metadata("datetime")
    topics = get_bk_metadata("topics")
    consumer_group = get_bk_metadata("consumer-group")

    # Execute  dry-run or reset for each topic passed
    for topic in topics.split(","):
        if args.d is True:
            run_command([CMD,
                         "--command-config",
                         f'{APP_ENV}.properties',
                         "--bootstrap-server",
                         bootstrap_server,
                         "--topic",
                         topic.strip(),
                         "--group",
                         consumer_group,
                         "--reset-offsets",
                         "--to-datetime",
                         datetime,
                         "--dry-run"], "Please review your topics, consumer group and datetime")
        elif args.e is True:
            run_command([CMD,
                         "--command-config",
                         f'{APP_ENV}.properties',
                         "--bootstrap-server",
                         bootstrap_server,
                         "--topic",
                         topic.strip(),
                         "--group",
                         consumer_group,
                         "--reset-offsets",
                         "--to-datetime",
                         datetime,
                         "--execute"], "Please review your topics, consumer group and datetime")
        else:
            print("No args passed. Exiting")
            exit(1)
    if args.e is True:
        print("#######################################")
        print("Kafka replay complete")
        print("#######################################")


if __name__ == "__main__":
    run()
