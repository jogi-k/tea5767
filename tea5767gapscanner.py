#!/usr/bin/python3 
# -*- coding: utf-8 -*-

"""
Filename  	: tea5767gapscanner.py
Programmer	: Jogi Kuenstner
Date / Version	: Feb 2016. V1.0 
Tech		: Python 3, SMBUS, i2C, TEA5767 FM Radio, Raspberry Pi 2
Project		: FM-GAP-Scanner
Module		: TEA5767 Radio


Reference	:
1. https://raw.githubusercontent.com/JTechEng/tea5767/
2. https://github.com/pcnate/fm-radio-python
3. http://www.astromik.org/raspi/38.htm

Usage		:
sudo python3 tea5767gapscanner.py
or with executable file
sudo ./tea5767controller.py
"""



from tea5767stationscanner import tea5767

a = tea5767()
a.gapscan()
