class ModbusConnectionError(Exception):
    """ Base modbus exception """

    def __init__(self, string):
        """ Initialize the exception
        :param string: The message to append to the error
        """
        self.string = string

    def __str__(self):
        return 'Modbus Connection Error: %s' % self.string

    def is_error(self):
        """Error"""
        return True
