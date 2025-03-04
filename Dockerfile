FROM python
WORKDIR /data_provider
COPY ./configs /data_provider/configs
COPY ./house_files /data_provider/house_files
COPY ./runtime /data_provider/runtime
COPY ./utils /data_provider/utils
COPY requirements.txt /data_provider

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python", "-m", "runtime.Entrypoint"]