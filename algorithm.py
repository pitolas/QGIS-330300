# Copyright (C) 2026 Pítolas Armini B. da Silva
# SPDX-License-Identifier: GPL-3.0-or-later

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsCategorizedSymbolRenderer,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsMessageLog,
    Qgis,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDistance,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterNumber,
    QgsRendererCategory,
    QgsSingleSymbolRenderer,
    QgsSpatialIndex,
    QgsSymbol,
    QgsVectorLayer,
)

_POST_PROCESSORS = []


class _LotsStylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    def postProcessLayer(self, layer, context, feedback):
        if not isinstance(layer, QgsVectorLayer):
            return
        aliases = {
            'N_ARVORES': 'Nº de árvores no entorno',
            'DIST_VERDE': 'Distância à área verde (m)',
            'BAIRRO330': 'Bairro',
            'PERC_COPA': 'Cobertura arbórea do bairro (%)',
            'OK_ARV': 'Atende critério de árvores',
            'OK_COPA': 'Atende critério de cobertura',
            'OK_VERDE': 'Atende critério de área verde',
            'N_CRIT': 'Nº de critérios atendidos',
            'ATENDE330': 'Atende aos 3 critérios',
        }
        for name, alias in aliases.items():
            idx = layer.fields().indexFromName(name)
            if idx >= 0:
                layer.setFieldAlias(idx, alias)
        if layer.fields().indexFromName('N_CRIT') < 0:
            return
        spec = [
            (0, '0 critérios', QColor(198,40,40)),
            (1, '1 critério', QColor(239,108,0)),
            (2, '2 critérios', QColor(251,192,45)),
            (3, '3 critérios — atende', QColor(46,125,50)),
        ]
        cats=[]
        for value,label,color in spec:
            sym = QgsSymbol.defaultSymbol(layer.geometryType())
            if sym is None: continue
            sym.setColor(color); sym.setOpacity(0.70)
            cats.append(QgsRendererCategory(value, sym, label))
        if cats:
            layer.setRenderer(QgsCategorizedSymbolRenderer('N_CRIT', cats))
            layer.triggerRepaint()


class _ApprovedStylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    def postProcessLayer(self, layer, context, feedback):
        if not isinstance(layer, QgsVectorLayer):
            return
        sym = QgsSymbol.defaultSymbol(layer.geometryType())
        if sym is not None:
            sym.setColor(QColor(46,125,50)); sym.setOpacity(0.70)
            layer.setRenderer(QgsSingleSymbolRenderer(sym))
            layer.triggerRepaint()


class _NeighborhoodStylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    def postProcessLayer(self, layer, context, feedback):
        if not isinstance(layer, QgsVectorLayer):
            return
        aliases = {
            'AREA_BAIR': 'Área do bairro',
            'AREA_COPA': 'Área de cobertura arbórea',
            'PERC_COPA': 'Cobertura arbórea (%)',
            'OK_COPA': 'Atende cobertura mínima',
        }
        for name, alias in aliases.items():
            idx=layer.fields().indexFromName(name)
            if idx>=0: layer.setFieldAlias(idx, alias)
        if layer.fields().indexFromName('OK_COPA') < 0:
            return
        cats=[]
        for value,label,color in [
            (0,'Abaixo da cobertura mínima',QColor(198,40,40)),
            (1,'Atende cobertura mínima',QColor(46,125,50)),
        ]:
            sym=QgsSymbol.defaultSymbol(layer.geometryType())
            if sym is None: continue
            sym.setColor(color); sym.setOpacity(0.55)
            cats.append(QgsRendererCategory(value,sym,label))
        if cats:
            layer.setRenderer(QgsCategorizedSymbolRenderer('OK_COPA',cats))
            layer.triggerRepaint()


class Analise330300Algorithm(QgsProcessingAlgorithm):
    LOTES='LOTES'; ARVORES='ARVORES'; AREAS_VERDES='AREAS_VERDES'; MIN_ARVORES='MIN_ARVORES'; DIST_ARVORES='DIST_ARVORES'; DIST_VERDE='DIST_VERDE'; BAIRROS='BAIRROS'; COBERTURA='COBERTURA'; MIN_COBERTURA='MIN_COBERTURA'; PRACAS='PRACAS'; INCLUIR_PRACAS='INCLUIR_PRACAS'; APLICAR_ESTILO='APLICAR_ESTILO'; OUT_LOTES='OUT_LOTES'; OUT_ATENDEM='OUT_ATENDEM'; OUT_BAIRROS='OUT_BAIRROS'

    def createInstance(self): return Analise330300Algorithm()
    def name(self): return 'executar'
    def displayName(self): return 'Executar Análise 3-30-300'
    def group(self): return 'Infraestrutura Verde'
    def groupId(self): return 'infraestrutura_verde'
    def shortHelpString(self):
        return ('Analisa os lotes por três critérios parametrizáveis:\n\n'
                '1) quantidade mínima de árvores dentro de uma distância do lote;\n'
                '2) percentual mínimo de cobertura arbórea do bairro;\n'
                '3) distância máxima do lote até parques/áreas protegidas, com praças opcionais.\n\n'
                'A camada original não é alterada. As saídas recebem campos de diagnóstico.')

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.LOTES,'1. Camada de Lotes (Geral)',[QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterMultipleLayers(self.ARVORES,'2. Camada(s) de Árvores',layerType=QgsProcessing.TypeVectorPoint,optional=False))
        self.addParameter(QgsProcessingParameterMultipleLayers(self.AREAS_VERDES,'3. Camada(s) de Parques / Áreas Protegidas',layerType=QgsProcessing.TypeVectorPolygon,optional=False))
        self.addParameter(QgsProcessingParameterNumber(self.MIN_ARVORES,'4. Nº mínimo de Árvores (Proximidade)',type=QgsProcessingParameterNumber.Integer,defaultValue=3,minValue=0))
        self.addParameter(QgsProcessingParameterDistance(self.DIST_ARVORES,'5. Distância máx. até Árvores (metros)',defaultValue=50,parentParameterName=self.LOTES,minValue=0))
        self.addParameter(QgsProcessingParameterDistance(self.DIST_VERDE,'6. Distância máx. até Parques / Áreas Verdes (metros)',defaultValue=300,parentParameterName=self.LOTES,minValue=0))
        self.addParameter(QgsProcessingParameterFeatureSource(self.BAIRROS,'7. Camada de Bairros (Geral)',[QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.COBERTURA,'8. Camada de Cobertura Arbórea (Mapeamento)',[QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterNumber(self.MIN_COBERTURA,'9. Percentual mínimo de Cobertura Arbórea no Bairro (%)',type=QgsProcessingParameterNumber.Double,defaultValue=30.0,minValue=0.0,maxValue=100.0))
        self.addParameter(QgsProcessingParameterBoolean(self.INCLUIR_PRACAS,'10. Incluir Praças como áreas verdes',defaultValue=False))
        self.addParameter(QgsProcessingParameterMultipleLayers(self.PRACAS,'11. Camada(s) de Praças (opcional)',layerType=QgsProcessing.TypeVectorPolygon,optional=True))
        self.addParameter(QgsProcessingParameterBoolean(self.APLICAR_ESTILO,'12. Aplicar simbologia automática às saídas',defaultValue=True))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUT_LOTES,'13. Saída — Lotes analisados',type=QgsProcessing.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUT_ATENDEM,'14. Saída — Lotes que atendem aos 3 critérios',type=QgsProcessing.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUT_BAIRROS,'15. Saída — Bairros com percentual de cobertura',type=QgsProcessing.TypeVectorPolygon))

    def _safe_geom(self, geom):
        if geom is None or geom.isEmpty(): return QgsGeometry()
        g=QgsGeometry(geom)
        try:
            if not g.isGeosValid():
                fixed=g.makeValid()
                if fixed and not fixed.isEmpty(): g=fixed
        except Exception as exc:
            QgsMessageLog.logMessage(
                "Falha não crítica ao validar/corrigir geometria: {}".format(exc),
                "Análise 3-30-300",
                level=Qgis.MessageLevel.Warning,
            )
        return g

    def _transform_geom(self, geom, src_crs, dst_crs, context):
        g=self._safe_geom(geom)
        if g.isEmpty() or src_crs==dst_crs: return g
        tr=QgsCoordinateTransform(src_crs,dst_crs,context.transformContext())
        g.transform(tr)
        return g

    def _append_field_if_missing(self, fields, field):
        if fields.indexFromName(field.name())<0: fields.append(field)

    def _name_field(self, source):
        names=[f.name() for f in source.fields()]
        lower={n.casefold():n for n in names}
        for p in ('nome','nomebairro','bairro','name','descricao'):
            if p in lower: return lower[p]
        for n in names:
            low=n.casefold()
            if 'nome' in low or 'bairro' in low or 'name' in low: return n
        return None

    def _index_from_layers(self, layers, work_crs, context, feedback):
        idx=QgsSpatialIndex(); geoms={}; next_id=1
        for layer in layers:
            if layer is None: continue
            for feat in layer.getFeatures():
                if feedback.isCanceled(): break
                g=self._transform_geom(feat.geometry(),layer.crs(),work_crs,context)
                if g.isEmpty(): continue
                f=QgsFeature(); f.setId(next_id); f.setGeometry(g); idx.addFeature(f)
                geoms[next_id]=g; next_id+=1
        return idx,geoms

    def _coverage_for_neighborhoods(self,bairros,cobertura,work_crs,context,feedback):
        cov_index=QgsSpatialIndex(); cov_geoms={}; next_id=1
        for feat in cobertura.getFeatures():
            if feedback.isCanceled(): break
            g=self._transform_geom(feat.geometry(),cobertura.sourceCrs(),work_crs,context)
            if g.isEmpty(): continue
            f=QgsFeature(); f.setId(next_id); f.setGeometry(g); cov_index.addFeature(f); cov_geoms[next_id]=g; next_id+=1
        name_field=self._name_field(bairros); results={}; total=max(1,bairros.featureCount())
        for pos,feat in enumerate(bairros.getFeatures()):
            if feedback.isCanceled(): break
            bg=self._transform_geom(feat.geometry(),bairros.sourceCrs(),work_crs,context)
            if bg.isEmpty(): continue
            area_bairro=bg.area(); parts=[]
            for cid in cov_index.intersects(bg.boundingBox()):
                cg=cov_geoms.get(cid)
                if cg is None or cg.isEmpty(): continue
                try:
                    if bg.intersects(cg):
                        inter=bg.intersection(cg)
                        if inter and not inter.isEmpty(): parts.append(inter)
                except Exception as exc:
                    QgsMessageLog.logMessage(
                        "Falha não crítica ao intersectar cobertura e bairro: {}".format(exc),
                        "Análise 3-30-300",
                        level=Qgis.MessageLevel.Warning,
                    )
            if parts:
                try:
                    union=QgsGeometry.unaryUnion(parts); area_copa=union.area() if union and not union.isEmpty() else 0.0
                except Exception:
                    area_copa=sum(p.area() for p in parts)
            else: area_copa=0.0
            perc=(area_copa*100.0/area_bairro) if area_bairro>0 else 0.0
            nome=str(feat[name_field]) if name_field else str(feat.id())
            results[feat.id()]={'geom':bg,'nome':nome,'area_bairro':area_bairro,'area_copa':area_copa,'perc_copa':perc}
            feedback.setProgress(15.0*(pos+1)/total)
        idx=QgsSpatialIndex()
        for fid,row in results.items():
            f=QgsFeature(); f.setId(fid); f.setGeometry(row['geom']); idx.addFeature(f)
        return results,idx

    def _bairro_for_lot(self,lot_geom,bairro_results,bairro_index):
        if lot_geom is None or lot_geom.isEmpty(): return None
        centroid=lot_geom.centroid(); candidates=bairro_index.intersects(lot_geom.boundingBox())
        for fid in candidates:
            try:
                if bairro_results[fid]['geom'].contains(centroid): return bairro_results[fid]
            except Exception as exc:
                QgsMessageLog.logMessage(
                    "Falha não crítica no teste de contenção do lote no bairro: {}".format(exc),
                    "Análise 3-30-300",
                    level=Qgis.MessageLevel.Warning,
                )
        best=None; best_area=-1.0
        for fid in candidates:
            bg=bairro_results[fid]['geom']
            try:
                if not bg.intersects(lot_geom): continue
                a=bg.intersection(lot_geom).area()
                if a>best_area: best_area=a; best=bairro_results[fid]
            except Exception as exc:
                QgsMessageLog.logMessage(
                    "Falha não crítica ao calcular a interseção lote/bairro: {}".format(exc),
                    "Análise 3-30-300",
                    level=Qgis.MessageLevel.Warning,
                )
        return best

    def _register_post_processor(self,context,dest_id,processor):
        global _POST_PROCESSORS
        _POST_PROCESSORS.append(processor)
        details=context.layerToLoadOnCompletionDetails(dest_id)
        details.setPostProcessor(processor)

    def processAlgorithm(self,parameters,context,feedback):
        lotes=self.parameterAsSource(parameters,self.LOTES,context); bairros=self.parameterAsSource(parameters,self.BAIRROS,context); cobertura=self.parameterAsSource(parameters,self.COBERTURA,context)
        if lotes is None or bairros is None or cobertura is None: raise QgsProcessingException('Uma ou mais camadas obrigatórias não puderam ser abertas.')
        arvores=self.parameterAsLayerList(parameters,self.ARVORES,context); areas_verdes=self.parameterAsLayerList(parameters,self.AREAS_VERDES,context)
        incluir_pracas=self.parameterAsBool(parameters,self.INCLUIR_PRACAS,context); pracas=self.parameterAsLayerList(parameters,self.PRACAS,context) if incluir_pracas else []
        aplicar_estilo=self.parameterAsBool(parameters,self.APLICAR_ESTILO,context)
        if not arvores: raise QgsProcessingException('Informe pelo menos uma camada de árvores.')
        if not areas_verdes: raise QgsProcessingException('Informe pelo menos uma camada de parques/áreas protegidas.')
        min_arvores=self.parameterAsInt(parameters,self.MIN_ARVORES,context); dist_arvores=self.parameterAsDouble(parameters,self.DIST_ARVORES,context); dist_verde=self.parameterAsDouble(parameters,self.DIST_VERDE,context); min_cobertura=self.parameterAsDouble(parameters,self.MIN_COBERTURA,context)
        work_crs=lotes.sourceCrs()
        if work_crs.isGeographic(): raise QgsProcessingException('A camada de lotes está em CRS geográfico. Use um CRS projetado em metros.')
        feedback.pushInfo('=== ANÁLISE 3-30-300 — v1.0.1 ===')
        feedback.pushInfo('Parâmetros: mínimo {} árvore(s); raio árvores {:.2f} m; cobertura mínima {:.2f}%; distância máxima área verde {:.2f} m.'.format(min_arvores,dist_arvores,min_cobertura,dist_verde))
        tree_index,tree_geoms=self._index_from_layers(arvores,work_crs,context,feedback)
        green_layers=list(areas_verdes); green_layers.extend(pracas if incluir_pracas else [])
        green_index,green_geoms=self._index_from_layers(green_layers,work_crs,context,feedback)
        bairro_results,bairro_index=self._coverage_for_neighborhoods(bairros,cobertura,work_crs,context,feedback)

        bairro_fields=QgsFields(bairros.fields())
        for fld in [QgsField('AREA_BAIR',QVariant.Double),QgsField('AREA_COPA',QVariant.Double),QgsField('PERC_COPA',QVariant.Double),QgsField('OK_COPA',QVariant.Int)]: self._append_field_if_missing(bairro_fields,fld)
        sink_b,dest_b=self.parameterAsSink(parameters,self.OUT_BAIRROS,context,bairro_fields,bairros.wkbType(),work_crs)
        if sink_b is None: raise QgsProcessingException('Não foi possível criar a saída de bairros.')
        bairro_orig={f.id():f for f in bairros.getFeatures()}
        for fid,row in bairro_results.items():
            src=bairro_orig.get(fid)
            if src is None: continue
            vals={bairros.fields()[i].name():src.attributes()[i] for i in range(len(src.attributes()))}
            vals.update({'AREA_BAIR':row['area_bairro'],'AREA_COPA':row['area_copa'],'PERC_COPA':row['perc_copa'],'OK_COPA':1 if row['perc_copa']>=min_cobertura else 0})
            f=QgsFeature(bairro_fields); f.setGeometry(row['geom']); f.setAttributes([vals.get(field.name()) for field in bairro_fields]); sink_b.addFeature(f,QgsFeatureSink.FastInsert)

        out_fields=QgsFields(lotes.fields())
        for fld in [QgsField('N_ARVORES',QVariant.Int),QgsField('DIST_VERDE',QVariant.Double),QgsField('BAIRRO330',QVariant.String,len=120),QgsField('PERC_COPA',QVariant.Double),QgsField('OK_ARV',QVariant.Int),QgsField('OK_COPA',QVariant.Int),QgsField('OK_VERDE',QVariant.Int),QgsField('N_CRIT',QVariant.Int),QgsField('ATENDE330',QVariant.Int)]: self._append_field_if_missing(out_fields,fld)
        sink_all,dest_all=self.parameterAsSink(parameters,self.OUT_LOTES,context,out_fields,lotes.wkbType(),work_crs)
        sink_ok,dest_ok=self.parameterAsSink(parameters,self.OUT_ATENDEM,context,out_fields,lotes.wkbType(),work_crs)
        if sink_all is None or sink_ok is None: raise QgsProcessingException('Não foi possível criar uma das saídas de lotes.')

        total=max(1,lotes.featureCount()); aprovados=0; criteria_counts={0:0,1:0,2:0,3:0}
        for pos,src in enumerate(lotes.getFeatures()):
            if feedback.isCanceled(): break
            g=self._safe_geom(src.geometry())
            if g.isEmpty(): continue
            bt=g.boundingBox(); bt.grow(dist_arvores); n_arvores=0
            for tid in tree_index.intersects(bt):
                tg=tree_geoms.get(tid)
                if tg is None: continue
                try:
                    if g.distance(tg)<=dist_arvores: n_arvores+=1
                except Exception as exc:
                    QgsMessageLog.logMessage(
                        "Falha não crítica ao calcular distância lote/árvore: {}".format(exc),
                        "Análise 3-30-300",
                        level=Qgis.MessageLevel.Warning,
                    )
            bg=g.boundingBox(); bg.grow(dist_verde); min_dist=None
            for gid in green_index.intersects(bg):
                gg=green_geoms.get(gid)
                if gg is None: continue
                try:
                    d=g.distance(gg)
                    if min_dist is None or d<min_dist: min_dist=d
                except Exception as exc:
                    QgsMessageLog.logMessage(
                        "Falha não crítica ao calcular distância lote/área verde: {}".format(exc),
                        "Análise 3-30-300",
                        level=Qgis.MessageLevel.Warning,
                    )
            bairro=self._bairro_for_lot(g,bairro_results,bairro_index); bairro_nome=bairro['nome'] if bairro else ''; perc_copa=bairro['perc_copa'] if bairro else 0.0
            ok_arv=1 if n_arvores>=min_arvores else 0; ok_copa=1 if perc_copa>=min_cobertura else 0; ok_verde=1 if (min_dist is not None and min_dist<=dist_verde) else 0; ncrit=ok_arv+ok_copa+ok_verde; atende=1 if ncrit==3 else 0
            criteria_counts[ncrit]+=1
            vals={lotes.fields()[i].name():src.attributes()[i] for i in range(len(src.attributes()))}
            vals.update({'N_ARVORES':n_arvores,'DIST_VERDE':float(min_dist) if min_dist is not None else None,'BAIRRO330':bairro_nome,'PERC_COPA':float(perc_copa),'OK_ARV':ok_arv,'OK_COPA':ok_copa,'OK_VERDE':ok_verde,'N_CRIT':ncrit,'ATENDE330':atende})
            f=QgsFeature(out_fields); f.setGeometry(g); f.setAttributes([vals.get(field.name()) for field in out_fields]); sink_all.addFeature(f,QgsFeatureSink.FastInsert)
            if atende: sink_ok.addFeature(f,QgsFeatureSink.FastInsert); aprovados+=1
            feedback.setProgress(15+85.0*(pos+1)/total)
        total_proc=sum(criteria_counts.values()); pct=(100.0*aprovados/total_proc) if total_proc else 0.0
        feedback.pushInfo('')
        feedback.pushInfo('=== RESUMO DA ANÁLISE ===')
        feedback.pushInfo('Lotes processados: {}'.format(total_proc))
        feedback.pushInfo('0 critérios atendidos: {}'.format(criteria_counts[0]))
        feedback.pushInfo('1 critério atendido: {}'.format(criteria_counts[1]))
        feedback.pushInfo('2 critérios atendidos: {}'.format(criteria_counts[2]))
        feedback.pushInfo('3 critérios atendidos: {}'.format(criteria_counts[3]))
        feedback.pushInfo('Lotes que atendem aos 3 critérios: {} ({:.2f}%)'.format(aprovados,pct))
        if aplicar_estilo:
            try:
                self._register_post_processor(context,dest_all,_LotsStylePostProcessor())
                self._register_post_processor(context,dest_ok,_ApprovedStylePostProcessor())
                self._register_post_processor(context,dest_b,_NeighborhoodStylePostProcessor())
            except Exception as exc:
                feedback.pushWarning('Saídas criadas, mas a simbologia automática não pôde ser registrada: {}'.format(exc))
        return {self.OUT_LOTES:dest_all,self.OUT_ATENDEM:dest_ok,self.OUT_BAIRROS:dest_b}
