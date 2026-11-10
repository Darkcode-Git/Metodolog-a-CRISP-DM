import pandas as pd
import pytest

from analisis_acciones import (
    calcular_indicadores,
    obtener_comparativa_balance,
    resumen_financiero,
)


def historial_con_precios(cantidad=60):
    precios = [100 + indice for indice in range(cantidad)]
    return pd.DataFrame(
        {
            "Close": precios,
            "High": [precio + 2 for precio in precios],
            "Low": [precio - 2 for precio in precios],
            "Volume": [1_000] * cantidad,
        },
        index=pd.date_range("2025-01-01", periods=cantidad),
    )


def test_calcular_indicadores_agrega_medias_y_no_modifica_entrada():
    historial = historial_con_precios()

    resultado = calcular_indicadores(historial)

    assert "SMA20" not in historial.columns
    assert resultado.loc[resultado.index[19], "SMA20"] == pytest.approx(109.5)
    assert resultado.loc[resultado.index[49], "SMA50"] == pytest.approx(124.5)
    assert resultado.loc[resultado.index[1], "Retorno Diario"] == pytest.approx(
        1 / 100
    )


def test_calcular_indicadores_exige_precio_de_cierre():
    with pytest.raises(ValueError, match="Close"):
        calcular_indicadores(pd.DataFrame({"Open": [1.0]}))


def test_comparativa_balance_usa_el_trimestre_de_hace_un_ano():
    fechas = pd.to_datetime(
        ["2025-12-31", "2025-09-30", "2025-06-30", "2025-03-31", "2024-12-31"]
    )
    balances = pd.DataFrame(
        [[120, 115, 110, 105, 100]],
        index=["Total Assets"],
        columns=fechas,
    )

    assert obtener_comparativa_balance(balances) == "20.00%"


def test_comparativa_balance_indica_datos_no_disponibles():
    assert obtener_comparativa_balance(None) == "N/A"
    assert obtener_comparativa_balance(pd.DataFrame()) == "N/A"
    assert obtener_comparativa_balance(
        pd.DataFrame([[1, 2]], index=["Cash"])
    ) == "Sin Activos"


def test_resumen_financiero_calcula_rendimiento_y_rechaza_historial_vacio():
    resumen = resumen_financiero(
        "Empresa de prueba",
        "TEST",
        historial_con_precios(2),
        {"sector": "Tecnología"},
    )

    assert resumen["Rendimiento %"] == 1.0
    assert resumen["Sector"] == "Tecnología"
    assert resumen["Volumen Promedio"] == 1_000
    assert resumen["Sharpe Ratio"] == 0.0
    with pytest.raises(ValueError, match="no contiene datos"):
        resumen_financiero("Empresa de prueba", "TEST", pd.DataFrame())
