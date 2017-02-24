# -*- coding: utf-8 -*-
"""
/***************************************************************************
    Small-ETL
	A QGIS plugin to perform schema transformations of QGIS vectorlayers
                             -------------------
    begin            : 2017-02-01
    author           : Michael Kürbs(LEG Thüringen)
    email            : michael.kuerbs@leg-thueringen.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from qgis.core import *
from qgis.gui import *

import os
import sys

class LogObject(QObject):
    def __init__(self, message, type):
        QObject.__init__(self)
        self.message= message
        self.type = type