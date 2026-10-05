# Copyright (C) 2026 Pítolas Armini B. da Silva
# SPDX-License-Identifier: GPL-3.0-or-later

from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication
import processing
from .provider import Analise330300Provider

class Analise330300Plugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.action = None

    def initGui(self):
        self.provider = Analise330300Provider()
        QgsApplication.processingRegistry().addProvider(self.provider)
        self.action = QAction('Análise 3-30-300', self.iface.mainWindow())
        self.action.setToolTip('Executar análise parametrizável 3-30-300')
        self.action.triggered.connect(self.run_algorithm)
        self.iface.addPluginToVectorMenu('Análise 3-30-300', self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginVectorMenu('Análise 3-30-300', self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.deleteLater()
            self.action = None
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

    def run_algorithm(self):
        processing.execAlgorithmDialog('analise330300:executar')
