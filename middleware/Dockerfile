FROM python:3.11
WORKDIR /elevaite
COPY ./requirements.txt /elevaite/requirements.txt
RUN pip install --no-cache-dir --upgrade uvicorn==0.21
RUN pip install --no-cache-dir --upgrade -r /elevaite/requirements.txt
COPY ./ /elevaite/

ENV OPENAI_API_KEY="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"
ENV QDRANT_URL="https://a29a4a5f-b731-4ffa-befd-5c3f702c66f3.us-east-1-0.aws.cloud.qdrant.io:6333"
ENV QDRANT_API_KEY="bD7Kx0EQ3hPe2FJjzjNpXr7E4mZatk9MAhqwNHi4EBOPdNqKcRW7HA"
ENV QDRANT_COLLECTION="kbDocs_netskope_v1"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
