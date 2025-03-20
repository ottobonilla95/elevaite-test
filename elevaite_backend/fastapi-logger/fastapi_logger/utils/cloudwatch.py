import boto3
import time


def send_log_to_cloudwatch(log: str, log_group: str, log_stream: str) -> None:
    """
    Sends a given log string to AWS CloudWatch Logs.

    Args:
        log (str): The log message to send.
        log_group (str): The name of the CloudWatch log group.
        log_stream (str): The name of the log stream.
    """
    client = boto3.client("logs")

    # Retrieve the upload sequence token for the log stream
    try:
        response = client.describe_log_streams(
            logGroupName=log_group, logStreamNamePrefix=log_stream
        )
        if response["logStreams"]:
            sequence_token = response["logStreams"][0].get("uploadSequenceToken")
        else:
            print("Log stream not found. Please ensure the log stream exists.")
            return
    except Exception as e:
        print("Error retrieving log stream information:", e)
        return

    # Create a log event with the current timestamp (in milliseconds)
    timestamp = int(time.time() * 1000)
    log_event = {"timestamp": timestamp, "message": log}

    # Prepare the parameters for sending the log event
    params = {
        "logGroupName": log_group,
        "logStreamName": log_stream,
        "logEvents": [log_event],
    }
    if sequence_token:
        params["sequenceToken"] = sequence_token

    # Send the log event to CloudWatch
    try:
        result = client.put_log_events(**params)
        print("Log event sent successfully:", result)
    except Exception as e:
        print("Error sending log event:", e)
