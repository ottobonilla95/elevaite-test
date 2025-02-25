import time
import boto3


def get_processing_job_name(step_details: dict) -> str:
    """Extract the processing job name from step details."""
    metadata = step_details.get("Metadata", {})
    return metadata.get("ProcessingJob", {}).get("Arn", "").split("/")[-1]


def get_cloudwatch_logs(job_name: str, start_time=None, end_time=None) -> list:
    """Retrieve CloudWatch logs for a SageMaker processing job."""
    try:
        logs_client = boto3.client("logs")

        # Get the log group and stream
        log_group = f"/aws/sagemaker/ProcessingJobs"

        # Get log streams for this job
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            logStreamNamePrefix=job_name,
            orderBy="LogStreamName",
            limit=1,
        )

        if not streams.get("logStreams"):
            print(f"No log streams found for job {job_name}")
            return []

        log_stream = streams["logStreams"][0]["logStreamName"]

        # Get the logs
        kwargs = {
            "logGroupName": log_group,
            "logStreamName": log_stream,
            "startFromHead": True,
        }

        if start_time:
            kwargs["startTime"] = start_time
        if end_time:
            kwargs["endTime"] = end_time

        logs = []
        while True:
            response = logs_client.get_log_events(**kwargs)
            for event in response["events"]:
                logs.append(event["message"])

            if not response.get("nextForwardToken") or response[
                "nextForwardToken"
            ] == kwargs.get("nextToken"):
                break

            kwargs["nextToken"] = response["nextForwardToken"]

        return logs

    except Exception as e:
        if "AccessDeniedException" in str(e):
            print(
                "⚠️ Unable to fetch CloudWatch logs - Missing permissions. Add CloudWatch Logs permissions to your IAM role."
            )
        else:
            print(f"Error fetching logs: {str(e)}")
        return []


def monitor_pipeline(
    execution_arn: str, poll_interval: int = 30, summarize: bool = False
):
    """
    Monitor a SageMaker pipeline execution until completion.

    If summarize is False (default), detailed information is printed to stdout.
    If summarize is True, key summary information is accumulated and returned as a dict.

    Args:
        execution_arn: The ARN of the pipeline execution.
        poll_interval: Time in seconds between status checks (default: 30).
        summarize: Whether to accumulate a structured summary instead of printing details.

    Returns:
        If summarize is False: The final pipeline execution status as a string.
        If summarize is True: A dictionary containing the pipeline execution summary.
    """
    client = boto3.client("sagemaker")

    if summarize:
        summary = {
            "execution_arn": execution_arn,
            "poll_interval": poll_interval,
            "current_status": None,
            "final_status": None,
            "steps": {},
        }
    else:
        print(f"Monitoring pipeline execution: {execution_arn}")

    # Track steps we've seen fail to avoid duplicate log processing
    failed_steps_processed = set()

    while True:
        response = client.describe_pipeline_execution(
            PipelineExecutionArn=execution_arn
        )
        status = response.get("PipelineExecutionStatus")

        if summarize:
            summary["current_status"] = status
        else:
            print(f"\nCurrent pipeline status: {status}")

        steps_response = client.list_pipeline_execution_steps(
            PipelineExecutionArn=execution_arn
        )

        for step in steps_response.get("PipelineExecutionSteps", []):
            step_name = step.get("StepName")
            step_status = step.get("StepStatus")

            if summarize:
                step_summary = summary["steps"].get(step_name, {"step_name": step_name})
                step_summary["status"] = step_status
                summary["steps"][step_name] = step_summary
            else:
                # Display basic step information
                status_symbol = (
                    "✅"
                    if step_status == "Succeeded"
                    else "❌" if step_status == "Failed" else "⏳"
                )
                print(f"{status_symbol} Step '{step_name}' - Status: {step_status}")

            if step_status == "Failed" and step_name not in failed_steps_processed:
                failed_steps_processed.add(step_name)
                failure_reason = step.get("FailureReason", "No failure reason provided")

                if summarize:
                    summary["steps"][step_name]["failure_reason"] = failure_reason
                    job_name = get_processing_job_name(step)
                    if job_name:
                        logs = get_cloudwatch_logs(job_name)
                        if logs:
                            relevant_logs = logs[-50:] if len(logs) > 50 else logs
                            summary["steps"][step_name]["logs"] = relevant_logs
                        else:
                            summary["steps"][step_name]["logs"] = [
                                "No logs available or insufficient permissions"
                            ]
                else:
                    print(f"\n🔍 Detailed failure information for step '{step_name}':")
                    print(f"Failure reason: {failure_reason}")

                    job_name = get_processing_job_name(step)
                    if job_name:
                        print(f"\n📋 CloudWatch Logs for job '{job_name}':")
                        logs = get_cloudwatch_logs(job_name)
                        if logs:
                            relevant_logs = logs[-50:] if len(logs) > 50 else logs
                            print("\nLast log entries before failure:")
                            for log in relevant_logs:
                                print(f"    {log}")
                        else:
                            print("    No logs available or insufficient permissions")
                    print("\n" + "=" * 80 + "\n")

        if status in ["Succeeded", "Failed", "Stopped"]:
            break

        time.sleep(poll_interval)

    if summarize:
        summary["final_status"] = status
        summary["steps"] = list(summary["steps"].values())
        return summary
    else:
        print(f"\n🏁 Pipeline execution finished with status: {status}")
        return status
