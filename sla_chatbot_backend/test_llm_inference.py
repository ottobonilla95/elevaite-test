from fastapi.testclient import TestClient
from httpx import Response

from llm_inference import app

client = TestClient(app)


def test_read_main():
    print("hello")
    response: Response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_post_message():
    response: Response = client.post(
        "/",
        headers={"X-Token": "coneofsilence"},
        json={
            "conversation_payload": [{"actor": "system", "content": "How can I help you"}, {"actor": "user", "content": "Were there any breaches recently"}],
            "query": "Was there any breaches?",
            "skip_llm_call": True,
            }
    )

    expected_prompt = """
You are an analyst who helps customers understand decides whether there is a breach of SLOs or not.

Your goal is to answer users questions politly. Only use the information given below.
If you cannot find the information decline politely.
Give specific answers

There are three categories of SLOs: Availability, Risk and Compliance and Service Operations

Each one of the categories has:
 - category: Availability, Risk and Compliance or Service Operations
 - breach_detected: True means a breach happened, false means that no breach
 - service_target
 - actual_service_level
 - service_level_date
 - service_credit: Also known as slo_breach_penalty
 - earnback: The credit paid to the vendor
 - data_source
 - comment: Which can contain more details like (but not limited to) exception for the chargeback
 - description: describing the SLO

There is a breach if and only if breach_detected is set to Yes for a given date then this is considered an SLO breach and slo_breach_penalty should be paid.
If a breach is detected mention the service target and the actual service level.
If the user asks about a breach and there are multiple breaches list them all on separate lines
Use the information in the comment that can contain exception on whether the penalty should be applied or not.

Below is the data for each category

system: How can I help you
user: Were there any breaches recently"""

    assert response.status_code == 200
    assert response.json() == {
        "prompt": expected_prompt,
    }