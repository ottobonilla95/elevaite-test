from datetime import datetime
import time
from typing import Any, Dict, List
import boto3


def tail_cloudwatch_logs(job_name: str, poll_interval: int = 5):
    """
    Continuously poll and print CloudWatch logs for a SageMaker processing job.

    Args:
        job_name: The name of the SageMaker processing job.
        poll_interval: Seconds between log fetches (default: 5 seconds).
    """
    logs_client = boto3.client("logs")
    log_group = "/aws/sagemaker/ProcessingJobs"

    streams = logs_client.describe_log_streams(
        logGroupName=log_group,
        logStreamNamePrefix=job_name,
        orderBy="LogStreamName",
        limit=1,
    )

    if not streams.get("logStreams"):
        print(f"No log streams found for job {job_name}")
        return

    log_stream = streams["logStreams"][0]["logStreamName"]
    print(f"Tail logs for job '{job_name}' on stream '{log_stream}'")

    next_token = None

    try:
        while True:
            kwargs = {
                "logGroupName": log_group,
                "logStreamName": log_stream,
                "startFromHead": True,
            }
            if next_token:
                kwargs["nextToken"] = next_token

            response = logs_client.get_log_events(**kwargs)
            events = response.get("events", [])
            if events:
                for event in events:
                    print(event["message"])
            else:
                pass

            new_token = response.get("nextForwardToken")
            if new_token == next_token:
                time.sleep(poll_interval)
            else:
                next_token = new_token
    except KeyboardInterrupt:
        print("Stopped tailing logs.")


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
    execution_arn: str,
    poll_interval: int = 30,
    summarize: bool = False,
    is_bedrock: bool = False,
) -> List[str]:
    """
    Monitor a pipeline execution until completion.

    For SageMaker pipelines (is_bedrock=False), it uses SageMaker API calls to monitor detailed step status.
    For Bedrock (Step Functions) pipelines (is_bedrock=True), it uses Step Functions API to monitor detailed step-by-step events.

    Args:
        execution_arn: The ARN of the pipeline execution.
        poll_interval: Time in seconds between status checks (default: 30).
        summarize: If True, accumulate a structured summary.
        is_bedrock: If True, use Step Functions (Bedrock) monitoring logic.

    Returns:
        A list of log messages (as strings). If summarize is True, the final summary dict is converted
        to a string and returned as a single-element list.
    """
    logs: List[str] = []

    def log_message(message: str) -> None:
        logs.append(message)

    summary: Dict[str, Any] = {}

    if is_bedrock:
        client = boto3.client("stepfunctions")
        terminal_statuses = ["SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED"]
        if summarize:
            summary = {
                "execution_arn": execution_arn,
                "poll_interval": poll_interval,
                "current_status": None,
                "final_status": None,
                "steps": {},
            }
        else:
            log_message(
                f"Monitoring Bedrock (Step Functions) execution: {execution_arn}"
            )

        steps: Dict[str, Dict[str, Any]] = {}
        state_map: Dict[int, str] = {}
        failed_steps_processed = set()

        while True:
            # Get overall execution status.
            exec_response = client.describe_execution(executionArn=execution_arn)
            status = exec_response.get("status")

            if summarize:
                summary["current_status"] = status
            else:
                log_message(f"\nCurrent execution status: {status}")

            # Retrieve full execution history with pagination.
            events: List[Dict[str, Any]] = []
            next_token = None
            while True:
                kwargs = {
                    "executionArn": execution_arn,
                    "maxResults": 100,
                    "reverseOrder": False,
                }
                if next_token:
                    kwargs["nextToken"] = next_token
                history_response = client.get_execution_history(**kwargs)
                events.extend(history_response.get("events", []))
                next_token = history_response.get("nextToken")
                if not next_token:
                    break

            # Process events in chronological order.
            for event in events:
                event_type = event.get("type")
                event_time = event.get("timestamp")

                # Process TaskStateEntered: record step details.
                if event_type == "TaskStateEntered":
                    details = event.get("stateEnteredEventDetails", {})
                    step_name = details.get("name")
                    if step_name:
                        state_map[event.get("id", "")] = step_name
                        if step_name not in steps:
                            steps[step_name] = {
                                "step_name": step_name,
                                "status": "InProgress",
                                "entered_time": (
                                    event_time.isoformat() if event_time else None
                                ),
                            }
                            if details.get("input"):
                                steps[step_name]["input"] = details.get("input")
                        else:
                            steps[step_name]["entered_time"] = (
                                event_time.isoformat()
                                if event_time
                                else steps[step_name].get("entered_time")
                            )

                # Process successful completion via TaskStateExited.
                elif event_type == "TaskStateExited":
                    details = event.get("stateExitedEventDetails", {})
                    step_name = details.get("name")
                    if step_name and step_name in steps:
                        steps[step_name]["status"] = "Succeeded"
                        steps[step_name]["exited_time"] = (
                            event_time.isoformat() if event_time else None
                        )
                        if details.get("output"):
                            steps[step_name]["output"] = details.get("output")

                # Process failure events.
                elif event_type in ["TaskFailed", "TaskTimedOut", "TaskAborted"]:
                    prev_event_id = event.get("previousEventId", "")
                    step_name = state_map.get(prev_event_id)

                    # Fallback: if mapping failed, search for an InProgress step with entered_time before this event.
                    if not step_name:
                        candidate = None
                        candidate_time = None
                        for s_name, details in steps.items():
                            if details.get("status") == "InProgress" and details.get(
                                "entered_time"
                            ):
                                try:
                                    entered_time = datetime.fromisoformat(
                                        details["entered_time"].replace("Z", "+00:00")
                                    )
                                except Exception:
                                    continue
                                if event_time and entered_time < event_time:
                                    if candidate is None or (
                                        entered_time
                                        and candidate_time
                                        and entered_time > candidate_time
                                    ):
                                        candidate = s_name
                                        candidate_time = entered_time
                        step_name = candidate

                    if step_name and step_name in steps:
                        event_details = (
                            event.get("taskFailedEventDetails")
                            or event.get("taskTimedOutEventDetails")
                            or event.get("taskAbortedEventDetails")
                            or {}
                        )
                        error = event_details.get("error", "No error provided")
                        cause = event_details.get("cause", "No cause provided")
                        failure_reason = f"Error: {error}; Cause: {cause}"
                        steps[step_name]["status"] = "Failed"
                        steps[step_name]["exited_time"] = (
                            event_time.isoformat() if event_time else None
                        )
                        steps[step_name]["failure_reason"] = failure_reason
                        if step_name not in failed_steps_processed:
                            failed_steps_processed.add(step_name)
                            job_name = get_processing_job_name(event)
                            if job_name:
                                logs_cloud = get_cloudwatch_logs(job_name)
                                steps[step_name]["logs"] = (
                                    logs_cloud[-50:]
                                    if logs_cloud and len(logs_cloud) > 50
                                    else logs_cloud
                                )
                            else:
                                steps[step_name]["logs"] = [
                                    "No logs available or insufficient permissions"
                                ]

            # Fallback update: if overall status is terminal and any step remains InProgress, update with overall error details.
            if status in terminal_statuses:
                if status == "FAILED":
                    overall_error = exec_response.get("error", "Unknown error")
                    overall_cause = exec_response.get("cause", "No cause provided")
                    overall_failure_reason = (
                        f"Execution error: {overall_error}; Cause: {overall_cause}"
                    )
                    for s_name, details in steps.items():
                        if details.get("status") == "InProgress":
                            details["status"] = "Failed"
                            details["failure_reason"] = overall_failure_reason
                break

            # Output step details during execution.
            if not summarize:
                for step_detail in steps.values():
                    s_name = step_detail.get("step_name")
                    s_status = step_detail.get("status")
                    log_message(f"Step '{s_name}': Status: {s_status}")
                    if s_status == "Succeeded" and "output" in step_detail:
                        log_message(f"   Output: {step_detail['output']}")

            time.sleep(poll_interval)

        if summarize:
            summary["final_status"] = status
            summary["steps"] = list(steps.values())
            return [str(summary)]
        else:
            log_message(f"\n🏁 Execution finished with status: {status}")
            return logs

    else:
        # SageMaker mode remains unchanged.
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
            log_message(f"Monitoring pipeline execution: {execution_arn}")

        failed_steps_processed = set()

        while True:
            response = client.describe_pipeline_execution(
                PipelineExecutionArn=execution_arn
            )
            status = response.get("PipelineExecutionStatus")

            if summarize:
                summary["current_status"] = status
            else:
                log_message(f"\nCurrent pipeline status: {status}")

            steps_response = client.list_pipeline_execution_steps(
                PipelineExecutionArn=execution_arn
            )

            for step in steps_response.get("PipelineExecutionSteps", []):
                step_name = step.get("StepName")
                step_status = step.get("StepStatus")

                if summarize:
                    if "steps" not in summary:
                        summary["steps"] = {}
                    step_summary = summary["steps"].get(
                        step_name, {"step_name": step_name}
                    )
                    step_summary["status"] = step_status
                    summary["steps"][step_name] = step_summary
                else:
                    status_symbol = (
                        "✅"
                        if step_status == "Succeeded"
                        else "❌" if step_status == "Failed" else "⏳"
                    )
                    log_message(
                        f"{status_symbol} Step '{step_name}' - Status: {step_status}"
                    )

                if step_status == "Failed" and step_name not in failed_steps_processed:
                    failed_steps_processed.add(step_name)
                    failure_reason = step.get(
                        "FailureReason", "No failure reason provided"
                    )

                    if summarize:
                        summary["steps"][step_name]["failure_reason"] = failure_reason
                        job_name = get_processing_job_name(step)
                        if job_name:
                            logs_cloud = get_cloudwatch_logs(job_name)
                            if logs_cloud:
                                relevant_logs = (
                                    logs_cloud[-50:]
                                    if len(logs_cloud) > 50
                                    else logs_cloud
                                )
                                summary["steps"][step_name]["logs"] = relevant_logs
                            else:
                                summary["steps"][step_name]["logs"] = [
                                    "No logs available or insufficient permissions"
                                ]
                    else:
                        log_message(
                            f"\n🔍 Detailed failure information for step '{step_name}':"
                        )
                        log_message(f"Failure reason: {failure_reason}")
                        job_name = get_processing_job_name(step)
                        if job_name:
                            log_message(f"\n📋 CloudWatch Logs for job '{job_name}':")
                            logs_cloud = get_cloudwatch_logs(job_name)
                            if logs_cloud:
                                relevant_logs = (
                                    logs_cloud[-50:]
                                    if len(logs_cloud) > 50
                                    else logs_cloud
                                )
                                log_message("Last log entries before failure:")
                                for log in relevant_logs:
                                    log_message(f"    {log}")
                            else:
                                log_message(
                                    "    No logs available or insufficient permissions"
                                )
                        log_message("\n" + "=" * 80 + "\n")

            if status in ["Succeeded", "Failed", "Stopped"]:
                break

            time.sleep(poll_interval)

        if summarize:
            summary["final_status"] = status
            summary["steps"] = list(summary["steps"].values())
            return [str(summary)]
        else:
            log_message(f"\n🏁 Pipeline execution finished with status: {status}")
            return logs
