FROM python:3.9-slim
WORKDIR /data_provider
COPY ./runtime /data_provider/runtime
COPY ./utils /data_provider/utils
COPY requirements.txt /data_provider

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python", "-m", "runtime.Entrypoint"]