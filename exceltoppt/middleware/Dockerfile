FROM python:3.11
RUN mkdir elevaite
WORKDIR /elevaite
COPY poetry.lock pyproject.toml /elevaite
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN pip install --no-cache-dir --upgrade uvicorn==0.23.2
# Install dependencies
RUN poetry install
COPY . .

ENV OPENAI_API_KEY="<api_key"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9003"]
