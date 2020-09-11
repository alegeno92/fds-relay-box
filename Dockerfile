FROM python:3.8-alpine
RUN pip install --no-cache-dir paho-mqtt pyserial pymodbus
RUN mkdir -p /fds-relay-box/app
WORKDIR /fds-relay-box
COPY app ./app
COPY manage.py ./manage.py
CMD ["python", "manage.py"]