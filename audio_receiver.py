
import boto3
import json
import time
import requests
import symbl
from datetime import datetime, timedelta
from botocore.config import Config

# Configure boto3 client
config = Config(
    retries = dict(
        max_attempts = 10
    )
)

kinesis_client = boto3.client('kinesis', config=config)

# Stream details
stream_name = 'symblai-kinesis-data-stream' # Replace with your stream name
consumer_name = 'my-local-consumer'

connection_object = None

def register_consumer():
    try:
        response = kinesis_client.register_stream_consumer(
            StreamARN=get_stream_arn(stream_name),
            ConsumerName=consumer_name
        )
        print(f"Consumer {consumer_name} registered successfully.")
        return response['Consumer']['ConsumerARN']
    except kinesis_client.exceptions.ResourceInUseException:
        print(f"Consumer {consumer_name} already exists.")
        return get_consumer_arn()

def get_stream_arn(stream_name):
    response = kinesis_client.describe_stream(StreamName=stream_name)
    return response['StreamDescription']['StreamARN']

def get_consumer_arn():
    response = kinesis_client.describe_stream_consumer(
        StreamARN=get_stream_arn(stream_name),
        ConsumerName=consumer_name
    )
    return response['ConsumerDescription']['ConsumerARN']

def handle_tracker_response(connection_object, tracker_response):

    # tracker_name = tracker_response['trackers'][0]['name']
    tracker_value = tracker_response['trackers'][0]['matches'][0]['value']
    # tracker_transcript = tracker_response['trackers'][0]['matches'][0]['messageRefs'][0]['text']

    conversation_message = '\n'.join([x.text for x in connection_object.conversation.get_messages().messages])

    from utils import vector_index_search, get_nebula_response
    relevant_info = vector_index_search(tracker_value)['data']

    get_nebula_response(conversation_message, relevant_info)

def get_troubleshooting_tracker():
    from utils import generate_token
    troubleshooting_tracker_url = f"https://api.symbl.ai/v1/manage/trackers?name={requests.utils.quote('Troubleshooting Tracker')}"

    headers = {
        'Authorization': f'Bearer {generate_token()}'
    }
    response = requests.request("GET", troubleshooting_tracker_url, headers=headers)
    troubleshooting_tracker = json.loads(response.text)['trackers']
    return troubleshooting_tracker

def main():
    consumer_arn = register_consumer()

    shard_id = input('Give shardId: ')
    starting_sequence_number = input('Give starting sequence number: ')

    shard_iterator = kinesis_client.get_shard_iterator(
        StreamName=stream_name,
        ShardId=shard_id,
        ShardIteratorType='AT_SEQUENCE_NUMBER',
        StartingSequenceNumber=starting_sequence_number
    )['ShardIterator']

    response = kinesis_client.get_records(ShardIterator=shard_iterator, Limit=2000)

    trackers = get_troubleshooting_tracker()

    connection_object = symbl.Streaming.start_connection(trackers=trackers)

    events = {
        'tracker_response': lambda tracker: handle_tracker_response(connection_object, tracker)
    }

    connection_object.subscribe(events)

    time.sleep(5)

    for record in response['Records']:
        connection_object.send_audio(record['Data'])

if __name__ == "__main__":
    main()

