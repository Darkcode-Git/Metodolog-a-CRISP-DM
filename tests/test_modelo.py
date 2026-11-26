import numpy as np
import pandas as pd
import pytest

from analisis_acciones import CARACTERISTICAS, predecir_tendencia
from analisis_acciones.modelo import preparar_datos_modelo


def historial_variable(cantidad=180):
    indice = pd.date_range("2024-01-01", periods=cantidad)
    posiciones = np.arange(cantidad)
    precios = 100 + posiciones * 0.03 + np.sin(posiciones / 3) * 4
    volumen = 1_000 + (posiciones % 17) * 35

    return pd.DataFrame(
        {
            "Close": precios,
            "High": precios + 1.5,
            "Low": precios - 1.5,
            "Volume": volumen,
        },
        index=indice,
    )


def test_preparar_datos_crea_objetivo_sin_usar_cierre_futuro():
    historial = historial_variable(80)

    variables, objetivo, ultima_observacion = preparar_datos_modelo(historial)

    assert list(variables.columns) == list(CARACTERISTICAS)
    assert len(variables) == len(objetivo)
    assert len(variables) == 60
    assert not variables.isna().any(axis=None)
    assert ultima_observacion.index.tolist() == list(CARACTERISTICAS)
    assert objetivo.iloc[-1] == int(
        historial["Close"].iloc[-1] > historial["Close"].iloc[-2]
    )


def test_predecir_tendencia_entrega_probabilidad_e_importancias():
    resultado = predecir_tendencia(historial_variable(), estimadores=40)

    assert resultado.clase in (0, 1)
    assert resultado.etiqueta in ("Alcista", "Bajista o lateral")
    assert 0.5 <= resultado.probabilidad <= 1.0
    assert resultado.muestras_entrenamiento == 160
    assert resultado.precision_validacion is not None
    assert list(resultado.importancias) == list(CARACTERISTICAS)
    assert sum(resultado.importancias.values()) == pytest.approx(1.0)


def test_preparar_datos_exige_volumen_e_historial_suficiente():
    historial = historial_variable()
    with pytest.raises(ValueError, match="Volume"):
        preparar_datos_modelo(historial.drop(columns="Volume"))

    with pytest.raises(ValueError, match="al menos 30"):
        preparar_datos_modelo(historial.iloc[:40])
