"""Cálculos financieros independientes de la fuente de datos."""

from collections.abc import Mapping
from math import sqrt

import pandas as pd


def calcular_indicadores(historial: pd.DataFrame) -> pd.DataFrame:
    """Devuelve el historial con promedios móviles y retornos diarios."""
    if "Close" not in historial.columns:
        raise ValueError("El historial debe incluir la columna 'Close'.")

    resultado = historial.copy()
    resultado["SMA20"] = resultado["Close"].rolling(20).mean()
    resultado["SMA50"] = resultado["Close"].rolling(50).mean()
    resultado["Retorno Diario"] = resultado["Close"].pct_change()
    return resultado


def obtener_comparativa_balance(balances: pd.DataFrame | None) -> str:
    """Calcula el cambio interanual de activos totales cuando hay datos."""
    if balances is None or balances.empty or len(balances.columns) < 2:
        return "N/A"

    fila_activos = next(
        (indice for indice in balances.index if "Total Assets" in str(indice)),
        None,
    )
    if fila_activos is None:
        return "Sin Activos"

    ultimo_trimestre = pd.Timestamp(balances.columns[0])
    comparables = []
    for columna in balances.columns[1:]:
        diferencia_dias = abs((ultimo_trimestre - pd.Timestamp(columna)).days)
        if 340 <= diferencia_dias <= 390:
            comparables.append((abs(diferencia_dias - 365), columna))

    if comparables:
        trimestre_anterior = min(comparables, key=lambda item: item[0])[1]
    else:
        trimestre_anterior = (
            balances.columns[4] if len(balances.columns) > 4 else balances.columns[-1]
        )

    activos = balances.loc[fila_activos]
    activos_actuales = activos.iloc[0]
    activos_anteriores = activos.loc[trimestre_anterior]
    if (
        pd.isna(activos_actuales)
        or pd.isna(activos_anteriores)
        or activos_anteriores == 0
    ):
        return "N/A"

    cambio = ((activos_actuales - activos_anteriores) / activos_anteriores) * 100
    return f"{cambio:.2f}%"


def resumen_financiero(
    nombre: str,
    ticker: str,
    historial: pd.DataFrame,
    info: Mapping[str, object] | None = None,
    balances: pd.DataFrame | None = None,
) -> dict[str, object]:
    """Calcula métricas de rendimiento a partir de datos históricos."""
    if historial.empty:
        raise ValueError("El historial no contiene datos.")

    datos = calcular_indicadores(historial)
    precios = datos["Close"].dropna()
    if precios.empty:
        raise ValueError("El historial no contiene precios de cierre válidos.")

    retornos = datos["Retorno Diario"].dropna()
    desviacion = float(retornos.std()) if len(retornos) > 1 else 0.0
    volatilidad = desviacion * sqrt(252) * 100
    sharpe = (
        float(retornos.mean()) / desviacion * sqrt(252)
        if desviacion > 0
        else 0.0
    )
    volumen = (
        int(historial["Volume"].mean())
        if "Volume" in historial.columns and historial["Volume"].notna().any()
        else "N/A"
    )
    metadatos = info or {}

    return {
        "Empresa": nombre,
        "Ticker": ticker,
        "Precio Actual": round(float(precios.iloc[-1]), 2),
        "Precio Máximo": round(float(historial["High"].max()), 2)
        if "High" in historial.columns
        else round(float(precios.max()), 2),
        "Precio Mínimo": round(float(historial["Low"].min()), 2)
        if "Low" in historial.columns
        else round(float(precios.min()), 2),
        "Rendimiento %": round(
            (float(precios.iloc[-1]) / float(precios.iloc[0]) - 1) * 100, 2
        ),
        "Volatilidad %": round(volatilidad, 2),
        "Sharpe Ratio": round(sharpe, 2),
        "Volumen Promedio": volumen,
        "Crec. Activos Trimestral YoY": obtener_comparativa_balance(balances),
        "Market Cap": metadatos.get("marketCap", "N/A"),
        "Sector": metadatos.get("sector", "N/A"),
        "Dividend Yield": metadatos.get("dividendYield", "N/A"),
    }
