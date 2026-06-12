---
description: Extrae y convierte un documento a Markdown usando el pipeline completo.
allowed-tools: Bash, Read, Write
---

Ejecuta el pipeline de extracción sobre el archivo indicado por el usuario.

1. Verificar que el archivo existe con `ls` o `Get-ChildItem`
2. Correr: `python extract.py $ARGUMENTS --verbose`
3. Mostrar las primeras 50 líneas del `.md` generado
4. Reportar motor usado, páginas procesadas y errores si los hay
