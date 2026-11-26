# File: test_app.py
import pytest
import pandas as pd
from stock_analysis_app import descargar_datos_accion, preparar_features

def test_descargar_datos_valido():
    """Verifica que yfinance retorne un DataFrame no vacío para un ticker válido."""
    df = descargar_datos_accion("MSFT", period="1m")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "Close" in df.columns

def test_preparar_features_columnas():
    """Verifica que se generen correctamente las columnas de indicadores y target."""
    df_raw = descargar_datos_accion("AAPL", period="3m")
    df_proc = preparar_features(df_raw)
    assert "SMA_5" in df_proc.columns
    assert "SMA_20" in df_proc.columns
    assert "Target" in df_proc.columns
    assert df_proc['Target'].isin([0, 1]).all()
