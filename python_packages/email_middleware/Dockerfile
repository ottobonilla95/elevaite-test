FROM python:3.11
WORKDIR /elevaite
COPY ./requirements.txt /elevaite/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /elevaite/requirements.txt
COPY ./ /elevaite/
CMD ["python", "email_listener.py"]
