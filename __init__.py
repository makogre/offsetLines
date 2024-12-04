# -*- coding: utf-8 -*-
"""
/***************************************************************************
 offsetLines
                                 A QGIS plugin
 This plugin lets you offset lines parallel to its original in a variable distance
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-12-04
        copyright            : (C) 2024 by makogre
        email                : maximiliangrell97@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
    from .offset_lines import offsetLines
    return offsetLines(iface)
