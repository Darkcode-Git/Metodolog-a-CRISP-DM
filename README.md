# Análisis de acciones con Streamlit

Dashboard educativo para consultar precios históricos, promedios móviles y métricas de acciones. La aplicación usa Yahoo Finance mediante `yfinance` y conserva el notebook original como material complementario.

> **Aviso:** este proyecto tiene fines educativos. Los datos pueden tener retrasos, errores o no estar disponibles. El análisis no es asesoría ni una recomendación de inversión.

## Ejecutar localmente

Requiere Python 3.11 o superior.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements-dev.txt
streamlit run app.py
```

La aplicación presenta diez acciones de referencia, precios de un año, medias móviles de 20 y 50 sesiones, rendimiento, volatilidad anualizada, ratio de Sharpe, volumen y metadatos disponibles. Los resultados se almacenan en caché durante 15 minutos para limitar solicitudes repetidas a Yahoo Finance. La disponibilidad de empresas, métricas y cotizaciones depende del proveedor externo.

## Arquitectura

- `app.py`: interfaz Streamlit y consulta de datos externos.
- `analisis_acciones/metricas.py`: cálculos puros reutilizados por la aplicación y las pruebas.
- `tests/`: pruebas deterministas; no requieren acceso a Internet ni datos financieros en vivo.
- `Parra_Juan_Analizando_EA1.ipynb`: notebook original del análisis.
- `.github/workflows/ci.yml`: integración continua en solicitudes de cambios y actualizaciones de `main`.

## Flujo de trabajo DevOps con GitHub

### Ramas, commits y pull requests

1. Crea una rama corta para cada cambio: `git switch -c feature/nombre-del-cambio`.
2. Ejecuta las pruebas localmente con `python -m pytest -q`.
3. Registra cambios pequeños con mensajes claros, por ejemplo `git commit -m "Añade gráfico de medias móviles"`.
4. Publica la rama (`git push -u origin feature/nombre-del-cambio`) y abre un pull request hacia `main`.
5. Revisa los cambios y espera la comprobación **CI / Pruebas** en verde antes de aprobar y fusionar el pull request.
6. Elimina la rama después de la fusión. Mantén `main` como rama de producción.

Se recomienda proteger `main` desde **Settings → Rules → Rulesets**: exigir pull requests, requerir la comprobación **Pruebas** y bloquear inserciones directas. Así, una versión no probada no llega a la rama que observa el despliegue.

### Integración continua (GitHub Actions)

El workflow ejecuta las pruebas con Python 3.11 en cada pull request dirigido a `main` y en cada actualización de `main`. La comprobación de CI debe estar aprobada antes de fusionar cambios; las pruebas usan datos locales simulados para ser reproducibles y no dependen de la API de Yahoo Finance.

### Despliegue continuo (Streamlit Community Cloud)

Streamlit Community Cloud publica y actualiza la aplicación al detectar cambios en la rama configurada. Para habilitar el primer despliegue:

1. Inicia sesión en [Streamlit Community Cloud](https://share.streamlit.io/) y autoriza el repositorio de GitHub.
2. Crea una aplicación seleccionando este repositorio, la rama `main` y el archivo `app.py`.
3. Guarda la URL pública que Streamlit asigna a la aplicación. Los siguientes cambios fusionados a `main` se publican automáticamente.
4. Protege `main` y exige CI según los pasos anteriores; así, la ruta recomendada de despliegue son las fusiones de pull requests con pruebas aprobadas.

La publicación necesita una cuenta autorizada de Streamlit Community Cloud y no puede completarse únicamente desde este repositorio. La aplicación no requiere secretos: consume datos públicos de Yahoo Finance. Si en el futuro se añaden credenciales, deben guardarse en **App settings → Secrets** de Streamlit, nunca en el código ni en GitHub.

## Ejecutar las pruebas

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```
