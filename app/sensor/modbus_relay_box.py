import logging
from datetime import datetime
from random import uniform

from pymodbus.client.sync import ModbusTcpClient as ModbusClient

from .exceptions import ModbusConnectionError
from .reader import SensorValue

DEFAULT_MODBUS_IP = '192.168.2.253'
DEFAULT_C23_RS485 = '/dev/ttymxc2'  # mxc3 on schematics

DEFAULT_RELAY_BOX_UNIT = 0x09
DEFAULT_MODBUS_PORT = 502

LABEL_RB_VB = "adc_vb"
LABEL_RB_ADC_VCH_1 = "adc_vch_1"
LABEL_RB_ADC_VCH_2 = "adc_vch_2"
LABEL_RB_ADC_VCH_3 = "adc_vch_3"
LABEL_RB_ADC_VCH_4 = "adc_vch_4"
LABEL_RB_T_MOD = "t_mod"
LABEL_RB_GLOBAL_FAULTS = "global_faults"
LABEL_RB_GLOBAL_ALARMS = "global_alarms"
LABEL_RB_HOURMETER_HI = "hourmeter_HI"
LABEL_RB_HOURMETER_LO = "hourmeter_LO"
LABEL_RB_CH_FAULTS_1 = "ch_faults_1"
LABEL_RB_CH_FAULTS_2 = "ch_faults_2"
LABEL_RB_CH_FAULTS_3 = "ch_faults_3"
LABEL_RB_CH_FAULTS_4 = "ch_faults_4"
LABEL_RB_CH_ALARMS_1 = "ch_alarms_1"
LABEL_RB_CH_ALARMS_2 = "ch_alarms_2"
LABEL_RB_CH_ALARMS_3 = "ch_alarms_3"
LABEL_RB_CH_ALARMS_4 = "ch_alarms_4"

DECIMALS = 1


# Modbus reader
class ModbusRelayBox:
    def __init__(self, id, ip_address=DEFAULT_MODBUS_IP, port=DEFAULT_MODBUS_PORT,
                 unit_id=DEFAULT_RELAY_BOX_UNIT, dummy_data=False):
        self.id = id
        self.ip_address = ip_address
        self.port = port
        self.unit_id = unit_id
        self.client = None
        self.dummy_data = dummy_data

        if not dummy_data:
            self.client = ModbusClient(self.ip_address, self.port)

        self.logger = logging.getLogger(__name__)

    def connect(self):
        self.logger.debug("opening ip: %s port: %s unit: %s ", self.ip_address, self.port, self.unit_id)
        if not self.client.connect():
            raise ModbusConnectionError("Error in Modbus connection")

    def disconnect(self):
        self.client.close()

    def read(self):

        if self.dummy_data:
            return self.generate_dummy()

        try:
            self.connect()
        except ModbusConnectionError as e:
            self.logger.error(e)
            return []

        try:
            # read registers. Start at 0 for convenience
            rr = self.client.read_holding_registers(0, 80, unit=self.unit_id)
        except Exception as e:
            self.logger.error('Charge Controller: ModbusIOException' + str(e))
            return []

        self.disconnect()

        if rr is None:
            return []

        return self.fill(rr.registers)

    def fill(self, registers=None):
        if registers is None:
            return []

        v_scale = float(78.421 * 2 ** (-15))

        return [
            SensorValue(self.id, LABEL_RB_VB, round(registers[0] * v_scale, DECIMALS), int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_ADC_VCH_1, round(registers[1] * v_scale, DECIMALS),
                        int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_ADC_VCH_2, round(registers[2] * v_scale, DECIMALS),
                        int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_ADC_VCH_3, round(registers[3] * v_scale, DECIMALS),
                        int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_ADC_VCH_4, round(registers[4] * v_scale, DECIMALS),
                        int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_T_MOD, registers[5], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_GLOBAL_FAULTS, registers[6], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_GLOBAL_ALARMS, registers[7], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_HOURMETER_HI, registers[8], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_HOURMETER_LO, registers[9], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_CH_FAULTS_1, registers[10], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_CH_FAULTS_2, registers[11], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_CH_FAULTS_3, registers[12], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_CH_FAULTS_4, registers[13], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_CH_ALARMS_1, registers[14], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_CH_ALARMS_2, registers[15], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_CH_ALARMS_3, registers[16], int(datetime.now().timestamp())),
            SensorValue(self.id, LABEL_RB_CH_ALARMS_4, registers[17], int(datetime.now().timestamp())),
        ]

    def generate_dummy(self):
        values = [
            LABEL_RB_VB,
            LABEL_RB_ADC_VCH_1,
            LABEL_RB_ADC_VCH_2,
            LABEL_RB_ADC_VCH_3,
            LABEL_RB_ADC_VCH_4,
            LABEL_RB_T_MOD,
            LABEL_RB_GLOBAL_FAULTS,
            LABEL_RB_GLOBAL_ALARMS,
            LABEL_RB_HOURMETER_HI,
            LABEL_RB_HOURMETER_LO,
            LABEL_RB_CH_FAULTS_1,
            LABEL_RB_CH_FAULTS_2,
            LABEL_RB_CH_FAULTS_3,
            LABEL_RB_CH_FAULTS_4,
            LABEL_RB_CH_ALARMS_1,
            LABEL_RB_CH_ALARMS_2,
            LABEL_RB_CH_ALARMS_3,
            LABEL_RB_CH_ALARMS_4
        ]
        data = []
        for val in values:
            data.append(
                SensorValue(self.id, val, round(uniform(0, 255), DECIMALS), int(datetime.now().timestamp())))

        return data
