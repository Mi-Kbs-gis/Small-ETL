# -*- coding: utf-8 -*-
"""
/***************************************************************************
    Small-ETL
    A QGIS plugin to perform schema transformations of QGIS vectorlayers
                             -------------------
    begin            : 2017-02-01
    author           : Michael Kürbs(TLUG Thüringen)
    email            : michael.kuerbs@tlug.thueringen.de
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
import random


from SchemaTransformer import SchemaTransformer
from SchemaTransformerDefinitionWriter import SchemaTransformerDefinitionWriter
from SchemaTransformerDefinitionReader import SchemaTransformerDefinitionReader
from UniversalVectorLayerExport import UniversalVectorLayerExport
from LogObject import LogObject

#sys.path.append(os.path.dirname(__file__))
#form, base = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'SchemaTransformer.ui"'), resource_suffix='')

pluginPath = os.path.dirname(os.path.abspath(__file__))
form, base = loadUiType(pluginPath + "\SchemaTransformer.ui")

class SchemaTransformDialog(base):
    reload(sys)
    sys.setdefaultencoding('utf-8')
    def __init__(self, main):
        base.__init__(self)
        self.main = main
        self.ui = form()
        self.ui.setupUi(self)
        #self.setWindowFlags(Qt.WindowStaysOnTopHint) #immer im Vordergrund
        self.setAcceptDrops(True)
        self.loadLayers()
        # self.main.sourceLayer=QgsMapLayerRegistry.instance().mapLayer(str(0))
        # self.main.targetLayer=QgsMapLayerRegistry.instance().mapLayer(str(0))
        #self.setSelectetLayers
        self.loadLayerAttributes #Setting up the TableWidget with the StartValues of the Comboboxes
        ################# actions ########################
        #self.ui.pushButton_reloadLayers.clicked.connect(self.buttonReloadLayers)
        self.ui.pushButton_Start.clicked.connect(self.startProcess)
        self.ui.pushButton_Cancel.clicked.connect(self.clickOnCancel)
        self.ui.pushButton_saveTrafo.clicked.connect(self.saveLayerTransformDefinition)
        self.ui.pushButton_loadTrafo.clicked.connect(self.readLayerTransformDefinition)
        self.ui.pushButton_saveToNewFile.clicked.connect(self.runSaveFileDialog)
        #self.ui.pushButton_GeometryRule.clicked.connect(self.showExpressionsBuilder(self.main.sourceLayer))
        self.widget_GeometryRule=QgsFieldExpressionWidget()
        #Startwert setzen auf SourceGeometrie
        self.widget_GeometryRule.setExpression('$geometry')#geht erst ab Version 2.18
        self.widget_GeometryRule.setExpressionDialogTitle("Geometry Rule")
        self.ui.gridLayout_geometry.addWidget(self.widget_GeometryRule,1,0)#Fuege es in 2.zeile und 1.Spalte neben dem Label Geometry Rule ein
        #Wiget for selecting targetCRS
        self.projection_selection_widget = QgsProjectionSelectionWidget()
        #self.projection_selection_widget.resize(100, 30)
        self.ui.gridLayout_geometry.addWidget(self.projection_selection_widget,1,1)#Fuege es in 2.zeile und 2.Spalte neben dem Label Geometry Rule ein
        self.ui.gridLayout_geometry.setColumnMinimumWidth(1,300)
        self.projection_selection_widget.crsChanged.connect(self.settingUpTargetCRS)
        QObject.connect(self.ui.mComboBox_SourceLayer, SIGNAL("currentIndexChanged (int)"), self.comboItemChanged)   #Auswahl Layer
        QObject.connect(self.ui.mComboBox_TargetLayer, SIGNAL("currentIndexChanged (int)"), self.comboItemChanged)   #Auswahl Layer
        self.ui.progressBar.setValue(0)
        #setting up SaveTo Radiobuttons
        self.ui.radioButton_inTargetFile.toggled.connect(self.setSaveToModus)
        self.ui.radioButton_newFile.toggled.connect(self.setSaveToModus)
        self.ui.radioButton_tempFile.toggled.connect(self.setSaveToModus)
        self.ui.radioButton_relDbWithRelationships.toggled.connect(self.setSaveToModus)
        self.ui.gridLayout_saveTo.setColumnMinimumWidth(1,100)

        self.ui.radioButton_inTargetFile.setChecked(True) #Am Start soll Target Layer ausgewaehlt sein.
        self.saveToModus=1
        self.geomTypeChangeAllowed=False
        self.projection_selection_widget.setEnabled(False)

        self.ui.radioButton_allFeatures.setChecked(True) #Am Start soll All Features ausgewaehlt sein.

        #Setzte Layerselection as unmanaged
        self.comboLayerChanged=False
        self.absNewFileName='' # path for Export of a new File

        
        #nicht implementierte GUI-Elemente ausaschalten
        self.ui.radioButton_relDbWithRelationships.setEnabled(False)#.setCheckable(False)
        self.ui.radioButton_relDbWithRelationships.setVisible(False)
        #self.ui.radioButton_newFile.setEnabled(False)
        #self.ui.radioButton_tempFile.setEnabled(False)

    def comboItemChanged(self):
        self.comboLayerChanged=True
        #print 'comboLayerChanged'
        self.loadLayerAttributes()
    

        #analyzer for the SaveTo Radio-Buttons 
    def setSaveToModus(self):
        try:
            if self.ui.radioButton_inTargetFile.isChecked():
                self.saveToModus=1 # "inTargetFile"
                self.geomTypeChangeAllowed=False
                #set exportCRS to targetLayer.crs
                self.projection_selection_widget.setCrs(self.main.targetLayer.crs())
                self.exportCRS=self.main.targetLayer.crs()
                #block CRS-Selection
                self.projection_selection_widget.setEnabled(False)

            elif self.ui.radioButton_newFile.isChecked():
                self.saveToModus=2 # newFile
                self.geomTypeChangeAllowed=True
                self.projection_selection_widget.setEnabled(True)
            elif self.ui.radioButton_tempFile.isChecked():
                self.saveToModus=3 # tempFile
                self.geomTypeChangeAllowed=True
                self.projection_selection_widget.setEnabled(True)
            elif self.ui.radioButton_relDbWithRelationships.isChecked():
                self.saveToModus=4 # relDbWithRelationships
                self.geomTypeChangeAllowed=False
                #set exportCRS to targetLayer.crs
                self.projection_selection_widget.setCrs(self.main.targetLayer.crs())
                self.exportCRS=self.main.targetLayer.crs()
                #block CRS-Selection
                self.projection_selection_widget.setEnabled(False)
        except Exception as err:
            pass
            #print "Error while setting SaveTo from Radiobutton: "+ str(err.args) + ";" + str(repr(err))


            
    def setDefaultTargetCrs(self):
        self.projection_selection_widget.setCrs(self.main.targetLayer.crs())
        self.exportCRS=self.main.targetLayer.crs()

    # After selecting the layers, the tableWidget have to reload the content
    def loadLayerAttributes(self):     # def buttonReloadLayers(self, checked):
        self.ui.listWidgetLog.clear()
        #print "lade Layers in Settings" 
        self.setSelectetLayers()
        #init the global Schema Transformator Object
        self.schemaTrans=SchemaTransformer(self.main.sourceLayer, self.main.targetLayer)
        self.schemaTrans.logMeldung.connect(self.schreibeLog)
        #pruefe, wenn Layer unterschiedliche Bezugssysteme haben gib eine Warnung heraus
        if not self.schemaTrans.isSameLayerCrs(self.main.sourceLayer, self.main.targetLayer):
            self.schreibeLog(LogObject("Different Coordinate Reference Systems. Transfomation is set: " + self.main.sourceLayer.crs().authid()+ ' to ' + self.main.targetLayer.crs().authid(),'Warning'))
            print 'Layer haben unterschiedliche Bezugssysteme'
        
        #Default exportCRS is the CRS of the targetLayer
        self.exportCRS=self.main.targetLayer.crs()
        self.projection_selection_widget.setCrs(self.main.targetLayer.crs())
    
    #This function is loading the Layers into the Layer Comboboxes
    def loadLayers(self):
        #lade Layernamen in Comboboxen
        layerList = []
        layers=[] # Liste wird geleert
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        iLayer=0
        for name, layer in layerMap.iteritems():
            if layer.type() != QgsMapLayer.RasterLayer:
                #print name + ' Index: '+ str(iLayer)
                layers.append(layer)
                #Layername in Combobox
                layerList.append( unicode( layer.name()+" ("+str(layer.crs().authid()))+")")
                iLayer=iLayer+1
        self.main.layers=layers
        self.main.layerList=layerList
        print str(len(layerList)) + '|' +str(len(layers))+ ' Layer geladen'
        for layer in layerList: # foreach layer in legend 
            self.ui.mComboBox_SourceLayer.addItem(layer)
            self.ui.mComboBox_TargetLayer.addItem(layer)

    #This function performs the main process of the plugin
    def startProcess(self):
        #Check if Source and TargetLayer has Geometry Than check if useGeometry is active
        if not self.main.sourceLayer.wkbType()==100 and not self.main.targetLayer.wkbType()==100: #and not self.main.exportLayer.wkbType()==100
            if not self.ui.checkBox_GeometryUse.isChecked():
                #ask if the geometry shall be used
                reply = QMessageBox.question(self, 'Continue?', 
                 'The current Layers have geometries! Would you use it?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    #set geometry use active
                    self.ui.checkBox_GeometryUse.setChecked(True)

        #hier werden die Transformatiuonseinstellung definiert - soll ueber GUI ablaufen
        #in jedem Lisetneintrag wird ein Feld eingetragen [zielFeldID,optionale Expression]
        self.ui.progressBar.setValue(0)
        if self.main.sourceLayer.isValid and self.main.targetLayer.isValid:
            # get the geometry and attribute definition from the Expression-Comboboxes
            expGeom, layerTransformDef=self.generateTransformationDefinition()
            #ToDo: take the new Data into a new LayerFile or into the targetLayer
            
            ##################### Main Process #########################
                      
            targetDataProvider=self.main.targetLayer.dataProvider()


            #was the geometry needed
            useGeometrie=self.ui.checkBox_GeometryUse.isChecked()
            #Check the Connection Condition
            onlySelectedFeats=self.checkOnlySelectionCondition()
            # perfom the schema transformation
            self.schemaTrans.notifyProgress.connect(self.onProgress)
            isValid=self.schemaTrans.setProcessParameter(layerTransformDef, onlySelectedFeats, useGeometrie, expGeom, self.geomTypeChangeAllowed)
            if isValid:

                newFeatures=self.schemaTrans.starte()#

                self.processVectorExport(self.main.targetLayer, newFeatures, self.exportCRS, self.schemaTrans.targetGeometryType)

    def processVectorExport(self, referenceLayer, newFeatures, exportCRS, geomType):
        print 'geomType: '+str(geomType)#+'='+str(self.schemaTrans.wkbTypes[geomType])

        hasError=False
        
        
        if self.saveToModus==1: # "inTargetFile"
            pass
            
        elif self.saveToModus==2: # newFile
            fInfo=QFileInfo(self.absNewFileName)
            #pathInfo=QFileInfo(fInfo.filePath)
            if len(str(self.absNewFileName))==0: #pathInfo.exists: # setting up the new file parameters fileName and File-Type
                self.schreibeLog(LogObject("New File Path is not set!",'Error')) # or does not exist!
                hasError=True
        elif self.saveToModus==3: # tempFile
            pass
        elif self.saveToModus==4: # relDbWithRelationships -- not implemented yet
            pass
        else:
            self.schreibeLog(LogObject("Output Option is not set",'Error'))
             
        if hasError==False:
            uve=UniversalVectorLayerExport(referenceLayer, newFeatures, exportCRS, self.saveToModus, geomType)
            uve.logMeldung.connect(self.schreibeLog)
            if self.saveToModus==2:
                uve.setNewFile(self.absNewFileName,self.newFileExtension)
            uve.manageExportProcess()
            print 'Export features with Modus ' + str(self.saveToModus)
        else:
            self.schreibeLog(LogObject("The new features were not exported!",'Error'))

    def runSaveFileDialog(self):
        nameFilterList=[]
        nameFilterList.append(['ESRI Shapefile', 'shp']) #[DriverName,File-Extension]
        #nameFilterList.append(['FileGDB','gdb']) # No Driver
        nameFilterList.append(['GeoJSON','json'])
        nameFilterList.append(['Geopackage','gpkg'])
        nameFilterList.append(['GML','gml'])
        nameFilterList.append(['KML','kml'])
        nameFilterList.append(['MapInfo File' ,'tab'])
        nameFilterList.append(['SQLite','sqlite'])
        ###### non Spatial ######
        #nameFilterList.append(['XLS','xls']) #OGR-Fehler: GDALDriver::Create() no create method implemented for this format.
        nameFilterList.append(['XLSX','xlsx'])# it works!!!
        nameFilterList.append(['ODS', 'ods'])
        nameFilterList.append(['CSV', 'csv'])
        nameFilterList.append(['DBF', 'dbf'])

        
        filters=self.createFileFilteList(nameFilterList)
    
        #get Filename from Dialog
        dlg=QFileDialog( self )
        dlg.setWindowTitle( 'Save To New File' )
        #dlg.setViewMode( QFileDialog.Detail )
        #dlg.setNameFilters(nameFilterList)
        dlg.setNameFilters(filters)# [self.tr('ESRI Shapefile (*.shp)'),self.tr('SQLite (*.sqlite)'),self.tr('GeoJSON (*.json)')] )#,self.tr('Geopackage (*.gpkg)'), self.tr('All Files (*)')] )
        #dlg.setDefaultSuffix( 'shp' )
        if dlg.exec_() :
            fileName = dlg.selectedFiles()[0]
            if len(fileName)>1:
                

                nameFilter=dlg.selectedNameFilter()
                print 'nameFilter: ' + nameFilter.decode("utf-8")
                formatExt='shp' #Default
                for nFilter in nameFilterList:
                    tempName=nFilter[0]
                    tempExt=nFilter[1]
                    nameDef=nameFilter.split(' ') #Get first word befor Space
                    tempDef=tempName.split(' ')
                    print 'compare: ' + nameDef[0]+"<->"+tempDef[0]

                    if nameDef[0]==tempDef[0]:#=='ESRI Shapefile (*.shp)':
                        formatExt=tempExt
                        print 'compare true: ' + nameDef[0]+"<->"+tempDef[0]

                print 'Extension: ' + formatExt
                #fileName+dlg.selectedNameFilter()
                fInfo=QFileInfo(fileName)

                self.absNewFileName = fileName #QFileDialog.getSaveFileName(self, "Save To New File", "Export_" , "All files (*)") #".shp")
                
                #Check if the File Extension is valid
                print "Check if the File Extension is valid: "+self.absNewFileName 
                ptPos=self.absNewFileName.rfind(".") # detection of the point where the File-Extension is beginning
                fileExt=self.absNewFileName[ptPos+1:]
                if not fileExt==formatExt:
                    self.absNewFileName=self.absNewFileName+'.'+formatExt
                    #print 'Extension added ' + '.'+formatExt
                    fileExt=formatExt
                else:
                    fileExt=formatExt
                    
                self.newFileExtension=fileExt #.decode("utf-8")
                
                #print "File-Extension= " + fileExt+ ' rfind(".")='+str(fileExt.find("."))+'    fileExt.find("/"):'+str(fileExt.find("/"))
                fileInfo=QFileInfo(self.absNewFileName)
                if fileExt.find("/")>-1:
                    self.absNewFileName=''
                    self.newFileExtension=''
                    print 'File Name not valid!'
                    self.ui.pushButton_saveToNewFile.setText("...")
                elif fInfo.exists():
                    QMessageBox.warning(self,'File already exists!','Choose another file name.')
                    self.absNewFileName=''
                else:
                    self.ui.pushButton_saveToNewFile.setText(fileInfo.fileName())
                    
                print 'File: '+self.absNewFileName
                

        
        #tr("GeoData OGR (*.shp *.gml *.xml *.tab)")
    def createFileFilteList(self, inList):
        filterList=[]
        for item in inList:
            tempName=item[0]
            tempExt=item[1]
            
            filterTxt=tempName+' (*.'+ tempExt +')' #Sample:    'ESRI Shapefile (*.shp)'
            filterList.append(filterTxt)
        return filterList
    
    def checkOnlySelectionCondition(self):
        if self.ui.radioButton_selectedFeatures.isChecked():
            return True
        else:
            return False #self.ui.radioButton_allFeatures.isChecked()==True
    
    #This function stores the transformation definition in 2 dimensional list (targetFieldID, QgsExpression)
    def generateTransformationDefinition(self):
        #get the Geometry Expression from the Widget
        geomFilter=self.widget_GeometryRule.currentField()[0]
        expGeom = QgsExpression(geomFilter)
        #get the attribute transformation rules
        layerTransformDef=[]
        targetFields=self.main.targetLayer.pendingFields()
        iFeld=0
        try:
            logTextType='Message'
            for field in targetFields:
                expWidget=self.ui.tableWidget_Transform.cellWidget(iFeld,1 )
                #print expWidget.currentText()
                if expWidget.isExpression():
                    filter=expWidget.currentField()[0]
                    exp = QgsExpression(filter)
                    layerTransformDef.append([iFeld,exp])
                elif len(expWidget.currentText())>0:
                    # es wurde nur ein Feld ausgewaehlt
                    filter=expWidget.currentField()[0]
                    exp = QgsExpression(filter)
                    layerTransformDef.append([iFeld,exp]) #expWidget.expression()]) # unter vorbehalt
                else:
                    # Field is emty
                    logTextType='Warning'
                    pass
                #self.schreibeLog(LogObject(field.name()+': '+expWidget.currentText(),'Message'))
                #print field.name()+': '+expWidget.currentText()
                iFeld=iFeld+1
        except UnicodeEncodeError as err:
            print "Error beim auslesen der Transformationsdefinitionen "+str(iFeld) + ". Feld des TransformWidget: "+ str(err.args) + ";" + str(repr(err))
        return expGeom, layerTransformDef
        
    # This function is sets the global layer variables
    def setSelectetLayers(self):
        #print "setSelectetLayers startet"
        # Identify selected layer by its index
        sourceLayerIndex = self.ui.mComboBox_SourceLayer.currentIndex()
        #print 'Index SourceLayer: ' + str(sourceLayerIndex)
        self.main.sourceLayer = self.main.layers[sourceLayerIndex] #Error list out of range
        targetLayerIndex = self.ui.mComboBox_TargetLayer.currentIndex()
        #print 'Index TargetLayer: ' + str(sourceLayerIndex)
        self.main.targetLayer = self.main.layers[targetLayerIndex]
        #setting up the tableWidgets
        self.setLayerTables()
        #### Is the source layer non-spatial?
        if self.main.sourceLayer.wkbType()==100:
            self.schreibeLog(LogObject('Source-Layer is a data-only layer!','Warning'))
            print 'Source-Layer is a data-only layer'
        #falls keine Auswahl im Source Layer vorliegt, deaktiviere den Radiobutton
        #if self.main.sourceLayer.selectedFeatureCount()==0:
        #    self.ui.radioButton_selectedFeatures.setEnabled(False)
        #    self.ui.radioButton_allFeatures.setChecked(True)
        #else:
        #self.ui.radioButton_selectedFeatures.setEnabled(True)
        

        # This function is setting up the tableWidgets
    def setLayerTables(self):
        # leere die Tabellen
        self.ui.tableWidget_SourceLayer.clearContents()
        #self.ui.tableWidget_TargetLayer.clearContents()
        self.ui.tableWidget_Transform.clearContents()
        #Spalten SrcTable
        fields=self.main.sourceLayer.pendingFields()
        #fields=self.main.sourceLayer.dataProvider().fields()
        srcEncoding=self.main.sourceLayer.dataProvider().encoding()
        print 'Source Layer Encoding: '+ str(self.main.sourceLayer.dataProvider().encoding())
        anzSrcFields=len(fields)
        srcFieldNames=[]
        srcFieldTypes=[]
        srcFieldNumbers=[]
        iSrcField=0
        for field in fields:
            fName=field.name()#.decode("utf-8")#.encode("utf-8")
            srcFieldNames.append(fName)
            srcFieldTypes.append(field.type)
            srcFieldNumbers.append(str(iSrcField)) #setVerticalHeaderLabels needs a QStringList
            iSrcField=iSrcField+1
        self.ui.tableWidget_SourceLayer.setRowCount(anzSrcFields) #Vertical Header means the FieldNumber
        srcHeadlabels = ['Source-Field']
        
        self.ui.tableWidget_Transform.setHorizontalHeaderLabels(srcHeadlabels)
        self.ui.tableWidget_SourceLayer.setVerticalHeaderLabels(srcFieldNumbers)#srcFieldNames) #QStringList Spaltennamen
        # definiere Spalteneintraege der Tabelle
        self.ui.tableWidget_SourceLayer.setColumnCount(1) # nur eine Spalte
        #schreibe Feldeigenschaften in Datenzeile
        iFeld=0
        for field in fields:
            strLabel=str(field.name()+' ('+field.typeName()+')')
            #strLabel=field.typeName()
            #print strLabel
            item = QTableWidgetItem(strLabel)
            self.ui.tableWidget_SourceLayer.setItem(iFeld,0,item)
            #item = QTableWidgetItem(strLabel)
            #item.setData( Qt.UserRole, str(field.name()+'|'+field.typeName()))
            #self.ui.tableWidget_SourceLayer.setItem(1,iFeld,item)
            iFeld=iFeld+1
        self.ui.tableWidget_SourceLayer.resizeColumnsToContents()
        self.ui.tableWidget_SourceLayer.setDragEnabled(True)


        # Spalten ZielTable und TransformTable
        tarFields=self.main.targetLayer.pendingFields()
        anztarFields=len(tarFields)
        tarFieldNames=[]
        tarFieldTypes=[]
        tarFieldNumbers=[]
        iTarField=0
        for field in tarFields:
            fName=field.name()
            tarFieldNames.append(fName)
            tarFieldTypes.append(field.typeName())
            tarFieldNumbers.append(str(iTarField)) #setVerticalHeaderLabels needs a QStringList
            iTarField=iTarField+1
        #print str(len(tarFieldNames))+ " Felder aus TargetLayer"
        
        #self.ui.tableWidget_TargetLayer = DragDropTable()#rows, columns, parent)
        #self.ui.tableWidget_Transform = DragDropTable()#rows, columns, parent)
        #self.ui.tableWidget_TargetLayer.setAcceptDrops(True)
        self.ui.tableWidget_Transform.setAcceptDrops(True)
        #self.ui.tableWidget_TargetLayer.setDragEnabled(True)
        self.ui.tableWidget_Transform.setDragEnabled(True)
        
        #self.ui.tableWidget_TargetLayer.setColumnCount(anztarFields)
        #self.ui.tableWidget_TargetLayer.setHorizontalHeaderLabels(tarFieldNames) #QStringList Spaltennamen
        self.ui.tableWidget_Transform.setRowCount(anztarFields)
        self.ui.tableWidget_Transform.setVerticalHeaderLabels(tarFieldNumbers)#tarFieldNames) #QStringList Spaltennamen
        #Header of self.ui.tableWidget_Transform
        transHeadlabels = ['Target-Field', 'Rule']
        
        self.ui.tableWidget_Transform.setHorizontalHeaderLabels(transHeadlabels)
        # definiere Spalteneintraege der Tabelle
        self.ui.tableWidget_Transform.setColumnCount(2) # nur zwei Spalten
        #schreibe Feldeigenschaften in Datenzeile
        iTarfeld=0
        for field in tarFields:
            #Der Datentyp kommt in die erste Zeile
            item = QTableWidgetItem(field.name()+' ('+field.typeName()+')') 
            self.ui.tableWidget_Transform.setItem(iTarfeld,0,item)
            #In die zeite Zeile kommt die Transformationsdefinition fuer das Feld
            expItem=QgsFieldExpressionWidget()
            expItem.setLayer(self.main.sourceLayer)
            self.ui.tableWidget_Transform.setCellWidget(iTarfeld,1, expItem)#.setCellWidget(0, iTarfeld, trafoButton)
            #
            #QObject.connect(trafoItem, SIGNAL("clicked()"), self.showExpressionsBuilder(self.main.sourceLayer, trafoItem))
 

            iTarfeld=iTarfeld+1

        self.ui.tableWidget_Transform.resizeColumnsToContents()
        #self.ui.tableWidget_Transform.setAcceptDrops(True)
        #self.ui.tableWidget_Transform.setDragEnabled(True)

        
        #setting up Geometry-Rule-Widget
        self.widget_GeometryRule.setLayer(self.main.sourceLayer)

    #Update Progressbar
    def onProgress(self, i):
        self.ui.progressBar.setValue(i)
        #if self.ui.progressBar.value() >= self.ui.progressBar.maximum():
        #    self.close()
    
    #write Row into Log List
    def schreibeLog(self, log):
        item = QListWidgetItem(log.message)
        if log.type=='Message':
            item.setBackgroundColor(QColor(198,233,175)) #Message Green
        elif log.type=='Warning':
            item.setBackgroundColor(QColor(255,248,198)) #Warning Yellow
        elif log.type=='Error':
            item.setBackgroundColor(QColor(255,213,255)) #Error Red
        else:
            item.setBackgroundColor(QColor(255,255,255)) # White
        self.ui.listWidgetLog.addItem(item)


    def clickOnCancel(self):
        self.close()
        #sys.exit(app.exec_())
        
    def saveLayerTransformDefinition(self):
        if self.comboLayerChanged==False:
            QMessageBox.warning(self,'Layer Selection is needed!','Select the Layers befor reading the Transfomation-Definition!')
        else:
            expGeom, layerTransformDef=self.generateTransformationDefinition()
            #get the Geometry Expression from the Widget
            #geomFilter=self.widget_GeometryRule.currentField()[0]
            #expGeom = QgsExpression(geomFilter)
            writer=SchemaTransformerDefinitionWriter(expGeom,layerTransformDef, self.main.sourceLayer, self.main.targetLayer)

    def readLayerTransformDefinition(self):
        if self.comboLayerChanged==False:
            QMessageBox.warning(self,'Layer Selection is needed!','Select the Layers befor reading the Transfomation-Definition!')
        else:
            reader=SchemaTransformerDefinitionReader(self.main.sourceLayer, self.main.targetLayer)
            expGeom=reader.expGeom # Geometry Rule
            self.widget_GeometryRule.setExpression(expGeom.expression())
            print 'Geometry Rule:' + expGeom.expression()
            layerTransformDef=reader.layerTransformDef
            #self.ui.tableWidget_Transform.clearContents()
            #ToDo Pruefe ob Anzahl der TranformDef=der Felder des Target Layers
            iDef=0
            iList=0
            for trafoDef in layerTransformDef:
                if len(trafoDef)==2:
                    try:
                        iTrafoFeld=trafoDef[0]
                        exp=trafoDef[1] #QgsExpression(expTxt.expression())
                        
                        #ToDo TransformarmationsDefinition i widget uebernehmen 
                        ## Unter QGIS 2.14 kann das QgsFieldExpressionWidget nicht per Code mit einer Expression gefuellt werden erst ab 2.18
                        
                        expItem=QgsFieldExpressionWidget()
                        expItem.setLayer(self.main.sourceLayer)
                        expItem.setExpression(exp.expression())
                        #ToDo setting the Actions
                        #expItem.currentFieldChanged.connect(self.trandformRuleChanged)
                        #expItem.expressionEditingFinished.connect(self.trandformRuleChanged)
                        self.ui.tableWidget_Transform.removeCellWidget(iTrafoFeld, 1)
                        self.ui.tableWidget_Transform.setCellWidget(iTrafoFeld,1, expItem)
                        #print str(iTrafoFeld) + '-->'+ str(exp.expression())
                    except:
                        self.schreibeLog(LogObject('Error while taking over Field Expressions at Index ' + str(iDef) ,'Error'))
                        print "Error while taking over Field Expressions at Index " + str(iDef) 
                iList=iList+1
                if len(exp.expression())>1:
                    iDef=iDef+1
            if iDef>1:
                self.schreibeLog(LogObject('LayerTransformation imported: ' + str(iDef)+ ' Rules for ' + str(len(layerTransformDef)) + ' Fields' ,'Message'))
    
    def settingUpTargetCRS(self):
        #check if Save To Mode is "New File" or "Temp File"
        if self.ui.radioButton_newFile.isChecked() or self.ui.radioButton_tempFile.isChecked():
            projection_selection_widget = QgsProjectionSelectionWidget()
            projection_selection_widget.resize(400, 30)

            self.exportCRS=projection_selection_widget
        else:
            self.projection_selection_widget.setCrs(self.main.targetLayer.crs())
            self.exportCRS=self.main.targetLayer.crs()
    
        #projection_selection_widget.show() 
    
    #ToDo Einfaerben von korrespondierenden Feldern mit Zufallsfarbe 
    #def trandformRuleChanged(self, expWidget): # takes a QgsFieldExpressionWidget
    
    # def getRandomColor(self):
    # random.seed()
    # r=random.randint(0,255)
    # g=random.randint(0,255)
    # b=random.randint(0,255)
    # return QColor.fromRgb(r,g,b,100) #Alpha=100
                
                

    ######################## non used #################################

    def on_expression_fieldChange(self, fieldName):
        self.commitData.emit(self.sender())
        
    def showExpressionsBuilder(self, layer):#, item):
        #context = self.param.expressionContext()
        dlg = QgsExpressionBuilderDialog(layer, 'Geometrie-Formel', self)#(layer, item.text(), self)#, 'generic', context) # 2. Parameter ist gleich der Starttext!!
        dlg.setWindowTitle(self.tr('Expression based input'))
        if dlg.exec_() == QDialog.Accepted:
            exp = QgsExpression(dlg.expressionText())
            if not exp.hasParserError():
                #self.setValue(dlg.expressionText())
                print dlg.expressionText()
                #item.setText(dlg.expressionText())
                #return dlg.expressionText()#exp
        self.geomExpression=exp
        #self.ui.pushButton_GeometryRule.setText(self.geomExpression.currentText())

    def getDataTypePixMap(self, typeName):
        imagePath=pluginPath + "\icons"
        fileName=""
        if typeName=="Integer":
            fileName=""
        elif typeName=="Real":
            fileName=""
        elif typeName=="String":
            fileName=""
        elif typeName=="Date":
            fileName=""
        elif typeName=="Geometry":
            fileName=""
            icon=QIcon(":/plugins/SchemaTransformTool/icons/geom.png")
        # pic=QtGui.QPixmap(imagePath+"\"+fileName)
        # return pic

