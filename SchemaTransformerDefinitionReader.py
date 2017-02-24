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
import codecs

class SchemaTransformerDefinitionReader(QObject):
    logMeldung=pyqtSignal('QString')
    reload(sys)
    sys.setdefaultencoding('utf-8')
    def __init__(self, sourceLayer, targetLayer):
        QObject.__init__(self)
        self.sourceLayer = sourceLayer
        self.targetLayer = targetLayer
        tarFile=QFileInfo(self.targetLayer.source())
        self.startPath=tarFile.filePath()
        self.expGeom, self.layerTransformDef=self.readFile(self.startPath)
        
    def readFile(self, startPath=''):
        layerTransformDef=[]
        #fileName = QFileDialog.getOpenFileName('Open Definition', startPath, selectedFilter='*.csv')
        dlg = QFileDialog()                                              
        dlg.setAcceptMode(0) #Means open File
        dlg.setDirectory(startPath)
        dlg.setDefaultSuffix("csv")
        dlg.setNameFilters(["CSV files (*.csv)"])#, "All files (*)"])
        if dlg.exec_() == 0:                                            
            return
        fileName=dlg.selectedFiles()[0]
        #file = open(fileName,'r')
        file = codecs.open(fileName, 'r', 'utf-8')#file_encoding)
        #allText = file.read()
        #stream=QTextStream(QString(allText),QIODevice.ReadOnly)
        #self.editor()
        rowNum=0
        #expGeom=QgsExpression() #emty Expression
        #with file:
        #lineTexts=file.readLines()
        #hasText=True
        #while hasText:
        for lineText in file:    
            #if not lineText:
            #    #break
            #    #hasText=False
            lineText.decode('utf-8') 
            if rowNum==0:
                #'Geometry Rule:'
                splitTextGeom=lineText.split(':')
                if len(splitTextGeom)==2:
                    expTxtGeom=splitTextGeom[1]
                    expGeom=QgsExpression(expTxtGeom)
                else:
                    #no Geometry Rule
                    expGeom=QgsExpression('')
            else:
                splitText=lineText.split(';')
                try:
                    trafoDef=[int(splitText[0]), QgsExpression(splitText[1])]
                    if len(trafoDef)==2:
                        layerTransformDef.append(trafoDef)
                except:
                    print "Red Def: Error in Row " + str(rowNum)+": "+lineText
            rowNum=rowNum+1
        return expGeom, layerTransformDef