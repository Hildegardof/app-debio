import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import modulo_utils as utils

def renderizar_antioxidantes():
    st.title("🧪 Ensaios Antioxidantes")
    st.write("Módulo dedicado ao processamento de ensaios colorimétricos e sequestro de radicais livres.")

    aba_inibicao, aba_reducao = st.tabs(["1️⃣ DPPH / ABTS (% Inibição e IC50)", "2️⃣ FRAP / Fosfomolibdênio (Equivalentes)"])

    with aba_inibicao:
        st.subheader("Radicais Livres: Cálculo de % de Inibição e $IC_{50}$")
        ensaio_escolhido = st.radio("Selecione o ensaio:", ["DPPH", "ABTS"], horizontal=True)
        st.info("💡 A fórmula utilizada será: **% Inibição = [(Abs Controle - Abs Amostra) / Abs Controle] × 100**")

        col1, col2 = st.columns(2)
        with col1: abs_controle = st.number_input(f"Absorbância do Controle ({ensaio_escolhido}):", min_value=0.000, format="%.3f", value=0.800)
        with col2: unidade_conc_inib = st.text_input("Unidade de Concentração (Ex: µg/mL):", value="µg/mL", key="unidade_inib")

        st.divider()
        st.write("📊 **Insira os dados das suas amostras (Concentração vs. Absorbância):**")
        df_inib_vazio = pd.DataFrame({'Amostra': ['Extrato Folha']*5, 'Concentracao': [10, 50, 100, 250, 500], 'Absorbancia': [0.750, 0.600, 0.400, 0.200, 0.050]})
        tabela_inib = st.data_editor(df_inib_vazio, num_rows="dynamic", use_container_width=True, key="inib_editor")

        if st.button(f"🚀 Calcular % Inibição e $IC_{{50}}$ ({ensaio_escolhido})", use_container_width=True):
            df_calc = tabela_inib.dropna(how='any').copy()
            if abs_controle > 0 and not df_calc.empty:
                try:
                    df_calc['Concentracao'] = utils.parse_numero_br(df_calc['Concentracao'])
                    df_calc['Absorbancia'] = utils.parse_numero_br(df_calc['Absorbancia'])

                    df_calc['% Inibição'] = ((abs_controle - df_calc['Absorbancia']) / abs_controle) * 100
                    df_calc['% Inibição'] = df_calc['% Inibição'].clip(lower=0).round(2)

                    st.success("✅ Cálculos realizados com sucesso!")
                    st.dataframe(df_calc, use_container_width=True, hide_index=True)

                    st.subheader("📈 Gráfico de Dispersão e $IC_{50}$")
                    st.caption(
                        "Ajuste sobre log-concentração × resposta: logístico de 4 parâmetros (4PL/Hill) quando há "
                        "≥4 pontos, ou regressão log-linear como alternativa quando o ajuste não-linear não converge. "
                        "Ref.: Sebaugh, 2011, *Pharmaceutical Statistics* 10:128-134."
                    )
                    amostras_unicas = df_calc['Amostra'].unique()
                    fig, ax = plt.subplots(figsize=(8, 5))
                    valores_ic50 = {}

                    for amostra in amostras_unicas:
                        dados_am = df_calc[df_calc['Amostra'] == amostra]
                        x = dados_am['Concentracao'].values
                        y = dados_am['% Inibição'].values

                        ax.scatter(x, y, label=f"{amostra} (Pontos)")

                        resultado = utils.calcular_ic50(x, y)
                        if resultado is None:
                            st.warning(f"⚠️ Insira pelo menos 2 concentrações distintas e positivas para a amostra '{amostra}'.")
                            continue

                        x_curva = np.linspace(x.min(), x.max(), 200)
                        ax.plot(x_curva, resultado.curva(x_curva), linestyle='--', label=f"Ajuste {amostra} ({resultado.metodo})")

                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            st.metric(label=f"$IC_{{50}}$ estimado — '{amostra}'", value=f"{resultado.ic50:.2f} {unidade_conc_inib}")
                        with col_m2:
                            st.metric(label="Qualidade do ajuste (R²)", value=f"{resultado.r2:.4f}", help=f"Método: {resultado.metodo}")

                        if not resultado.dentro_da_faixa:
                            st.warning(
                                f"⚠️ O IC50 de '{amostra}' ({resultado.ic50:.2f} {unidade_conc_inib}) está **fora da "
                                f"faixa de concentrações testadas** ({x.min():.2f}–{x.max():.2f} {unidade_conc_inib}) "
                                "— trate como extrapolação, não como resultado validado."
                            )
                        if resultado.r2 < 0.90:
                            st.warning(f"⚠️ Ajuste com R² baixo ({resultado.r2:.4f}) para '{amostra}' — considere repetir a leitura ou revisar outliers.")

                        valores_ic50[amostra] = {
                            'ic50': resultado.ic50,
                            'r2': resultado.r2,
                            'metodo': resultado.metodo,
                            'dentro_da_faixa': resultado.dentro_da_faixa,
                        }

                    ax.axhline(50, color='red', linestyle=':', label='Linha de 50% Inibição')
                    ax.set_xlabel(f'Concentração ({unidade_conc_inib})')
                    ax.set_ylabel('% de Inibição')
                    ax.set_title(f'Ensaio de {ensaio_escolhido} - Atividade Antioxidante')
                    ax.legend()
                    ax.grid(True, alpha=0.5)
                    st.pyplot(fig)

                    st.session_state['ic50_resultados'] = (
                        {'ensaio': ensaio_escolhido, 'unidade': unidade_conc_inib, 'valores': valores_ic50}
                        if valores_ic50 else None
                    )

                except Exception as e: st.error(f"Erro nos cálculos: {e}")
            else: st.error("A absorbância do controle deve ser maior que zero e a tabela preenchida.")

        if st.session_state.get('ic50_resultados'):
            st.divider()
            st.subheader("💾 Salvar no Laudo Técnico")
            if st.button("Salvar resultados de IC50 no laudo", use_container_width=True, key="salvar_ic50"):
                info = st.session_state['ic50_resultados']
                for amostra, v in info['valores'].items():
                    utils.registrar_resultado(
                        tipo=f"Antioxidante — {info['ensaio']} (IC50)",
                        nome=amostra,
                        dados={
                            "IC50": f"{v['ic50']:.2f} {info['unidade']}",
                            "Método de ajuste": v['metodo'],
                            "R²": f"{v['r2']:.4f}",
                            "Dentro da faixa testada": "Sim" if v['dentro_da_faixa'] else "Não (extrapolado)",
                        }
                    )
                st.success("✅ Resultados de IC50 salvos no laudo técnico! Acesse o módulo 📄 Laudos e Relatórios.")

    with aba_reducao:
        st.subheader("Ensaios Baseados em Curva Padrão (Equivalentes)")
        col_tipo1, col_tipo2 = st.columns(2)
        with col_tipo1:
            ensaio_red = st.selectbox("Selecione o Método:", ["FRAP", "Fosfomolibdênio", "Outro"])
        with col_tipo2:
            padrao = st.selectbox("Padrão de Referência Utilizado:", ["Trolox (TEAC)", "Ácido Ascórbico (AAE)", "Quercetina (QE)", "Rutina (RE)", "Outro"])

        unidade_final = st.text_input("Unidade de Expressão do Resultado Final:", value=f"µmol Equivalentes de {padrao.split(' ')[0]} / g")

        st.divider()
        st.write("📈 **1. Curva do Padrão Analítico**")
        df_padrao_red = pd.DataFrame({'Concentracao_Padrao': [10, 20, 40, 80, 100], 'Absorbancia_Padrao': [0.120, 0.230, 0.450, 0.880, 1.050]})
        tabela_padrao_red = st.data_editor(df_padrao_red, num_rows="dynamic", use_container_width=True, key="pad_red_editor")

        st.write("🧪 **2. Leituras das Amostras**")
        df_amo_red = pd.DataFrame({'Nome_Amostra': ['Extrato 1', 'Extrato 2'], 'Absorbancia_Lida': [0.550, 0.720], 'Fator_Diluicao': [1, 1]})
        tabela_amo_red = st.data_editor(df_amo_red, num_rows="dynamic", use_container_width=True, key="amo_red_editor")

        if st.button("🚀 Gerar Curva e Calcular Equivalentes", use_container_width=True):
            df_pad = tabela_padrao_red.dropna(how='any').copy()
            df_am = tabela_amo_red.dropna(subset=['Absorbancia_Lida']).copy()

            if len(df_pad) >= 2:
                try:
                    x_pad = utils.parse_numero_br(df_pad['Concentracao_Padrao']).values
                    y_pad = utils.parse_numero_br(df_pad['Absorbancia_Padrao']).values
                    reg = utils.regressao_linear(x_pad, y_pad)

                    if reg is None:
                        st.error("🚫 Não foi possível ajustar a curva: verifique se há pelo menos 2 concentrações distintas.")
                    else:
                        st.success(f"✅ Curva do {padrao.split(' ')[0]} gerada: **y = {reg.a:.4f}x + {reg.b:.4f}**")
                        utils.exibir_alerta_r2(reg.r2)

                        abs_lidas = utils.parse_numero_br(df_am['Absorbancia_Lida'])
                        fds = utils.parse_numero_br(df_am['Fator_Diluicao'])

                        conc_interpolada = reg.prever_x(abs_lidas)
                        resultado_final = conc_interpolada * fds

                        df_am['Concentração na Reta'] = conc_interpolada.round(4)
                        col_resultado = f'Resultado Final ({unidade_final})'
                        df_am[col_resultado] = resultado_final.round(4)

                        st.dataframe(df_am, use_container_width=True, hide_index=True)

                        fig2, ax2 = plt.subplots(figsize=(7, 4))
                        ax2.scatter(x_pad, y_pad, color='blue', label=f'Curva do {padrao}')
                        ax2.plot(x_pad, reg.prever_y(x_pad), color='gray', linestyle='--')
                        ax2.scatter(conc_interpolada, abs_lidas, color='red', marker='X', s=100, label='Amostras Lidas')

                        ax2.set_xlabel('Concentração do Padrão')
                        ax2.set_ylabel('Absorbância')
                        ax2.set_title(f'Interpolação de Equivalentes de {padrao} ({ensaio_red})')
                        ax2.legend()
                        ax2.grid(True, alpha=0.5)
                        st.pyplot(fig2)

                        st.session_state['frap_resultados'] = {
                            'ensaio': ensaio_red, 'padrao': padrao, 'unidade': unidade_final,
                            'equacao': f"y = {reg.a:.4f}x + {reg.b:.4f}", 'r2': reg.r2,
                            'col_resultado': col_resultado, 'tabela': df_am.copy(),
                        }

                except Exception as e: st.error(f"Erro nos cálculos: {e}")
            else: st.error("A curva do padrão precisa de pelo menos 2 pontos preenchidos.")

        if st.session_state.get('frap_resultados'):
            st.divider()
            st.subheader("💾 Salvar no Laudo Técnico")
            if st.button("Salvar resultados no laudo", use_container_width=True, key="salvar_frap"):
                info = st.session_state['frap_resultados']
                for _, linha in info['tabela'].iterrows():
                    utils.registrar_resultado(
                        tipo=f"Antioxidante — {info['ensaio']} ({info['padrao'].split(' ')[0]})",
                        nome=str(linha['Nome_Amostra']),
                        dados={
                            "Equação da curva": info['equacao'],
                            "R²": f"{info['r2']:.4f}",
                            "Resultado": f"{linha[info['col_resultado']]:.4f} {info['unidade']}",
                        }
                    )
                st.success("✅ Resultados salvos no laudo técnico! Acesse o módulo 📄 Laudos e Relatórios.")
