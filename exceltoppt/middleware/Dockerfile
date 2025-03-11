FROM python:3.11
RUN mkdir elevaite
WORKDIR /elevaite
COPY pyproject.toml /elevaite
# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN uv pip install --no-cache-dir --upgrade uvicorn==0.23.2
# Install dependencies
RUN uv sync
COPY . .

ENV OPENAI_API_KEY="<api_key"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9003"]
