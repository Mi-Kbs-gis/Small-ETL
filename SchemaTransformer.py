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

class SchemaTransformer(QThread):
    reload(sys)
    sys.setdefaultencoding('utf-8')
    notifyProgress = pyqtSignal(int)
    logMeldung=pyqtSignal(LogObject)
    def __init__(self, sourceLayer, targetLayer):
        QThread.__init__(self)
        self.targetLayer = targetLayer
        self.sourceLayer = sourceLayer
        self.helper=Helper()
        


    #def __del__(self):
    # self.wait()
        
    #This function defines a Transformation between the Layer-Crs    
    def getCrsTransform(self, sourceLayer, targetLayer):
        srcCrs=sourceLayer.crs()
        tarCrs=targetLayer.crs()
        transformCrs=QgsCoordinateTransform(srcCrs, tarCrs)
        return transformCrs

    #This function is for initialization of the SchemaTransformer Parameters
    def setProcessParameter(self, layerTransformDef, onlySelection, useGeometry, geometryExpression=None):
        isValid=True
        self.layerTransformDef=layerTransformDef
        self.onlySelection=onlySelection
        self.useGeometry=useGeometry
        self.geometryExpression=geometryExpression
        self.wkbTypes=self.setGeomTypeNames
        if useGeometry: 
            # check up the geometry type of the Geometry-Rule result
            self.targetGeometryType, self.isGeomValid=self.getGeomRuleGeomType(geometryExpression)
            if self.isGeomValid==False:
                isValid=False
            else:
                isValid=True
        else:
            self.targetGeometryType=100 #'NoGeometry'
            
        return isValid

    #This function is for getting the features for the processing "ALL" or "SELECTED"
    def getFeatures(self):
        if self.onlySelection: #Check the Connection Condition
            features = self.sourceLayer.selectedFeatures()
            anzahl=self.sourceLayer.selectedFeatureCount()
        else:
            features = self.sourceLayer.getFeatures()
            anzahl=self.sourceLayer.featureCount()
        return features,anzahl

        #This function generates a list of Features in the targetLayer-Schema : generateNewFeatures   
    def starte(self):
        hasError=False
        targetDataProvider=self.targetLayer.dataProvider()
        
        feats, anzAbsolute=self.getFeatures()
        
        targetFields=self.targetLayer.pendingFields()
        #print 'Ziel-Schema: ' + str(len(targetFields)) + ' Felder'
        #self.logMeldung.emit(['Ziel-Schema: ' + str(len(targetFields)) + ' Felder','0'])
        #self.logMeldung.emit(LogObject('Target-Schema: ' + str(len(targetFields)) + ' Fields: ', 'Message'))
        strFeldnamen=''
        iFeld=0
        for feld in targetFields:
            strFeldnamen=strFeldnamen+feld.name()+' '
            # try:
                # print feld.name() # wirft Error, wenn im Namen des TargetLayer ein Sonderzeichen ist
            # except:
                # print 'Feld ' + str(iFeld)+ ' des Ziellayers hat vermutlich Sonderzeichen, bitte entfernen'
                # self.logMeldung.emit(LogObject( 'Probably Field ' + str(iFeld)+ 'of Target has special characters, please replace it', 'Error'))
                # hasError=True
            iFeld=iFeld+1
            
        self.logMeldung.emit(LogObject('Target-Schema: ' + str(len(targetFields)) + ' Fields: ' + strFeldnamen, 'Message'))
        #self.logMeldung.emit(LogObject('hasError1: '+str(hasError), 'Message'))

        newFeatures=[]
        iFeat=0
        if hasError==False:
            
            for srcFeature in feats: #uebertrage die Objekte
                #Neues Objekt in Zieltabelle
                feature = QgsFeature(targetFields)
                
                for transformDef in self.layerTransformDef: #gehe jede FeldTransfoamtionsbedingung durch
                    nachId=transformDef[0] # Zielspalte
                    exp=transformDef[1]

                    exp.prepare(self.sourceLayer.pendingFields())
                    # Ist eine Expression definiert?
                    if len(exp.expression())>1:
                        #self.logMeldung.emit(LogObject(targetFields[nachId].name() + ': ' + exp.expression(), 'Message'))
                        #print str(targetFields[nachId].name()) + ': '+str(feature[nachId])+' Formel: ' + exp.expression()
                        try:
                            feature[nachId]=exp.evaluate(srcFeature)
                            if str(feature[nachId])=='NULL':
                                #no Value
                                feature[nachId]=None
                            elif exp.hasEvalError():
                                self.logMeldung.emit(LogObject('Expression EvalError: ' + exp.expression() + ' Wert: ' + str(feature[nachId])+' '+exp.evalErrorString(), 'Error'))
                                print 'Expression EvalError: ' + exp.expression() + ' Wert: ' + str(feature[nachId])+' '+exp.evalErrorString()
                                hasError=True
                                break
                                #raise ValueError(exp.evalErrorString())
                            elif exp.hasParserError():
                                self.logMeldung.emit(LogObject('Expression ParserError: ' + exp.expression() + ' Wert: ' + str(feature[nachId])+' '+exp.parserErrorString(), 'Error'))
                                hasError=True
                                print 'Expression ParserError: ' + exp.expression() + ' Wert: ' + str(feature[nachId])+' '+exp.parserErrorString()
                                break
                                #raise ValueError(exp.parserErrorString())
                        except Exception as err:
                            print 'Zielfeld(' +str(nachId)+ ") unbekannter Fehler bei Feature " + str(iFeat)+":"+str(targetFields[nachId].name())+" "+str(type(err))+" "+ str(err.args)
                            self.logMeldung.emit(LogObject(str(type(err))+": Expression"+ exp.expression() + ' Target-Field(' +str(targetFields[nachId].name())+"): "+ str(err.args)+' on feature' + str(iFeat), 'Error'))
                            hasError==True
                            #raise ValueError(str(type(err))+" "+ str(err.args))
                    else:
                        #try:
                        #    print str(targetFields[nachId].name()) + ": no value"
                        #except:
                        #    print 'Zielfeld(' +str(nachId)+ "): no value"
                        #self.logMeldung.emit(LogObject(targetFields[nachId].name() + ": no value", 'Message'))
                        feature[nachId]=None

                    #print "Result: " + str(feature[nachId]) 
                featTxt=""
                for att in feature.attributes():
                    if not str(att)=='NULL':
                        featTxt=featTxt + ' ' +str(att)
                attTxt='Feature('+str(iFeat)+'):'+featTxt
                print attTxt
                
                ############################ Geometrie #################################    
                #Soll eine Geometie uebernommen werden
                if self.useGeometry:
                    hasGeomError, tarGeom=self.generateGeometry(srcFeature, self.geometryExpression)
                    #self.logMeldung.emit(LogObject('hasGeomErrorGend: '+str(hasGeomError) + ' Formel: ' +self.geometryExpression, 'Message'))
                    if hasGeomError==True: #If there is a Error in Geometry Rule, don't run the process
                        hasError=True
                        print 'Geometry is not ok! '+ self.geometryExpression.expression()
                        self.logMeldung.emit(LogObject('Geometry on Feature('+ str(iFeat) + ') is not ok! '+ self.geometryExpression.expression(), 'Error'))
                        ########################### Projektion ################################
                    elif not tarGeom is None: # Falls eine Geometrie existiert, pruefe ob Bezugssysteme uebereinstimmen
                        try:
                            tarGeom=self.handleGeometryProjektion(tarGeom)
                            feature.setGeometry(tarGeom)
                        except:
                            hasError=True
                            self.logMeldung.emit(LogObject('Error while Projection Transformation, Please Check the CRS settings of the layers!', 'Error'))
                            break
                    else:
                        hasError=True
                        break
                        #feature.setGeometry(QgsGeometry())
                else: #Falls keine Geometrie uebernommen werden soll
                    #self.logMeldung.emit(LogObject(self.geometryExpression.parserErrorString (), 'Error'))
                    #print self.geometryExpression.parserErrorString ()
                    feature.setGeometry(QgsGeometry()) #leere Geometrie wird gesetzt                    
                    
                iFeat=iFeat+1

                newFeatures.append(feature)
                prozent=iFeat*100/anzAbsolute
                rest=(prozent*100)%100
                if rest==0: #Rest der ganzzahligen Division muss 0 sein, dann wird ein neuer Prozent-Status ausgegeben
                    #print str(prozent) + '% ..verarbeitet'
                    self.notifyProgress.emit(prozent)

        #self.logMeldung.emit(LogObject('hasErrorEnd: '+str(hasError), 'Message'))

        if hasError==False:
            #take over the features only if no error exits
            print str(len(newFeatures)) + ' Features processed'
            self.logMeldung.emit(LogObject(str(len(newFeatures)) + ' Features processed', 'Message'))
            return newFeatures
            
        else:
            self.logMeldung.emit(LogObject('Process cancelled', 'Error'))
            return []
    
    #This function generates a geometry from Source-Feature or a QgsExpression
    def generateGeometry(self, srcFeature, geometryExpression):
        hasError=False
        geomOK=False
        tarGeom=None
        
        #Wenn nein kann maximal durch eine Expression eine valide Geometrie erzeugt werden
        
        #if ToDo #Wurde eine Expression fuer die Geometrie definert
        if len(geometryExpression.expression())>0:
            #filter=self.widget_GeometryRule.currentField()[0]
            #context = QgsExpressionContext()
            #context.setFeature(srcFeature)
            exp = geometryExpression# QgsExpression(filter)
            # test=exp.checkExpression(context)
            # if test==False:
                # print 'Error Geometry Expression: '+ exp.formatPreviewString(QString)
            exp.prepare(self.sourceLayer.pendingFields())
            newGeomExp=exp.evaluate(srcFeature) #Formel gibt eine Geometrie zurueck-
            #self.logMeldung.emit(LogObject('newGeom: '+newGeomExp.exportToWkt() 'Message'))
            #self.logMeldung.emit(LogObject('hasEvalError: '+str(exp.hasEvalError), 'Message'))
            if exp.hasEvalError():# or newGeom.isNull():
                self.logMeldung.emit(LogObject('Error while Geometry-Rule Evaluation: ' + exp.expression() + 'on Source Feature('+str(srcFeature.id())+"): "+exp.evalErrorString(), 'Error'))#+ exp.evalErrorString' Wert 1.Punkt: ' + str(newGeomExp.vertexAt(0).toString()), 'Error'))
                hasError=True

            elif srcFeature==None:
                self.logMeldung.emit(LogObject('Error while generating Geometry. SrcFeature is Null: ', 'Error'))
                hasError=True
            elif newGeomExp==None:
                self.logMeldung.emit(LogObject('Error on Result of Geometrie-Rule, no Geometry can created: '  + exp.expression() + ' :'+exp.evalErrorString(), 'Error'))
                hasError=True
            elif not newGeomExp.wkbType()==self.targetLayer.dataProvider().geometryType():
                print 'Rule: '+str(newGeomExp.type())+' TargetLayer: '+ str(self.targetLayer.dataProvider().geometryType())
                #Type 0=WKBUnknown, Type 1=Point, 2=Linestring, 3=Polygon,  100=WKBNoGeometry                + str(self.wkbTypes[self.targetLayer.geometryType()]) + ' TargetLayer: ' + str(self.wkbTypes[newGeomExp.wkbType()])
                self.logMeldung.emit(LogObject('Error on Result of Geometrie-Rule, different Geometry Types!   Geometry Rule: ' + str(self.helper.getGeomTypeName(newGeomExp.wkbType())) + ' TargetLayer: ' + str(self.helper.getGeomTypeName(self.targetLayer.dataProvider().geometryType())) , 'Error'))#+") "+str(newGeomExp.exportToWkt()) + ' on Source Feature('+str(srcFeature.id())
                hasError=True
                #print 'Fehler bei Geometrie-Formel: Ausgabe nicht konform zum Geometrietyp des Ziel-Layers: ' + str(self.targetLayer.wkbType()) + ' Wert: ' + str(newGeomExp.wkbType())

            else:
                #self.logMeldung.emit(LogObject('Geom 1. Punkt: ' + str(newGeomExp.vertexAt(0).toString())+ ' Type: ' + str(newGeomExp.type()), 'Message'))
                #print 'Geom 1. Punkt: ' + str(newGeomExp.vertexAt(0).toString())+ ' Type: ' + str(newGeomExp.type())
                tarGeom=newGeomExp
        #Falls das Quellfeature eine Geometrie hat, wird diese uebernommen
        elif srcFeature.geometry(): #ab QGIS 2.18 srcFeature.hasGeometry():
            srcGeom=srcFeature.geometry()   
            err=srcGeom.validateGeometry()
            if not err:
                tarGeom=srcFeature.geometry()
                geomOK=True
                #self.logMeldung.emit(LogObject('Quell-Geom 1. Punkt: ' + str(tarGeom.vertexAt(0).toString()) + ' uebernommen! Type: ' + str(tarGeom.type()), 'Error'))
                #print 'Quell-Geom 1. Punkt: ' + str(tarGeom.vertexAt(0).toString()) + ' uebernommen! Type: ' + str(tarGeom.type())
            if geomOK == False:
                self.logMeldung.emit(LogObject('Error while getting geometrie. Geometriy is not valid. Feature ' + srcFeature.id(), 'Error'))
                hasError=True
                #print 'Error while getting geometrie. Geometriy is not valid. Feature ' + srcFeature.id()
                #raise ValueError(err.evalErrorString())
                #raise Expection(exp.parserErrorString())
        else:
            self.logMeldung.emit(LogObject('Es konnte keine Geometrie erzeugt werden. Quelldatensatz hat keine Geometrie und keine Geometrieformel defiert. ' + srcFeature.id(), 'Error'))
            print 'Es konnte keine Geometrie erzeugt werden. Quelldatensatz hat keine Geometrie und keine Geometrieformel defiert.'
            hasError=True
        return hasError, tarGeom

    #This function makes safe, that the result geometry is in the CRS of the TargetLayer
    def handleGeometryProjektion(self, geom):
        if not self.isSameLayerCrs(self.sourceLayer,self.targetLayer):
            #transform the Geometrie to the targetLayer-Crs
            #self.logMeldung.emit(LogObject('unterschiedliche Bezugssysteme: '+ self.sourceLayer.name() + '(' + str(self.sourceLayer.crs()) + ' --> ' +self.targetLayer.name() + '(' + str(self.targetLayer.crs()), 'Message'))
            #print 'unterschiedliche Bezugssysteme: '+ self.sourceLayer.name() + '(' + str(self.sourceLayer.crs()) + ' --> ' +self.targetLayer.name() + '(' + str(self.targetLayer.crs())

            self.setCrsTransformData(self.sourceLayer,self.targetLayer)# Transformation must be set
            boolTrafo=geom.transform(self.transformCrs)
            if boolTrafo==0:
                # Transformation ok
                pass
                #print str(boolTrafo) + ' nachher: ' + str(geom.vertexAt(0).toString()) + ' in neues Bezugssystem transformiert'
            else:
                self.logMeldung.emit(LogObject('Error while transforming Geometry CRS on ' + str(geom.exportToWkt()), 'Error'))
                print 'Bei der Transformation der Geometrie ' + str(geom.exportToWkt()) + ' ist ein Fehler aufgetreten.'
                raise ValueError('Bei der Transformation der Geometrie ' + str(geom.exportToWkt()) + ' ist ein Fehler aufgetreten.')                
        else:
            #keep the projection
            pass
        return geom
    
    #This function compares the geometry type of 2 QgsMapLayer-Objects
    def isSameLayerGeometryType(self, sourceLayer, targetLayer):
        srcTyp=self.sourceLayer.geometryType()
        tarTyp=self.targetLayer.geometryType()
        if tarTyp == srcTyp:
            return True
        else:
            return False

    #This function compare the geometry type of 2 QgsGeometry-Objects
    def isSameGeometryType(self, sourceGeom, targetGeom):
        srcTyp=sourceGeom.wkbType()
        tarTyp=targetGeom.wkbType()
        if tarTyp == srcTyp:
            return True
        else:
            return False

    def getGeomRuleGeomType(self, geometryExpression):
        feats, anzAbsolute=self.getFeatures() #get All features or the selected
        srcFeature=None
        for srcFeature in feats: # process the first feature
            #need only the first feature
            break
        #srcFeature=self.sourceLayer.getFeatures().next()

        hasError, geom = self.generateGeometry(srcFeature, geometryExpression)
        if hasError==False:
            return geom.wkbType(),True #.type()
            print 'Geometry-Rule ResultType: '+str(geom.wkbType())#+' '+self.wkbTypes[geom.wkbType()]
        else:
            print 'Geometry-Rule Problem while checking Geometry-Type ' #+'Geometry-Rule ResultType: '+str(geom.wkbType())+' '+self.wkbTypes[geom.wkbType()]
            return None, False

    #This function compare the CRS of 2 QgsMapLayer-Objects
    def isSameLayerCrs(self, layer1, layer2):
        crs1=layer1.crs()
        crs2=layer2.crs()
        if crs1==crs2:
            return True
        else:
            return False

    #This function is setting the Transformation Parameters for the CRS-Transformation
    def setCrsTransformData(self, sourceLayer, targetLayer):
        srcCrs=sourceLayer.crs()
        tarCrs=targetLayer.crs()
        self.transformCrs=QgsCoordinateTransform(srcCrs, tarCrs)

    #This function delivers the TypeName of a geometryType
    def setGeomTypeNames(self):
    
        wkbTypes = {}
        wkbTypes[0] = 'Unknown'
        wkbTypes[1] = 'Point'
        wkbTypes[2] = 'LineString'
        wkbTypes[3] = 'Polygon'
        wkbTypes[4] = 'MultiPoint'
        wkbTypes[5] = 'MultiLineString'
        wkbTypes[6] = 'MultiPolygon'
        wkbTypes[7] = 'GeometryCollection'
        wkbTypes[8] = 'CircularString'
        wkbTypes[9] = 'CompoundCurve'
        wkbTypes[10] = 'CurvePolygon'
        wkbTypes[11] = 'MultiCurve'
        wkbTypes[12] = 'MultiSurface'
        wkbTypes[100] = 'NoGeometry'
        wkbTypes[1001] = 'PointZ'
        wkbTypes[1002] = 'LineStringZ'
        wkbTypes[1003] = 'PolygonZ'
        wkbTypes[1004] = 'MultiPointZ'
        wkbTypes[1005] = 'MultiLineStringZ'
        wkbTypes[1006] = 'MultiPolygonZ'
        wkbTypes[1007] = 'GeometryCollectionZ'
        wkbTypes[1008] = 'CircularStringZ'
        wkbTypes[1009] = 'CompoundCurveZ'
        wkbTypes[1010] = 'CurvePolygonZ'
        wkbTypes[1011] = 'MultiCurveZ'
        wkbTypes[1012] = 'MultiSurfaceZ'
        wkbTypes[2001] = 'PointM'
        wkbTypes[2002] = 'LineStringM'
        wkbTypes[2003] = 'PolygonM'
        wkbTypes[2004] = 'MultiPointM'
        wkbTypes[2005] = 'MultiLineStringM'
        wkbTypes[2006] = 'MultiPolygonM'
        wkbTypes[2007] = 'GeometryCollectionM'
        wkbTypes[2008] = 'CircularStringM'
        wkbTypes[2009] = 'CompoundCurveM'
        wkbTypes[2010] = 'CurvePolygonM'
        wkbTypes[2011] = 'MultiCurveM'
        wkbTypes[2012] = 'MultiSurfaceM'
        wkbTypes[3001] = 'PointZM'
        wkbTypes[3002] = 'LineStringZM'
        wkbTypes[3003] = 'PolygonZM'
        wkbTypes[3004] = 'MultiPointZM'
        wkbTypes[3005] = 'MultiLineStringZM'
        wkbTypes[3006] = 'MultiPolygonZM'
        wkbTypes[3007] = 'GeometryCollectionZM'
        wkbTypes[3008] = 'CircularStringZM'
        wkbTypes[3009] = 'CompoundCurveZM'
        wkbTypes[3010] = 'CurvePolygonZM'
        wkbTypes[3011] = 'MultiCurveZM'
        wkbTypes[3012] = 'MultiSurfaceZM'
        wkbTypes[0x80000001] = 'Point25D, LineString25D, Polygon25D, MultiPoint25D'
        
        print 'WkbType Sample'+wkbTypes[1]
        return wkbTypes