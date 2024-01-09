"""
Control of WS2812 / NeoPixel LEDs.

MicroPython module: https://docs.micropython.org/en/v1.21.0/library/neopixel.html

This module provides a driver for WS2818 / NeoPixel LEDs.

``Note:`` This module is only included by default on the ESP8266, ESP32 and RP2
   ports. On STM32 / Pyboard and others, you can either install the
   ``neopixel`` package using :term:`mip`, or you can download the module
   directly from :term:`micropython-lib` and copy it to the filesystem.
"""


class Incomplete:
    pass


class NeoPixel:
    """
    Construct an NeoPixel object.  The parameters are:

        - *pin* is a machine.Pin instance.
        - *n* is the number of LEDs in the strip.
        - *bpp* is 3 for RGB LEDs, and 4 for RGBW LEDs.
        - *timing* is 0 for 400KHz, and 1 for 800kHz LEDs (most are 800kHz).
    """

    ORDER: Incomplete
    pin: Incomplete
    n: Incomplete
    bpp: Incomplete
    buf: Incomplete
    timing: Incomplete

    def __init__(self, pin, n, bpp=3, timing=1):
        self.pin = pin
        self.n = n
        self.bpp = bpp
        self.timing = timing
        self.pixels = [(0, 0, 0)] * n
        self._history = []  # This is for testing purposes

    def __len__(self) -> int:
        """
        Returns the number of LEDs in the strip.
        """
        ...

    def __setitem__(self, index, value):
        """
        Set the pixel at *index* to the value, which is an RGB/RGBW tuple.
        """
        self.pixels[index] = value
        self._history.append(value)  # This is for testing purposes

    def __getitem__(self, index):
        """
        Returns the pixel at *index* as an RGB/RGBW tuple.
        """
        return self.pixels[index]

    def fill(self, color):
        """
        Sets the value of all pixels to the specified *pixel* value (i.e. an
        RGB/RGBW tuple).
        """
        self.pixels = [color] * self.n
        self._history.append(color)  # For testing purposes

    def write(self):
        """
        Writes the current pixel data to the strip.
        """
        pass  # In a real NeoPixel class, this would write the data to the LEDs
