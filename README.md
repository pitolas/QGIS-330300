# Análise 3-30-300 para QGIS

Plugin independente para **QGIS** destinado à análise espacial parametrizável da regra **3-30-300** aplicada à infraestrutura verde urbana.

## Autoria

**Pítolas Armini B. da Silva**  
Geógrafo  
Contato: **arminipitolas@gmail.com**

Desenvolvimento e implementação do plugin **Análise 3-30-300 para QGIS**.

## Agradecimentos

Agradecimento especial a **Ramon Negrão Santos Junior, Eng. Florestal**, pela contribuição técnica e pelas discussões relacionadas à aplicação dos critérios da regra 3-30-300 à análise da infraestrutura verde urbana.

## Metodologia

A regra 3-30-300 utiliza, de forma geral, três referências para a presença de natureza no ambiente urbano:

- **3** — visualização de pelo menos três árvores a partir dos locais de permanência;
- **30** — aproximadamente 30% de cobertura arbórea no bairro;
- **300** — acesso a um espaço verde público a até 300 metros.

### Adaptação espacial utilizada pelo plugin

O primeiro critério não é reproduzido literalmente como “árvores visíveis da janela”. Para permitir sua aplicação por geoprocessamento, o plugin representa esse componente pela **quantidade de árvores existentes no entorno do lote**, dentro de uma distância configurável pelo usuário.

Os três parâmetros são configuráveis. Portanto, o plugin também pode ser utilizado em cenários como **5-25-500**, sem alteração do código.

## O que o plugin analisa

1. **Árvores no entorno dos lotes** — número mínimo de árvores dentro de uma distância configurável;
2. **Cobertura arbórea por bairro** — percentual mínimo definido pelo usuário;
3. **Proximidade a áreas verdes** — distância máxima até parques/áreas protegidas, com possibilidade de incluir praças.

## Entradas principais

- camada de lotes;
- uma ou mais camadas de árvores;
- uma ou mais camadas de parques/áreas protegidas;
- camada de bairros;
- camada de cobertura arbórea;
- praças, opcionalmente.

## Saídas

### Lotes analisados

Todos os lotes permanecem na saída e recebem indicadores diagnósticos:

| Campo | Significado |
|---|---|
| `N_ARVORES` | Número de árvores no entorno definido |
| `DIST_VERDE` | Distância, quando encontrada no raio de análise, à área verde mais próxima |
| `BAIRRO330` | Bairro associado ao lote |
| `PERC_COPA` | Percentual de cobertura arbórea do bairro |
| `OK_ARV` | Atende ao critério de árvores |
| `OK_COPA` | Atende ao critério de cobertura arbórea |
| `OK_VERDE` | Atende ao critério de proximidade à área verde |
| `N_CRIT` | Número de critérios atendidos, de 0 a 3 |
| `ATENDE330` | 1 quando o lote atende aos três critérios |

### Lotes que atendem aos três critérios

Camada contendo apenas os lotes com `ATENDE330 = 1`.

### Bairros com percentual de cobertura

Inclui área do bairro, área de copa, percentual de cobertura e indicador de atendimento ao limite definido.

## Simbologia

Quando a opção de simbologia automática está habilitada, a camada de lotes é categorizada por `N_CRIT`, permitindo visualizar os lotes que atendem 0, 1, 2 ou 3 critérios. Os bairros também recebem simbologia conforme o atendimento ao percentual mínimo de cobertura.

## Requisitos

- QGIS 3.34 ou superior;
- dados vetoriais adequados às análises;
- camada de lotes em **CRS projetado com unidade em metros**.

As demais camadas são transformadas temporariamente para o CRS dos lotes durante o processamento. As fontes originais não são alteradas.

## Instalação

No QGIS:

**Complementos → Gerenciar e Instalar Complementos → Instalar a partir de ZIP**

Selecione o arquivo `QGIS_330300_v1.0.0.zip`.

A ferramenta ficará disponível em:

- **Vetor → Análise 3-30-300**;
- **Caixa de Ferramentas de Processamento → Análise 3-30-300**.

## Referências da metodologia

CIDADES PELO CLIMA. **A regra 3-30-300: o movimento global que se propõe transformar as cidades através da natureza**. 16 dez. 2025.  
https://cidadespeloclima.pt/2025/12/16/a-regra-3-30-300/

ÁRVORE, SER TECNOLÓGICO. **O que é a regra 3-30-300?**  
https://arvoresertecnologico.com.br/o-que-e-a-regra-3-30-300/

## Licença

Este software é distribuído sob a licença **GNU General Public License v3.0 ou posterior (GPL-3.0-or-later)**. Consulte o arquivo `LICENSE`.

## English summary

**3-30-300 Analysis for QGIS** is a configurable urban green infrastructure analysis plugin. It evaluates tree presence around parcels, neighborhood canopy coverage, and proximity to parks/green spaces. The original “3 visible trees” criterion is operationalized as a configurable count of mapped trees around each parcel.


## v1.0.1 — Security hardening

This release resolves the six Bandit findings reported by the official QGIS
Plugin Repository. Non-fatal geometry-processing exceptions are now logged
instead of being silently ignored. The analysis methodology is unchanged.
