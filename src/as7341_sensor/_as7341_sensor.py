class Sensor:
    """Mock class for Sensor: Wrapper for AS7341 implementation"""

    def __init__(self, atime=100, astep=999, gain=8, i2c=None):
        """Mock initialization of Sensor"""
        self.__atime = atime
        self.__astep = astep
        self.__gain = gain
        self._all_channels_accessed = False  # This is for testing purposes

    @property
    def _atime(self):
        return self.__atime

    @_atime.setter
    def _atime(self, value):
        self.__atime = value

    @property
    def _astep(self):
        return self.__astep

    @_astep.setter
    def _astep(self, value):
        self.__atime = value

    @property
    def _gain(self):
        return self.__gain

    @_gain.setter
    def _gain(self, gain):
        self.__gain = gain

    @property
    def all_channels(self):
        """Mock method to get all channels data"""
        self._all_channels_accessed = True  # This is for testing purposes
        return [100, 200, 300, 400, 500, 600, 700, 800]  # return mock values

    def disable(self):
        """Mock method to disable the sensor"""
        pass
