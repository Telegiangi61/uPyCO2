# Copyright 2020 LeMaRiva|Tech (Mauro Riva) info@lemariva.com
# https://github.com/lemariva/uPyCO2
#
# Library modified by Gian Luigi Perrella 
# 
# https://github.com/Telegiangi61/uPyCO2
# 
# added:
# 1) reading of raw_H2 and raw_Ethanol
# 2) reading sensor serial id, i2c address and featureset
# 

import time
from micropython import const

_SGP30_DEFAULT_I2C_ADDR = const(0x58)
_SGP30_FEATURESET = const(0x22)

_SGP30_CRC8_POLYNOMIAL = const(0x31)
_SGP30_CRC8_INIT = const(0xFF)
_SGP30_WORD_LEN = const(2)

class SGP30:
    """
    A driver for the SGP30 gas sensor.

    :param i2c: The `I2C` object to use. This is the only required parameter.
    :param int address: (optional) The I2C address of the device.
    """
    def __init__(self, i2c, address=_SGP30_DEFAULT_I2C_ADDR):
        """Initialize the sensor, get the serial # and verify that we found a proper SGP30"""
        self._i2c = i2c
        self._addr = address
        self.serial = self._i2c_read_words_from_cmd(command=[0x36, 0x82], reply_size=3, delay=0.01)
        featureset = self._i2c_read_words_from_cmd([0x20, 0x2f], 1, 0.01)
        if featureset[0] != _SGP30_FEATURESET:
            raise RuntimeError('SGP30 Not detected')
        print(
            "SGP30 sensor discovered...\n" +
            "I2C address: " + str(self._addr) + "\n" +
            "Serial ID: " + str(self.serial) + "\n" +
            "Feature set: " + str(featureset) + "\n"
        )
        self.initialise_indoor_air_quality()

    @property
    def total_organic_compound(self):
        """Total Volatile Organic Compound in parts per billion."""
        return self.indoor_air_quality[1]

    @property
    def baseline_total_organic_compound(self):
        """Total Volatile Organic Compound baseline value"""
        return self.indoor_air_quality_baseline[1]

    @property
    def co2_equivalent(self):
        """Carbon Dioxide Equivalent in parts per million"""
        return self.indoor_air_quality[0]

    @property
    def baseline_co2_equivilant(self):
        """Carbon Dioxide Equivalent baseline value"""
        return self.indoor_air_quality_baseline[0]

    @property
    def raw_h2(self):
        """Total Volatile Organic Compound in parts per billion."""
        return self.raw_air_quality[0]
    
    @property
    def raw_ethanol(self):
        """Total Volatile Organic Compound in parts per billion."""
        return self.raw_air_quality[1]


    def initialise_indoor_air_quality(self):
        """Initialize the IAQ algorithm"""
        # name, command, signals, delay
        self._i2c_read_words_from_cmd(command=[0x20, 0x03], reply_size=0, delay=0.01)

    @property
    def indoor_air_quality(self):
        """Measure the CO2eq and TVOC"""
        # name, command, signals, delay
        return self._i2c_read_words_from_cmd(command=[0x20, 0x08], reply_size=2, delay=0.05)
    
    @property
    def raw_air_quality(self):
        """Measure the raw H2 and ETHANOL values for sensor testing"""
        # name, command, signals, delay
        return self._i2c_read_words_from_cmd(command=[0x20, 0x50], reply_size=2, delay=0.05)

    @property
    def indoor_air_quality_baseline(self):
        """Get the IAQ algorithm baseline for CO2eq and TVOC"""
        # name, command, signals, delay
        return self._i2c_read_words_from_cmd(command=[0x20, 0x15], reply_size=2, delay=0.01)

    def set_indoor_air_quality_baseline(self,
                                        co2_equivalent,
                                        total_volatile_organic_compounds):
        """Set the previously recorded IAQ algorithm baseline for CO2eq and TVOC"""
        if co2_equivalent == 0 and total_volatile_organic_compounds == 0:
            raise RuntimeError('Invalid baseline')
        buffer = []
        for value in [total_volatile_organic_compounds, co2_equivalent]:
            arr = [value >> 8, value & 0xFF]
            arr.append(generate_crc(arr))
            buffer += arr
        self._i2c_read_words_from_cmd(command=[0x20, 0x1e] + buffer, reply_size=0, delay=0.01)

    # Low level command functions
    def _i2c_read_words_from_cmd(self, command, reply_size, delay):
        """Run an SGP command query, get a reply and CRC results if necessary"""
        self._i2c.writeto(self._addr, bytes(command))
        time.sleep(delay)
        if not reply_size:
            return None
        crc_result = bytearray(reply_size * (_SGP30_WORD_LEN + 1))
        self._i2c.readfrom_into(self._addr, crc_result)
        result = []
        for i in range(reply_size):
            word = [crc_result[3*i], crc_result[3*i+1]]
            crc = crc_result[3*i+2]
            if generate_crc(word) != crc:
                raise RuntimeError('CRC Error')
            result.append(word[0] << 8 | word[1])
        return result


def generate_crc(data):
    """8-bit CRC algorithm for checking data"""
    crc = _SGP30_CRC8_INIT
    # calculates 8-Bit checksum with given polynomial
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ _SGP30_CRC8_POLYNOMIAL
            else:
                crc <<= 1
    return crc & 0xFF