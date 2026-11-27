"""Dashboard web para explorar métricas históricas de acciones."""

import pandas as pd
import streamlit as st
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from analisis_acciones import (
    calcular_indicadores,
    predecir_tendencia,
    resumen_financiero,
)


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
    historial = accion.history(period="2y", auto_adjust=True)
    if historial is None or historial.empty:
        raise ValueError(f"No se encontraron precios históricos para {ticker}.")
    return historial, accion.info or {}, accion.quarterly_balance_sheet


@st.cache_data(ttl=900, show_spinner=False)
def obtener_prediccion(historial: pd.DataFrame):
    """Reutiliza el entrenamiento mientras los datos financieros estén en caché."""
    return predecir_tendencia(historial)


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
st.line_chart(indicadores[["Close", "SMA5", "SMA20", "SMA50"]])

st.subheader("Predicción del próximo cierre")
try:
    prediccion = obtener_prediccion(historial)
except (TypeError, ValueError) as error:
    st.warning(f"No fue posible entrenar el modelo: {error}")
else:
    columnas_prediccion = st.columns(3)
    columnas_prediccion[0].metric("Tendencia estimada", prediccion.etiqueta)
    columnas_prediccion[1].metric(
        "Probabilidad del pronóstico", f"{prediccion.probabilidad:.1%}"
    )
    precision = (
        f"{prediccion.precision_validacion:.1%}"
        if prediccion.precision_validacion is not None
        else "No disponible"
    )
    columnas_prediccion[2].metric("Precisión temporal", precision)
    st.caption(
        f"Random Forest entrenado con {prediccion.muestras_entrenamiento} sesiones. "
        "La señal es experimental y no constituye asesoría financiera."
    )
    with st.expander("Importancia de las variables"):
        st.bar_chart(
            pd.Series(prediccion.importancias, name="Importancia").sort_values()
        )

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
    pd.DataFrame(
        {
            "Métrica": list(resumen_visible),
            "Valor": [str(valor) for valor in resumen_visible.values()],
        }
    ),
    width="stretch",
    hide_index=True,
)
st.caption(
    "Los datos se actualizan desde Yahoo Finance y se almacenan en caché durante "
    "15 minutos."
)

# File: stock_analysis_app.py

def descargar_datos_accion(ticker="AAPL", period="1y"):
    """Descarga datos históricos de cotizaciones desde Yahoo Finanzas."""
    data = yf.download(ticker, period=period, progress=False)
    if data.empty:
        raise ValueError(f"No se encontraron datos para el ticker {ticker}")
    return data

def preparar_features(df):
    """Calcula indicadores técnicos y variable objetivo."""
    df = df.copy()
    # Retorno diario
    df['Returns'] = df['Close'].pct_change()
    # Promedios Móviles Simples
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    # Volatilidad a 10 días
    df['Volatility_10'] = df['Returns'].rolling(window=10).std()
    
    # Variable objetivo: 1 si el precio de mañana es mayor al de hoy, 0 en caso contrario
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    
    df.dropna(inplace=True)
    return df

def entrenar_modelo_prediccion(df):
    """Entrena un modelo Random Forest para predecir la tendencia del precio."""
    feature_cols = ['Returns', 'SMA_5', 'SMA_20', 'Volatility_10']
    X = df[feature_cols]
    y = df['Target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    return model, acc

