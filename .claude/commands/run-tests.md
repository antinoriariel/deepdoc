---
description: Ejecuta la suite de tests con cobertura y muestra resumen.
allowed-tools: Bash
---

1. Correr: `pytest tests/ -v --cov=src --cov-report=term-missing`
2. Mostrar resumen de tests pasados/fallidos
3. Si hay fallos, analizar la causa y proponer fix
