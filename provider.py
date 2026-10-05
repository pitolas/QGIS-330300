# Copyright (C) 2026 Pítolas Armini B. da Silva
# SPDX-License-Identifier: GPL-3.0-or-later

from qgis.core import QgsProcessingProvider
from .algorithm import Analise330300Algorithm

class Analise330300Provider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(Analise330300Algorithm())
    def id(self):
        return 'analise330300'
    def name(self):
        return 'Análise 3-30-300'
    def longName(self):
        return 'Análise 3-30-300 — Infraestrutura Verde'
