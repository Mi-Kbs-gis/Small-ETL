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
from LogObject import LogObject
from Helper import Helper

class UniversalVectorLayerExport(QObject):
    logMeldung=pyqtSignal(LogObject)
    def __init__(self, referenceLayer, newFeatures, exportCRS, modus, geomType): # Modus(int)
        QObject.__init__(self)
        self.referenceLayer=referenceLayer
        self.newFeatures=newFeatures
        self.exportCRS=exportCRS
        self.modus = modus
        self.geomType=geomType
        self.helper=Helper()
        #generate global variables
        self.refDataProvider=self.referenceLayer.dataProvider()
        self.refFields=self.refDataProvider.fields()
        self.refEncoding=self.refDataProvider.encoding()
        
    def setNewFile(self, newFileAbsolutePath, newFileFormat):
        self.newFileAbsolutePath=newFileAbsolutePath
        self.newFileFormat=newFileFormat
        
    def manageExportProcess(self):
        #check the current modus
        if self.modus ==1: # inTargetFile"                                           
            self.writeToReferenceLayer()
            
        elif self.modus ==2: # newFile
            self.writeToNewFile()
        elif self.modus ==3: # tempFile
            self.writeToTempFile()
            
        elif self.modus ==4: # relDbWithRelationships
            self.writeToDbWithRelationships()


    def writeToReferenceLayer(self): #Modus 1
        hasError=False
        try:
            targetDataProvider=self.refDataProvider
            targetDataProvider.addFeatures(self.newFeatures)
        except Exception as err:
            hasError=True
            print " "+str(type(err))+" "+ str(err.args)
            self.logMeldung.emit(LogObject("Could not add the features in Reference Layer! "+str(type(err))+" "+ str(err.args), 'Error'))
        if hasError==False:
            print "Reference Layer was continued!"
            self.logMeldung.emit(LogObject("Continuation Reference Layer successful! "+str(len(self.newFeatures)) + " Features added!", 'Message'))


        
    def writeToNewFile(self): #Modus 2
        try:
            writer=self.manageVectorFileWriter(self.newFileFormat)#self.newFileAbsolutePath, self.refEncoding, self.refFields, self.geomType, self.exportCRS, self.newFileFormat)
            #writer = QgsVectorFileWriter(self.newFileAbsolutePath, self.refEncoding, self.refFields, self.geomType, self.exportCRS, self.newFileFormat)
            #writer = QgsVectorFileWriter("my_shapes.shp", "CP1250", fields, QGis.WKBPoint, self.exportCRS, "ESRI Shapefile")
            if writer.hasError() != QgsVectorFileWriter.NoError:
                self.logMeldung.emit(LogObject("Error when creating "+self.newFileFormat+"-File: " + writer.errorMessage(), 'Error'))
                print "Error when creating "+self.newFileFormat+"-File: ",  writer.errorMessage()
            else:
                try:
                    for feature in self.newFeatures:
                        writer.addFeature(feature)
                
                    print self.newFileFormat+"-File writing successful! "+str(self.newFileAbsolutePath)
                    self.logMeldung.emit(LogObject("File writing successful! "+str(self.newFileAbsolutePath), 'Message'))
                except Exception as exc:
                    self.logMeldung.emit(LogObject("Unknown Error when write features to new File: "+str(type(exc))+" "+ str(exc.args), 'Error'))
            # delete the writer to flush features to disk
            del writer
        except Exception as err:
            self.logMeldung.emit(LogObject("Unknown Error when creating new File: "+str(type(err))+" "+ str(err.args), 'Error'))
        
    def writeToTempFile(self): #Modus 3
        # try:
        geomTypeString=self.helper.getGeomTypeNames(self.geomType)
        vl = QgsVectorLayer(geomTypeString+'?crs='+str(self.exportCRS.authid()), "temporary_"+self.referenceLayer.name(), "memory")
        print "no crs set yed"
        #vl = iface.addVectorLayer(self.geomType, "temporary_"+self.referenceLayer.name(), "memory") #Lege einen temporaeren Layer an
        #vl.setCrs(self.exportCRS)
        print "crs was set"
        pr = vl.dataProvider()
        # add fields
        pr.addAttributes(self.refFields)
        vl.updateFields() # tell the vector layer to fetch changes from the provider
        pr.addFeatures(self.newFeatures)
        vl.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayer(vl)
        print "Features exported to temporary Layer"
        #Zoom To Layer-Extent
        #canvas = qgis.utils.iface.mapCanvas()
        #canvas.setExtent(vl.extent())

        self.logMeldung.emit(LogObject("Writing to new temporary Layer successful! "+str(len(self.newFeatures)) + " Features added!", 'Message'))
        # except:
            # self.logMeldung.emit(LogObject("Could not add the features in temporary Layer! ", 'Error'))
        

    def writeToDbWithRelationships(self): #Modus 4
        #ToDo read table Relationships with SQL
        print 'DB Export with Relationships is not implemented yed!'

    ################# Methods to manage VectorlayerExport - Formats ###########################
    #def getGeopackageWriter(self):
    
    def manageVectorFileWriter(self, driverName):
        #ext = QString('shp')#driverName.decode("utf-8"))
        optParam=[]
        if driverName=="shp" :
            longName = "ESRI Shapefile"
            
            glob = "*.shp"
            ext = "shp"

        elif driverName=="gpkg":

            longName = 'GPKG' #"GeoPackage"
            
            glob = "*.gpkg"
            ext = "gpkg"
            optParam=["SPATIALITE=YES",]

        elif driverName=="json":
            longName = "GeoJSON"
            
            glob = "*.json"
            ext = "json"

        elif driverName=="gml":
            longName = "GML"
            
            glob = "*.gml"
            ext = "gml"

        elif driverName=="kml":
            longName = "KML"
            
            glob = "*.kml"
            ext = "kml"      
            
        elif driverName=="sqlite":

            longName = 'SQLite'#"GeoPackage"
            
            glob = "*.sqlite"
            ext = "sqlite"
            optParam=["SPATIALITE=YES",]

        elif driverName=="gdb":# No Driver

            longName = 'FileGDB'
            
            glob = "*.gdb"
            ext = "gdb"
            optParam=["FEATURE_DATASET="+self.referenceLayer.name(),]

        elif driverName=="tab":

            longName = 'MapInfo File'
            
            glob = "*.tab"
            ext = "tab"

        ######### non spatial #########
        elif driverName=="ods":

            longName = 'ODS'
            
            glob = "*.ods"
            ext = "ods"

        elif driverName=="xls": #OGR-Fehler: GDALDriver::Create() no create method implemented for this format.

            longName = 'XLS'
            
            glob = "*.xls"
            ext = "xls"

        elif driverName=="xlsx":

            longName = 'XLSX'
            
            glob = "*.xlsx"
            ext = "xlsx"


        writer = QgsVectorFileWriter(self.newFileAbsolutePath, self.refEncoding, self.refFields, self.geomType, self.exportCRS, longName, optParam)
        return writer
        
        # From PostGIS layer to SpatiaLite:

        # from ogr2ogr import *
        # main( [ "",
                # "-f",
                # "SQLite",
                # "-lco",
                # "GEOMETRY_NAME=geom",
                # "-update",
                # existingDBPath, # Path to existing .sqlite file
                # "PG:{}".format( dataSourceURI.connectionInfo() ), # Connection string
                # "{}.{}".format( dataSourceURI.schema(), dataSourceURI.table() ) # Tablename
              # ]
           # )

        # From a Shapefile QGIS layer to SpatiaLite:

        # from ogr2ogr import *
        # main( [ "",
                # "-f",
                # "SQLite",
                # "-lco",
                # "GEOMETRY_NAME=geom",
                # "-update",
                # existingDBPath, # Path to existing .sqlite file
                # layer.source()
              # ]
           # )