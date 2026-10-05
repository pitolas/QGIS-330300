# Copyright (C) 2026 Pítolas Armini B. da Silva
# SPDX-License-Identifier: GPL-3.0-or-later

def classFactory(iface):
    from .plugin import Analise330300Plugin
    return Analise330300Plugin(iface)
