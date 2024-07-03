import boto3
import time
import wave

# Initialize AWS client
kinesis_client = boto3.client('kinesis')

def stream_audio_to_kinesis(audio_file, stream_name, chunk_size=8192):
    first_record_response = None
    with open(audio_file, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            x = kinesis_client.put_record(
                    StreamName=stream_name,
                    Data=data,
                    PartitionKey='partitionkey'
                )
            
            if not first_record_response:
                first_record_response = x
    return first_record_response

if __name__ == "__main__":
    input_audio = ['in1.wav', 'in2.wav', 'in3.wav', 'in4.wav']

    for in_aud in input_audio:
        audio_file = 'live-call-simulation-audio/' + in_aud
        kinesis_stream_name = 'symblai-kinesis-data-stream' # Replace with your stream name
        
        print(f"Streaming audio from {audio_file} to Kinesis stream {kinesis_stream_name}")
        first_record_response = stream_audio_to_kinesis(audio_file, kinesis_stream_name)
        print(first_record_response)
        print("Streaming completed")

"""
'Put' response is in following format. Store the ShardId and SequenceNumber from the first response, for use with audio_receiver.py.
{'ShardId': 'shardId-000000000003', 'SequenceNumber': '49653162392223642107452695523079917107329531761712431154', 'ResponseMetadata': {'RequestId': 'f8d41ddd-e71d-62f1-a62a-248bcdf7aa96', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'f8d41ddd-e71d-62f1-a62a-248bcdf7aa96', 'x-amz-id-2': 'Dw+MW+WMYzDDD/T0hxU4VeCxT1DAb1Lw/JYrnYW7aaZmDOzRk5iZe2XcMHNxPWNq7sJwEHiJn5by09qZS6xEJOv5N9gM7yln', 'date': 'Tue, 02 Jul 2024 17:21:26 GMT', 'content-type': 'application/x-amz-json-1.1', 'content-length': '110', 'connection': 'keep-alive'}, 'RetryAttempts': 0}}
"""