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
from qgis.core import *
from qgis.gui import *

# initialize Qt resources from file resouces.py
import resources


from dialogs import SchemaTransformDialog
#from griddrawer import GridDrawer


class SchemaPlugin:

  layerList=[]
  layers=[]
  sourceLayer=None
  targetLayer=None
  
  def __init__(self, iface):
    # save reference to the QGIS interface
    self.iface = iface
    self.canvas = iface.mapCanvas()                 # Flaeche, auf der die Geometrien gezeichnet werden
    #self.gridDrawer = GridDrawer(self.canvas)
    self.mapTool = QgsMapToolEmitPoint(self.canvas) # Mit diesem Maptool kann man die Koordinaten abfangen, wenn jemand auf den MapCanvas klickt

  def initGui(self):
    # create action that will start plugin configuration
    self.action = QAction(QIcon(":/plugins/Small-ETL/icon.png"), "Small-ETL Schema Transformator", \
      self.iface.mainWindow())
    self.action.setWhatsThis("Schema-Transformator")
    self.action.setStatusTip("This is status tip")
    QObject.connect(self.action, SIGNAL("triggered()"), self.run)

    # Fuegt Menueeintrag im Hauptmenue hinzu
    # self.mmqgis_menu = QMenu(QCoreApplication.translate("probenahme", "Probenahme"))
    # self.iface.mainWindow().menuBar().insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.mmqgis_menu)
    # self.mmqgis_menu.addAction(self.action)

    # add toolbar button and menu item
    self.iface.addVectorToolBarIcon(self.action)
    self.iface.addPluginToVectorMenu(u'&Small-ETL',self.action)

    # connect to signal renderComplete which is emitted when canvas
    # rendering is done
    # QObject.connect(self.iface.mapCanvas(), SIGNAL("renderComplete(QPainter *)"), \
    #   self.renderTest)

  def unload(self):
    # remove the plugin menu item and icon
    self.iface.removePluginVectorMenu(u'&Small-ETL',self.action)
    self.iface.removeVectorToolBarIcon(self.action)
    # disconnect form signal of the canvas
    # QObject.disconnect(self.iface.mapCanvas(), SIGNAL("renderComplete(QPainter *)"), \
    #   self.renderTest)

  def run(self):
    # create and show a configuration dialog or something similar
    print "TestPlugin: run called!"
    self.points = []                               # Liste der Punkte, die angeklickt werden
    self.dialog = SchemaTransformDialog(self)
    self.dialog.show()


