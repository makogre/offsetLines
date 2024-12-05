from PyQt5.QtWidgets import QAction, QInputDialog, QMessageBox, QComboBox, QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QIcon
from qgis.core import QgsVectorLayer, QgsFeature, QgsUnitTypes
import processing
import os

class offsetLines:
    def __init__(self, iface):
        """
        Initialisiert das Plugin.
        :param iface: Die QGIS-Schnittstelle.
        """
        self.iface = iface  # Speichert das iface-Objekt
        self.action = None  # Platzhalter für die Toolbar-Schaltfläche
        self.plugin_dir = os.path.dirname(__file__)  # Plugin-Verzeichnis

    def initGui(self):
        """
        Fügt die GUI-Elemente (Toolbar-Schaltfläche und Menüeintrag) hinzu.
        """
        # Icon-Pfad
        icon_path = os.path.join(self.plugin_dir, "icon.png")

        # Aktion erstellen
        self.action = QAction(QIcon(icon_path), "Offset Lines", self.iface.mainWindow())
        self.action.triggered.connect(self.run)  # Verknüpfe die Aktion mit der Hauptfunktion

        # Symbolleiste hinzufügen
        self.iface.addToolBarIcon(self.action)

        # Menüeintrag hinzufügen
        self.iface.addPluginToMenu("&Offset Lines", self.action)

    def unload(self):
        """
        Entfernt die GUI-Elemente beim Deaktivieren des Plugins.
        """
        if self.action:
            # Entferne die Aktion aus der Symbolleiste und dem Menü
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginMenu("&Offset Lines", self.action)

    def run(self):
        """
        Führt die Hauptlogik des Plugins aus.
        """
        layer = self.iface.activeLayer()

        # Überprüfen, ob ein Layer ausgewählt wurde
        if not layer:
            self.iface.messageBar().pushMessage("Error", "No active layer selected.", level=3)
            return

        # Überprüfen, ob es sich um einen Vektor-Layer handelt
        if not isinstance(layer, QgsVectorLayer):
            self.iface.messageBar().pushMessage("Error", "The selected layer is not a vector layer.", level=3)
            return

        # Features prüfen
        selected_features = layer.selectedFeatures()
        if len(selected_features) == 0:
            self.iface.messageBar().pushMessage("Error", "Please select a line feature.", level=3)
            return

        # Benutzer gibt den Versatzwert ein
        x, ok = QInputDialog.getDouble(None, "Enter offset value", "Offset in meters:", decimals=2)
        if not ok:
            return

        # Benutzer wählt die Seite aus
        side_dialog = QDialog()
        side_dialog.setWindowTitle("Select side")
        layout = QVBoxLayout()

        label = QLabel("Select side:")
        layout.addWidget(label)

        combo = QComboBox()
        combo.addItems(["Both sides", "Right side", "Left side"])
        layout.addWidget(combo)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(side_dialog.accept)
        layout.addWidget(ok_button)

        side_dialog.setLayout(layout)
        if not side_dialog.exec_():
            return

        selected_side = combo.currentText()

        # Bestimmen der Versatzabstände basierend auf der Auswahl
        if selected_side == "Both sides":
            distances = [x, -x]
        elif selected_side == "Right side":
            distances = [-x]
        else:  # Nur links
            distances = [x]

        # Überprüfen, ob das CRS metrische Einheiten verwendet
        crs = layer.crs()
        if not crs.mapUnits() == QgsUnitTypes.DistanceMeters:
            self.iface.messageBar().pushMessage(
                "Warning", 
                "The layer uses non-metric units. Temporarily transformed to EPSG:3857 (meters).", 
                level=2
            )
            # Temporärer Layer mit EPSG:3857 (metrisches CRS)
            transformed_layer = processing.run("native:reprojectlayer", {
                'INPUT': layer,
                'TARGET_CRS': 'EPSG:3857',
                'OUTPUT': 'memory:'
            })['OUTPUT']
        else:
            transformed_layer = layer

        # Temporären Layer erstellen
        temp_layer = QgsVectorLayer("LineString?crs=" + transformed_layer.crs().authid(), "temp_layer", "memory")
        temp_layer_data = temp_layer.dataProvider()
        temp_layer_data.addAttributes(transformed_layer.fields())
        temp_layer.updateFields()
        temp_layer.startEditing()

        for feature in selected_features:
            temp_layer.addFeature(feature)
        temp_layer.commitChanges()

        if not layer.isEditable():
            layer.startEditing()

        for dist in distances:
            params = {
                'INPUT': temp_layer,
                'DISTANCE': dist,
                'SEGMENTS': 8,
                'JOIN_STYLE': 1,
                'MITER_LIMIT': 2,
                'DISSOLVE': False,
                'OUTPUT': 'memory:'
            }
            result = processing.run("native:offsetline", params)
            offset_layer = result['OUTPUT']

            for offset_feature in offset_layer.getFeatures():
                new_feature = QgsFeature()
                new_feature.setGeometry(offset_feature.geometry())
                new_feature.setAttributes(offset_feature.attributes())
                layer.addFeature(new_feature)

        layer.commitChanges()
        self.iface.messageBar().pushMessage("Success", "Offset lines created successfully.", level=1)
