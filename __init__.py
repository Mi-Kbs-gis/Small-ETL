# -*- coding: utf-8 -*-
"""
/***************************************************************************
    Small-ETL
	A QGIS plugin to perform schema transformations and data integration of QGIS vectorlayers
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
def name():
    return "Small-ETL"
    
def description():
    return "A QGIS plugin to perform schema transformations and data integration of QGIS vectorlayers"
    
def version():
    return "Version 1.1"
    
def qgisMinimumVersion():
    return "1.0"
    
def authorName():
    return "Michael Kürbs (TLUG Thüringen)"
    
def classFactory(iFace):
    from plugin import SchemaPlugin
    return SchemaPlugin(iFace)