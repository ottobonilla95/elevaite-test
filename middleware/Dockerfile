FROM python:3.11
WORKDIR /elevaite
COPY ./requirements.txt /elevaite/requirements.txt
RUN pip install --no-cache-dir --upgrade uvicorn==0.21
RUN pip install --no-cache-dir --upgrade -r /elevaite/requirements.txt
COPY ./ /elevaite/

ENV OPENAI_API_KEY="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"
ENV QDRANT_URL="http://3.101.65.253:6333/"
ENV QDRANT_API_KEY="0E36VGNPGaDudAyWcNISW2J2iYD3qnldrt3_l-AOxMRINEthspE7Sg"
ENV QDRANT_COLLECTION="kbDocs_netskope_v1"

EXPOSE 9005
ENV PORT 9005
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9005"]
