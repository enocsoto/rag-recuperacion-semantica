# Recuperación semántica local

RAG sobre documentos de la plataforma Norte. Los archivos de `data/` se parten por tokens, se guardan en Chroma en disco y una cadena LCEL responde solo con esos fragmentos. Si la respuesta no está en el contexto, el modelo debe decir «No lo sé».

Los embeddings son el modelo local por defecto de Chroma, el mismo al indexar y al consultar. El LLM es aparte y lee la clave desde el entorno.

## Cómo instalar

Requiere Python 3.12.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
cp .env.example .env
```

Completa en `.env` la clave del proveedor. Para Anthropic, `LLM_PROVIDER=anthropic`.

## Cómo ingestar

```bash
.venv/bin/python ingesta.py
```

Lee `data/*.md` y `data/*.txt`. Parte con 500 tokens y 50 de solapamiento, medidos con `tiktoken` (`cl100k_base`), y hace upsert en `./vectorstore`. Si la colección ya tiene chunks, no vuelve a embeber. Para reindexar: `ingesta.py --force`.

## Cómo preguntar

```bash
.venv/bin/python rag.py
```

Hace dos consultas:

1. La hora UTC del snapshot diario de pedidos y cuántos días se retiene. La respuesta tiene que salir de `respaldos.md` (02:10 UTC y 14 días).
2. Una pregunta trampa sobre vacaciones del equipo. Esa información no está en `data/`. La respuesta esperada es «No lo sé» y `referencias` vacío.

`get_rag_response(query)` busca los 4 fragmentos más cercanos, arma el prompt y llama al modelo con `.ainvoke()`. La salida es un `RespuestaRAG` con `respuesta` y `referencias`.

## Dataset

| Archivo | Qué fija |
| --- | --- |
| `data/respaldos.md` | Job `norte-backup-pedidos`, snapshot 02:10 UTC, retención diaria de 14 días |
| `data/restauracion.md` | Rol `plataforma-oncall`, clúster `norte-restore`, tope de 45 minutos |
| `data/retencion.md` | Semanales 90 días, logs 7 días en Loki, métricas 30 días |
| `data/accesos.md` | MFA, rotación cada 60 días, prohibido usar `norte-root` |

## Variables

| Variable | Uso |
| --- | --- |
| `LLM_PROVIDER` | `openai` (por defecto) o `anthropic` |
| `OPENAI_API_KEY` | Obligatoria si el proveedor es `openai` |
| `ANTHROPIC_API_KEY` | Obligatoria si el proveedor es `anthropic` |
| `VECTORSTORE_PATH` | Carpeta de Chroma. Por defecto `./vectorstore` |

No pongas claves en el código. `vectorstore/` no se versiona.

## Tests

No llaman al LLM. La primera corrida descarga el embedding local de Chroma.

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Cadena

`preparar` recupera de Chroma. Después la cadena es `recuperación | prompt | modelo | PydanticOutputParser`, con un reintento si el JSON no cumple el esquema.
