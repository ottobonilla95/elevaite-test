FROM python:3.8
WORKDIR /elevaite
COPY ./requirements.txt /elevaite/requirements.txt
RUN pip3 install --no-cache-dir --upgrade uvicorn==0.21
RUN pip3 install --no-cache-dir --upgrade -r /elevaite/requirements.txt
COPY ./ /elevaite/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
