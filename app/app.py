import configparser
import json
import os
import logging
from random import randint
from threading import Thread, Event

from .sensor.configuration_manager import ConfigurationManager
from .sensor.modbus_relay_box import ModbusRelayBox
from .utils import connector, IIoT


def get_random_client_id():
    return 'RB_{}'.format(randint(1, 20))


class App(Thread):

    def __init__(self, config_file_path):
        super().__init__()
        self.exit_event = Event()
        self.config_file_path = config_file_path
        self.mqtt_client = None
        self.configurations = {}
        self.configuration_manager = ConfigurationManager(self.config_file_path)
        self.mqtt_topics = []
        self.relay_box = None
        self.logger = logging.getLogger(__name__)

    def init(self):
        self.configurations = self.load_configuration()
        self.configuration_manager.save(self.configurations)

        self.mqtt_client = connector.MqttLocalClient(client_id=self.configurations['CLIENT_ID'],
                                                     host=self.configurations['MQTT_HOSTNAME'],
                                                     port=self.configurations['MQTT_PORT'],
                                                     subscription_paths=self.get_mqtt_topics(),
                                                     message_callback=self.on_message_callback)

        self.relay_box = ModbusRelayBox(
            id=self.configurations['CLIENT_ID'],
            ip_address=self.configurations['MODBUS_IP'],
            port=self.configurations['MODBUS_PORT'],
            unit_id=int(self.configurations['MODBUS_UNIT']),
            dummy_data=self.configurations['DUMMY_DATA']
        )

    def reset(self):
        self.logger.debug('RESET')
        self.relay_box = ModbusRelayBox(
            id=self.configurations['CLIENT_ID'],
            ip_address=self.configurations['MODBUS_IP'],
            port=self.configurations['MODBUS_PORT'],
            unit_id=int(self.configurations['MODBUS_UNIT']),
            dummy_data=self.configurations['DUMMY_DATA']
        )

    def load_configuration(self):
        if os.path.exists(self.config_file_path):
            return self.get_configurations_from_config()

        return self.get_configurations_from_env()

    def get_configurations_from_env(self):
        return {
            'ENABLE': int(os.getenv('ENABLE', 0)),
            'CLIENT_ID': os.getenv('CLIENT_ID', get_random_client_id()),
            'MQTT_HOSTNAME': os.getenv('MQTT_HOSTNAME', 'mosquitto'),
            'MQTT_PORT': int(os.getenv('MQTT_PORT', '1883')),
            'READING_INTERVAL': int(os.getenv('READING_INTERVAL', 10)),
            'DUMMY_DATA': int(os.getenv('DUMMY_DATA', 0)),
            'MODBUS_IP': os.getenv('MODBUS_IP', '192.168.2.253'),
            'MODBUS_PORT': int(os.getenv('MODBUS_PORT', 502)),
            'MODBUS_UNIT': int(os.getenv('MODBUS_UNIT', 1)),
        }

    def get_mqtt_topics(self):
        return [
            '{}/{}/+/request'.format(IIoT.MqttChannels.configurations, self.configurations['CLIENT_ID']),
            '{}/{}/+/request'.format(IIoT.MqttChannels.actuators, self.configurations['CLIENT_ID'])
        ]

    def get_configurations_from_config(self):
        configs = configparser.ConfigParser()
        configs.read(self.config_file_path)
        default = configs['DEFAULT']
        return {
            'ENABLE': int(default['ENABLE']),
            'MQTT_HOSTNAME': default['MQTT_HOSTNAME'],
            'MQTT_PORT': int(default['MQTT_PORT']),
            'CLIENT_ID': default['CLIENT_ID'],
            'READING_INTERVAL': int(default['READING_INTERVAL']),
            'DUMMY_DATA': int(default['DUMMY_DATA']),
            'MODBUS_IP': default['MODBUS_IP'],
            'MODBUS_PORT': int(default['MODBUS_PORT']),
            'MODBUS_UNIT': int(default['MODBUS_UNIT'])
        }

    def run(self):
        self.logger.info('run')
        self.mqtt_client.run()

        while not self.mqtt_client.is_connecting.wait(0.5):
            self.logger.debug("connecting...")

        self.logger.info("connected")

        while not self.exit_event.isSet():
            try:
                if not self.exit_event.isSet():
                    self.read()
                self.exit_event.wait(self.configurations['READING_INTERVAL'])
            except KeyboardInterrupt:
                self.exit_event.set()
                self.logger.info('closing')

    def read(self):
        if self.configurations['ENABLE']:
            self.logger.debug('read')
            try:
                self.read_and_publish(self.relay_box.read())
            except Exception as e:
                self.logger.error(e)

    def read_and_publish(self, data):
        self.logger.debug("send data: %s", data)
        for value in data:
            topic = '{}/{}/{}'.format(IIoT.MqttChannels.sensors, value.module, value.sensor)
            self.mqtt_client.publish(topic, json.dumps(value.stocazzo_format()))

    def on_message_callback(self, message):
        topic = message.topic
        payload = json.loads(message.payload)

        self.logger.debug(topic)
        self.logger.debug(payload)

        topic_arguments = topic.split('/')

        payload = json.loads(message.payload)

        if topic_arguments[1] == 'configurations':
            try:
                _, mqtt_channel, module, configuration, direction = topic_arguments
                value = payload['value']
                value_type = payload['value_type']

                if self.change_configurations(configuration, value, value_type):
                    response_topic = "/{}/{}/{}/response".format(mqtt_channel, module, configuration)
                    self.mqtt_client.publish(response_topic, json.dumps(payload))

            except Exception as e:
                # publish back
                self.logger.error(e)
        elif topic_arguments[1] == 'actuators':
            self.logger.debug(payload)
        else:
            self.logger.error('unknown message on topic %s: %s', topic, payload)

    def change_configurations(self, key, value, value_type=None):
        if key not in self.configurations.keys():
            self.logger.error('%s not in configurations', key)
            return False

        if value_type == 'integer':
            value = int(value)
        elif value_type == 'float':
            value = float(value)
        elif value_type == 'string':
            value = str(value)
        else:
            return False

        self.configurations[str(key)] = value
        self.configuration_manager.save(self.configurations)
        self.reset()
        return True
