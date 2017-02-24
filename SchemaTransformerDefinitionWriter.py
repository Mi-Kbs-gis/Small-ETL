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

class SchemaTransformerDefinitionWriter(QObject):
    logMeldung=pyqtSignal('QString')
    reload(sys)
    sys.setdefaultencoding('utf-8')
    def __init__(self, expGeom,layerTransformDef, sourceLayer, targetLayer):
        QObject.__init__(self)
        self.expGeom=expGeom
        self.layerTransformDef=layerTransformDef
        self.sourceLayer = sourceLayer
        self.targetLayer = targetLayer
        tarFile=QFileInfo(self.targetLayer.source())
        self.startPath=tarFile.absoluteDir().absolutePath()  +'/'+ self.sourceLayer.name()+'_2_'+self.targetLayer.name()+'.csv'
        print self.startPath
        self.saveFile(self.startPath, self.expGeom, self.layerTransformDef)
        
    def saveFile(self, startPath,expGeom,layerTransformDef):
        #get Filename from Dialog
        #fileName = QFileDialog.getSaveFileName('Save Definition', startPath, selectedFilter='*.csv')
        dlg = QFileDialog()                                              
        dlg.setAcceptMode(1) #Means save File
        dlg.setDirectory(startPath)
        dlg.setDefaultSuffix("csv")
        dlg.setNameFilters(["CSV files (*.csv)"])#, "All files (*)"])
        if dlg.exec_() == 0:                                             
            return
        fileName=dlg.selectedFiles()[0]
        print fileName
        file=QFile(fileName)
        file = open(fileName,'w')
        if fileName:
            print fileName
            file = open(fileName,'w')
            #first write Geometry Rule
            file.write('Geometry Rule:' + expGeom.expression())#+'\n')
            for trafoDef in layerTransformDef:
                fieldNum=trafoDef[0]
                exp=trafoDef[1]
                text=str(fieldNum)+';'
                if len(str(exp.expression()))>1:
                    text=text+exp.expression()+'\n'
                else:
                    text=text+'\n'
                file.write(text)
            file.close()
