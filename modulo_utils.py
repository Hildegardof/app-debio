"""
modulo_utils.py
----------------
Funções analíticas e utilitárias compartilhadas entre os módulos do App DeBio.

Centraliza:
- Parsing numérico robusto (padrão brasileiro, vírgula decimal)
- Regressão linear com R² padronizado e alerta de linearidade (ICH Q2(R1))
- Ajuste de curvas dose-resposta (IC50/EC50) por log-concentração e logístico
  de 4 parâmetros (4PL / equação de Hill)
- Estatística de réplicas (média, desvio-padrão, RSD%)
- Exportação de DataFrames para Excel em memória
- Registro de resultados no "carrinho de laudos" (consumido pelo modulo_relatorios)

Este módulo não renderiza nenhuma tela sozinho — ele só fornece funções que os
demais módulos (modulo_oleos, modulo_antioxidantes, modulo_ferramentas,
modulo_relatorios) importam e reutilizam, evitando duplicação de lógica
analítica entre arquivos.

Os cálculos são mantidos em precisão total (float64); o arredondamento para
exibição é responsabilidade de cada módulo de interface.
"""

import io
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# 1. PARSING NUMÉRICO (padrão brasileiro: vírgula decimal)
# ============================================================

def parse_numero_br(valor):
    """
    Converte um valor, lista ou pandas Series no padrão numérico brasileiro
    (vírgula decimal) para float. Também aceita o padrão internacional (ponto).

    - Se `valor` for uma Series/lista/array: retorna uma pandas Series de floats,
      com entradas inválidas viradas em NaN (não lança exceção).
    - Se `valor` for escalar: retorna um float, ou NaN se não for conversível.
    """
    if isinstance(valor, (pd.Series, list, tuple, np.ndarray)):
        serie = pd.Series(valor)
        return pd.to_numeric(
            serie.astype(str).str.strip().str.replace(',', '.', regex=False),
            errors='coerce'
        )
    if valor is None:
        return np.nan
    try:
        return float(str(valor).strip().replace(',', '.'))
    except (ValueError, TypeError):
        return np.nan


# ============================================================
# 2. REGRESSÃO LINEAR + CRITÉRIO DE LINEARIDADE (ICH Q2(R1))
# ============================================================

@dataclass
class ResultadoRegressao:
    """Resultado de uma regressão linear simples y = a*x + b."""
    a: float
    b: float
    r2: float
    n: int
    x: np.ndarray = field(repr=False)
    y: np.ndarray = field(repr=False)
    y_pred: np.ndarray = field(repr=False)

    def prever_x(self, y_valor):
        """Interpola x a partir de y (inverte y = a*x + b). Aceita escalar ou Series/array."""
        if self.a == 0:
            if np.isscalar(y_valor):
                return np.nan
            return pd.Series(np.nan, index=getattr(y_valor, 'index', None))
        return (y_valor - self.b) / self.a

    def prever_y(self, x_valor):
        return self.a * np.asarray(x_valor, dtype=float) + self.b


def regressao_linear(x, y) -> Optional[ResultadoRegressao]:
    """
    Regressão linear simples (mínimos quadrados, grau 1).

    R² é calculado pela definição padrão R² = 1 - SQres/SQtot, que para
    regressão linear simples é numericamente equivalente ao quadrado do
    coeficiente de correlação de Pearson — usar essa forma padroniza o
    cálculo entre os módulos do app (antes havia duas fórmulas diferentes
    para o mesmo R², uma em cada módulo).

    Retorna None se houver menos de 2 pontos válidos ou se todos os x forem iguais.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    if len(x) < 2 or np.all(x == x[0]):
        return None

    coefs = np.polyfit(x, y, 1)
    a, b = float(coefs[0]), float(coefs[1])
    y_pred = a * x + b
    sq_res = float(np.sum((y - y_pred) ** 2))
    sq_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - (sq_res / sq_tot) if sq_tot > 0 else 1.0

    return ResultadoRegressao(a=a, b=b, r2=r2, n=len(x), x=x, y=y, y_pred=y_pred)


def exibir_alerta_r2(r2: float, limite: float = 0.99):
    """
    Exibe um alerta padronizado de linearidade para curvas analíticas.

    O critério R² ≥ 0,99 não é um número único mandatado pelo ICH Q2(R1) em si
    (que pede o relato do coeficiente de correlação, intercepto, inclinação e
    soma residual dos quadrados, sem fixar um valor de corte universal), mas é
    o critério de aceitação prático mais difundido na validação de métodos
    analíticos e adotado por diversas farmacopeias e laboratórios — por isso
    usado aqui como referência de alerta, ajustável via `limite`.
    """
    if r2 >= limite:
        st.success(f"✅ R² = {r2:.4f} — dentro do critério usual de linearidade (R² ≥ {limite:.2f}, ref. ICH Q2(R1)).")
    elif r2 >= limite - 0.04:
        st.warning(f"⚠️ R² = {r2:.4f} — abaixo do critério usual de linearidade (R² ≥ {limite:.2f}). Considere revisar pontos com resíduo alto ou repetir a curva.")
    else:
        st.error(f"🚫 R² = {r2:.4f} — linearidade comprometida (bem abaixo de {limite:.2f}). Resultados quantitativos desta curva não são confiáveis.")


# ============================================================
# 3. ESTATÍSTICA DE RÉPLICAS (DP / RSD%)
# ============================================================

def estatisticas_replicatas(df: pd.DataFrame, colunas: List[str]) -> pd.DataFrame:
    """
    Calcula, linha a linha, a média, o desvio-padrão amostral (ddof=1) e o
    RSD% (coeficiente de variação) ao longo das colunas de réplicas informadas.

    Retorna um DataFrame (mesmo índice de `df`) com as colunas: Media, DP, RSD_%.
    Usado principalmente para réplicas de injeção em CG (TR e Área).
    """
    valores = df[colunas].apply(pd.to_numeric, errors='coerce')
    media = valores.mean(axis=1)
    dp = valores.std(axis=1, ddof=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        rsd = np.where(media != 0, (dp / media.abs()) * 100, np.nan)
    return pd.DataFrame({'Media': media, 'DP': dp, 'RSD_%': rsd}, index=df.index)


# ============================================================
# 4. DOSE-RESPOSTA / IC50 (log-concentração + logístico de 4 parâmetros)
# ============================================================

@dataclass
class ResultadoIC50:
    """Resultado da estimativa de IC50/EC50 a partir de uma curva dose-resposta."""
    metodo: str  # "4PL" ou "log-linear (fallback)"
    ic50: float
    r2: float
    dentro_da_faixa: bool
    parametros: Dict[str, float]
    x: np.ndarray = field(repr=False)
    y: np.ndarray = field(repr=False)

    def curva(self, x_plot):
        """Retorna y previsto para um array de concentrações, seguindo o método usado no ajuste."""
        x_plot = np.asarray(x_plot, dtype=float)
        log_x = np.log10(np.clip(x_plot, 1e-12, None))
        if self.metodo == "4PL":
            bottom, top, logic50, hill = (self.parametros[k] for k in ("bottom", "top", "logic50", "hill"))
            return _modelo_4pl(log_x, bottom, top, logic50, hill)
        a, b = self.parametros['a'], self.parametros['b']
        return a * log_x + b


def _modelo_4pl(log_x, bottom, top, logic50, hill):
    """Logístico de 4 parâmetros sobre log10(concentração) — equação de Hill / GraphPad 'variable slope'."""
    return bottom + (top - bottom) / (1 + 10 ** ((logic50 - log_x) * hill))


def calcular_ic50(concentracao, resposta) -> Optional[ResultadoIC50]:
    """
    Estima o IC50 (ou EC50) de uma curva dose-resposta.

    Metodologia (nesta ordem de preferência):

    1. Ajuste logístico de 4 parâmetros (4PL / equação de Hill) sobre
       log10(concentração) × resposta — abordagem de referência para curvas
       dose-resposta sigmoidais (Sebaugh, 2011, *Pharmaceutical Statistics*
       10:128-134; equivalente ao modelo "log(inhibitor) vs. response —
       Variable slope" do GraphPad Prism).
    2. Se o ajuste não convergir (comum com poucos pontos, <4, dados quase
       lineares ou resposta não-sigmoidal), cai para regressão linear simples
       sobre log10(concentração) × resposta.

    Em ambos os casos o ajuste é feito sobre a concentração em escala
    logarítmica, e não sobre a concentração em escala linear (limitação do
    código original, que subestima/superestima o IC50 fora da região central
    da curva, já que a relação concentração × resposta em ensaios de
    inibição é sigmoidal, não linear).

    Retorna None se não houver pelo menos 2 concentrações positivas distintas.
    """
    x = np.asarray(concentracao, dtype=float)
    y = np.asarray(resposta, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y)) & (x > 0)
    x, y = x[mask], y[mask]
    if len(x) < 2 or len(np.unique(x)) < 2:
        return None

    log_x = np.log10(x)

    metodo = None
    ic50 = np.nan
    r2 = np.nan
    parametros: Dict[str, float] = {}

    if len(x) >= 4:
        try:
            from scipy.optimize import curve_fit
            p0 = [float(np.min(y)), float(np.max(y)), float(np.median(log_x)), 1.0]
            bounds = (
                [-np.inf, -np.inf, log_x.min() - 2, -10],
                [np.inf, np.inf, log_x.max() + 2, 10],
            )
            popt, _ = curve_fit(_modelo_4pl, log_x, y, p0=p0, bounds=bounds, maxfev=10000)
            bottom, top, logic50, hill = popt
            y_pred = _modelo_4pl(log_x, *popt)
            sq_res = float(np.sum((y - y_pred) ** 2))
            sq_tot = float(np.sum((y - np.mean(y)) ** 2))
            r2_fit = 1.0 - sq_res / sq_tot if sq_tot > 0 else 1.0
            if np.isfinite(logic50) and r2_fit > 0.5:
                metodo = "4PL"
                ic50 = float(10 ** logic50)
                r2 = float(r2_fit)
                parametros = {"bottom": float(bottom), "top": float(top), "logic50": float(logic50), "hill": float(hill)}
        except Exception:
            metodo = None

    if metodo is None:
        reg = regressao_linear(log_x, y)
        if reg is None:
            return None
        metodo = "log-linear (fallback)"
        r2 = reg.r2
        parametros = {"a": reg.a, "b": reg.b}
        if reg.a != 0:
            ic50 = float(10 ** ((50.0 - reg.b) / reg.a))
        else:
            ic50 = np.nan

    dentro_da_faixa = bool(np.isfinite(ic50) and x.min() <= ic50 <= x.max())

    return ResultadoIC50(
        metodo=metodo, ic50=ic50, r2=r2, dentro_da_faixa=dentro_da_faixa,
        parametros=parametros, x=x, y=y,
    )


# ============================================================
# 5. EXPORTAÇÃO
# ============================================================

def exportar_excel_bytes(df: pd.DataFrame, sheet_name: str = "Dados") -> bytes:
    """Serializa um DataFrame para bytes .xlsx prontos para uso em st.download_button."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return buffer.getvalue()


# ============================================================
# 6. CARRINHO DE LAUDOS (compartilhado com modulo_relatorios)
# ============================================================

def registrar_resultado(tipo: str, nome: str, dados: Dict[str, Any]):
    """
    Registra um resultado calculado em qualquer módulo no carrinho de laudos
    compartilhado (st.session_state['laudo_dados']), consumido pelo
    modulo_relatorios.py para montar o laudo técnico consolidado (.docx).

    tipo: categoria do resultado (ex.: "Antioxidante — DPPH (IC50)")
    nome: identificação legível (ex.: nome da amostra)
    dados: dicionário {rótulo: valor} a exibir na tabela do laudo
    """
    if 'laudo_dados' not in st.session_state:
        st.session_state['laudo_dados'] = []
    st.session_state['laudo_dados'].append({"tipo": tipo, "nome": nome, "dados": dados})


def listar_resultados_laudo() -> List[dict]:
    return st.session_state.get('laudo_dados', [])
