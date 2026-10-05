# Changelog

## 1.0.1
- Security hardening for the official QGIS Plugin Repository.
- Resolved all six Bandit B110/B112 findings caused by silent `try/except: pass`
  and `try/except: continue` patterns.
- Non-fatal geometry-processing exceptions are now recorded in the QGIS log.
- No `.bandit` exclusions and no `# nosec` suppressions are used.
- No change to the analytical methodology or user-facing workflow.

## 1.0.0 — 2026-10-05
- Primeira versão pública estável.
- Autoria e contato incluídos nos metadados.
- Agradecimentos e referências metodológicas documentados.
- Licença GPL-3.0-or-later incluída.
- Ícone próprio do plugin.
- Simbologia automática por número de critérios atendidos.
- Resumo estatístico final.
- Suporte a múltiplas camadas de árvores e áreas protegidas.
- Praças opcionais.
- Campos compatíveis com Shapefile.

## 0.2.0
- Simbologia automática e resumo estatístico.
- Aliases amigáveis e campos curtos.

## 0.1.0
- Primeira versão funcional para QGIS.
