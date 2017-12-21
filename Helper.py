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

from LogObject import LogObject

class Helper(QObject):
    reload(sys)
    sys.setdefaultencoding('utf-8')
    logMeldung=pyqtSignal(LogObject)
    def __init__(self):
        QObject.__init__(self)
        self.wkbTypes = {} #init dictionary
        self.setGeomTypeNames #init GeomTypeNames in dictionary
    #This function delivers the TypeName of a geometryType
    def getGeomTypeNames(self, geomType):       
        try:
            print 'key: '+str(geomType)+ ' '+self.getGeomTypeName(geomType) #    QgsWkbTypes.displayString(geomType) #geometryDisplayString(geomType)
            geoTypeName=self.getGeomTypeName(geomType)#self.wkbTypes[geomType]
            print 'value (Geometry Type): '+geoTypeName
            return geoTypeName
        except Exception as err:
            print 'Error while configuring Export-GeometryType: ' +str(type(err))+" "+ str(err.args)
            self.logMeldung.emit(LogObject('Error while configuring Export-GeometryType: ' +str(type(err))+" "+ str(err.args) , 'Error'))
            return str(geomType) 

    def getGeomTypeName(self,geomType):
        typeString='Unknown'
        if geomType==QGis.WKBPoint:#1
            typeString='Point'
            print 'Layer is a point layer'
            
        elif geomType==QGis.WKBLineString:#2
            typeString='LineString'
            print 'Layer is a line layer'

        elif geomType==QGis.WKBPolygon:#3
            typeString='Polygon'
            print 'Layer is a polygon layer'

        elif geomType==QGis.WKBMultiPoint:
            typeString='MultiPoint'
            print 'Layer is a multi point layer'
            
        elif geomType==QGis.WKBMultiLineString:
            typeString='MultiLineString'
            print 'Layer is a multi line layer'
            
        elif geomType==QGis.WKBMultiPolygon:
            typeString='MultiPolygon'
            print 'Layer is a multi-polygon layer'

        elif geomType==100:
            typeString='NoGeometry'
            print 'Layer is a data-only layer'
        
        return typeString
            
    #This function delivers the TypeName of a geometryType
    def setGeomTypeNames(self):
    

        self.wkbTypes[0] = 'Unknown'
        self.wkbTypes[1] = 'Point'
        self.wkbTypes[QGis.WKBLineString] = 'LineString'
        self.wkbTypes[QGis.WKBPolygon] = 'Polygon'
        self.wkbTypes[QGis.WKBMultiPoint] = 'MultiPoint'
        self.wkbTypes[QGis.WKBLineString] = 'MultiLineString'
        self.wkbTypes[QGis.WKBMultiPolygon] = 'MultiPolygon'
        self.wkbTypes[str(7)] = 'GeometryCollection'
        self.wkbTypes[str(8)] = 'CircularString'
        self.wkbTypes[str(9)] = 'CompoundCurve'
        self.wkbTypes[str(10)] = 'CurvePolygon'
        self.wkbTypes[str(11)] = 'MultiCurve'
        self.wkbTypes[str(12)] = 'MultiSurface'
        self.wkbTypes[str(100)] = 'NoGeometry'
        self.wkbTypes[str(1001)] = 'PointZ'
        self.wkbTypes[str(1002)] = 'LineStringZ'
        self.wkbTypes[str(1003)] = 'PolygonZ'
        self.wkbTypes[str(1004)] = 'MultiPointZ'
        self.wkbTypes[str(1005)] = 'MultiLineStringZ'
        self.wkbTypes[str(1006)] = 'MultiPolygonZ'
        self.wkbTypes[str(1007)] = 'GeometryCollectionZ'
        self.wkbTypes[str(1008)] = 'CircularStringZ'
        self.wkbTypes[str(1009)] = 'CompoundCurveZ'
        self.wkbTypes[str(1010)] = 'CurvePolygonZ'
        self.wkbTypes[str(1011)] = 'MultiCurveZ'
        self.wkbTypes[str(1012)] = 'MultiSurfaceZ'
        self.wkbTypes[str(2001)] = 'PointM'
        self.wkbTypes[str(2002)] = 'LineStringM'
        self.wkbTypes[str(2003)] = 'PolygonM'
        self.wkbTypes[str(2004)] = 'MultiPointM'
        self.wkbTypes[str(2005)] = 'MultiLineStringM'
        self.wkbTypes[str(2006)] = 'MultiPolygonM'
        self.wkbTypes[str(2007)] = 'GeometryCollectionM'
        self.wkbTypes[str(2008)] = 'CircularStringM'
        self.wkbTypes[str(2009)] = 'CompoundCurveM'
        self.wkbTypes[str(2010)] = 'CurvePolygonM'
        self.wkbTypes[str(2011)] = 'MultiCurveM'
        self.wkbTypes[str(2012)] = 'MultiSurfaceM'
        self.wkbTypes[str(3001)] = 'PointZM'
        self.wkbTypes[str(3002)] = 'LineStringZM'
        self.wkbTypes[str(3003)] = 'PolygonZM'
        self.wkbTypes[str(3004)] = 'MultiPointZM'
        self.wkbTypes[str(3005)] = 'MultiLineStringZM'
        self.wkbTypes[str(3006)] = 'MultiPolygonZM'
        self.wkbTypes[str(3007)] = 'GeometryCollectionZM'
        self.wkbTypes[str(3008)] = 'CircularStringZM'
        self.wkbTypes[str(3009)] = 'CompoundCurveZM'
        self.wkbTypes[str(3010)] = 'CurvePolygonZM'
        self.wkbTypes[str(3011)] = 'MultiCurveZM'
        self.wkbTypes[str(3012)] = 'MultiSurfaceZM'
        self.wkbTypes[str(0x80000001)] = 'Point25D, LineString25D, Polygon25D, MultiPoint25D'
        
        print 'WkbType Sample'+self.wkbTypes[str(1)]
        #return self.wkbTypes
        