# File: stock_analysis_app.py
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

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

if __name__ == "__main__":
    ticker_simbolo = "AAPL"
    print(f"[+] Extrayendo datos de {ticker_simbolo}...")
    df_raw = descargar_datos_accion(ticker_simbolo)
    df_proc = preparar_features(df_raw)
    modelo, exactitud = entrenar_modelo_prediccion(df_proc)
    print(f"[✓] Modelo entrenado con éxito. Exactitud en test: {exactitud:.2%}")
