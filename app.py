"""Dashboard web para explorar métricas históricas de acciones."""

import pandas as pd
import streamlit as st
import yfinance as yf

from analisis_acciones import calcular_indicadores, resumen_financiero


ACCIONES = {
    "Ecopetrol": "EC",
    "Bancolombia": "CIB",
    "Grupo Aval": "AVAL",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Google": "GOOGL",
    "Amazon": "AMZN",
    "Nvidia": "NVDA",
    "Meta": "META",
    "Tesla": "TSLA",
}


@st.cache_data(ttl=900, show_spinner=False)
def descargar_datos(ticker: str) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Obtiene historial y metadatos de Yahoo Finance; la caché dura 15 minutos."""
    accion = yf.Ticker(ticker)
    historial = accion.history(period="1y")
    if historial is None or historial.empty:
        raise ValueError(f"No se encontraron precios históricos para {ticker}.")
    return historial, accion.info or {}, accion.quarterly_balance_sheet


st.set_page_config(page_title="Análisis de acciones", page_icon="📈", layout="wide")
st.title("Análisis de acciones")
st.caption(
    "Indicadores históricos de Yahoo Finance. Información educativa; "
    "no constituye asesoría financiera."
)

empresa = st.selectbox("Selecciona una empresa", list(ACCIONES))
ticker = ACCIONES[empresa]

with st.spinner(f"Consultando datos de {ticker}..."):
    try:
        historial, info, balances = descargar_datos(ticker)
    except Exception as error:
        st.error(f"No fue posible obtener los datos de {ticker}: {error}")
        st.stop()

indicadores = calcular_indicadores(historial)
resumen = resumen_financiero(empresa, ticker, historial, info, balances)

columnas = st.columns(4)
columnas[0].metric("Precio actual", f"{resumen['Precio Actual']:,.2f}")
columnas[1].metric("Rendimiento del período", f"{resumen['Rendimiento %']:.2f}%")
columnas[2].metric("Volatilidad anualizada", f"{resumen['Volatilidad %']:.2f}%")
columnas[3].metric("Sharpe Ratio", f"{resumen['Sharpe Ratio']:.2f}")

st.subheader(f"Precio de cierre y promedios móviles — {empresa}")
st.line_chart(indicadores[["Close", "SMA20", "SMA50"]])

st.subheader("Resumen")
resumen_visible = {
    "Precio máximo": resumen["Precio Máximo"],
    "Precio mínimo": resumen["Precio Mínimo"],
    "Volumen promedio": resumen["Volumen Promedio"],
    "Variación interanual de activos": resumen["Crec. Activos Trimestral YoY"],
    "Capitalización de mercado": resumen["Market Cap"],
    "Sector": resumen["Sector"],
    "Rendimiento por dividendo": resumen["Dividend Yield"],
}
st.dataframe(
    pd.DataFrame.from_dict(resumen_visible, orient="index", columns=["Valor"]),
    use_container_width=True,
)
st.caption("Los datos se almacenan en caché durante 15 minutos.")
