"""Entrenamiento y predicción de la tendencia bursátil."""

from dataclasses import dataclass

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

from .metricas import calcular_indicadores


CARACTERISTICAS = (
    "Retorno Diario",
    "SMA5",
    "SMA20",
    "Volatilidad 10",
    "Ratio Volumen 20",
)
MINIMO_MUESTRAS = 30


@dataclass(frozen=True)
class ResultadoPrediccion:
    """Resultado interpretable de la predicción de la siguiente sesión."""

    clase: int
    etiqueta: str
    probabilidad: float
    muestras_entrenamiento: int
    precision_validacion: float | None
    importancias: dict[str, float]


def preparar_datos_modelo(
    historial: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Crea variables, objetivo futuro y observación de la última sesión."""
    if historial.empty:
        raise ValueError("El historial no contiene datos para entrenar.")
    if "Volume" not in historial.columns:
        raise ValueError("El historial debe incluir la columna 'Volume'.")

    datos = calcular_indicadores(historial)
    objetivo = (datos["Close"].shift(-1) > datos["Close"]).astype(int)
    conjunto = datos.loc[:, list(CARACTERISTICAS)].copy()
    conjunto.replace([float("inf"), float("-inf")], float("nan"), inplace=True)

    disponibles = conjunto.notna().all(axis=1) & objetivo.notna()
    variables = conjunto.loc[disponibles & (datos["Close"].shift(-1).notna())]
    etiquetas = objetivo.loc[variables.index]
    ultima_observacion = conjunto.iloc[[-1]].copy()

    if len(variables) < MINIMO_MUESTRAS:
        raise ValueError(
            "Se requieren al menos "
            f"{MINIMO_MUESTRAS} sesiones completas para entrenar el modelo; "
            f"hay {len(variables)}."
        )
    if ultima_observacion.isna().any(axis=None):
        raise ValueError("La sesión más reciente no permite calcular todos los indicadores.")

    return variables, etiquetas, ultima_observacion.iloc[0]


def _crear_modelo(
    random_state: int = 42,
    estimadores: int = 200,
) -> RandomForestClassifier:
    """Construye el clasificador con parámetros reproducibles."""
    if estimadores < 1:
        raise ValueError("El número de árboles debe ser mayor que cero.")

    return RandomForestClassifier(
        n_estimators=estimadores,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=-1,
    )


def _evaluar_temporal(
    variables: pd.DataFrame,
    objetivo: pd.Series,
    random_state: int,
    estimadores: int,
) -> float | None:
    """Evalúa el modelo únicamente sobre el tramo temporal más reciente."""
    punto_corte = int(len(variables) * 0.8)
    entrenamiento = variables.iloc[:punto_corte]
    validacion = variables.iloc[punto_corte:]

    if len(validacion) < 5 or entrenamiento[CARACTERISTICAS[0]].empty:
        return None
    if objetivo.iloc[:punto_corte].nunique() < 2:
        return None

    modelo = _crear_modelo(random_state, estimadores)
    modelo.fit(entrenamiento, objetivo.iloc[:punto_corte])
    predicciones = modelo.predict(validacion)
    return float(accuracy_score(objetivo.iloc[punto_corte:], predicciones))


def predecir_tendencia(
    historial: pd.DataFrame,
    *,
    random_state: int = 42,
    estimadores: int = 200,
) -> ResultadoPrediccion:
    """Entrena con datos pasados y predice el movimiento del próximo cierre."""
    variables, objetivo, ultima_observacion = preparar_datos_modelo(historial)
    precision = _evaluar_temporal(
        variables, objetivo, random_state, estimadores
    )

    modelo = _crear_modelo(random_state, estimadores)
    modelo.fit(variables, objetivo)
    probabilidades = modelo.predict_proba(ultima_observacion.to_frame().T)[0]
    clase = int(modelo.classes_[int(probabilidades.argmax())])
    probabilidad = float(probabilidades.max())
    importancias = dict(
        zip(
            variables.columns,
            (float(valor) for valor in modelo.feature_importances_),
            strict=True,
        )
    )

    return ResultadoPrediccion(
        clase=clase,
        etiqueta="Alcista" if clase == 1 else "Bajista o lateral",
        probabilidad=probabilidad,
        muestras_entrenamiento=len(variables),
        precision_validacion=precision,
        importancias=importancias,
    )
