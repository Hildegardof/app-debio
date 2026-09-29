import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import modulo_utils as utils

def renderizar_ferramentas():
    ferramenta_escolhida = st.sidebar.radio(
        "Selecione a ferramenta:",
        ["📈 Curva de Calibração", "🔄 Conversão de Unidades"]
    )

    # =========================================
    # 1. CURVA DE CALIBRAÇÃO GERAL
    # =========================================
    if ferramenta_escolhida == "📈 Curva de Calibração":
        st.title("📈 Curva de Calibração")
        with st.expander("⚙️ Escolha suas Unidades (Opcional)", expanded=True):
            col_u1, col_u2 = st.columns(2)
            with col_u1: unidade_conc = st.text_input("Unidade de Concentração:", value="mg/L")
            with col_u2: unidade_sinal = st.text_input("Nome do Sinal:", value="Área")

        st.divider()
        st.subheader("1. Construa a Curva do Padrão")
        df_padrao_vazio = pd.DataFrame({'Concentracao': [None]*5, 'Sinal': [None]*5})
        tabela_padrao = st.data_editor(df_padrao_vazio, column_config={"Concentracao": st.column_config.NumberColumn(f"Concentração ({unidade_conc})", format="%.4f"),"Sinal": st.column_config.NumberColumn(f"Sinal Lido ({unidade_sinal})", format="%.4f")},num_rows="dynamic", use_container_width=True, key="padrao_editor")

        padrao_limpo = tabela_padrao.dropna(how='any').copy()
        reg = None

        if not padrao_limpo.empty and len(padrao_limpo) >= 2:
            try:
                x = utils.parse_numero_br(padrao_limpo['Concentracao']).dropna().values
                y = utils.parse_numero_br(padrao_limpo['Sinal']).dropna().values
                if len(x) == len(y) and len(x) >= 2:
                    reg = utils.regressao_linear(x, y)
                    if reg is not None:
                        col1, col2 = st.columns(2)
                        with col1: st.metric(label="Equação da Reta", value=f"y = {reg.a:.4f}x + {reg.b:.4f}")
                        with col2: st.metric(label="R²", value=f"{reg.r2:.4f}")
                        utils.exibir_alerta_r2(reg.r2)

                        fig, ax = plt.subplots(figsize=(7, 4))
                        ax.scatter(x, y, color='#1f77b4')
                        ax.plot(x, reg.prever_y(x), color='#d62728', linestyle='--')
                        ax.set_xlabel(f'Concentração ({unidade_conc})')
                        ax.set_ylabel(f'{unidade_sinal}')
                        ax.grid(True, linestyle=':', alpha=0.6)
                        st.pyplot(fig)
            except Exception as e: st.error(f"Erro na curva: {e}")

        st.divider()
        st.subheader("2. Interpolação das Amostras")
        df_amostras_vazio = pd.DataFrame({'Amostra': ["Amostra 1", None], 'Sinal_Lido': [None, None], 'FD': [1, 1]})
        tabela_amostras = st.data_editor(df_amostras_vazio, column_config={"Amostra": "Nome da Amostra", "Sinal_Lido": st.column_config.NumberColumn(f"Sinal Lido ({unidade_sinal})", format="%.4f"), "FD": st.column_config.NumberColumn("Fator de Diluição (FD)", format="%.2f")}, num_rows="dynamic", use_container_width=True)

        if st.button("🚀 Calcular Concentração das Amostras", use_container_width=True):
            if reg is not None:
                try:
                    amostras_limpas = tabela_amostras.dropna(subset=['Sinal_Lido']).copy()
                    sinais = utils.parse_numero_br(amostras_limpas['Sinal_Lido'])
                    fds = utils.parse_numero_br(amostras_limpas['FD'])
                    conc_lida = reg.prever_x(sinais)
                    col_resultado = f'Concentração Real ({unidade_conc})'
                    amostras_limpas[col_resultado] = (conc_lida * fds).round(4)
                    st.dataframe(amostras_limpas, use_container_width=True, hide_index=True)

                    st.session_state['curva_calibracao_resultado'] = {
                        'unidade_conc': unidade_conc,
                        'equacao': f"y = {reg.a:.4f}x + {reg.b:.4f}",
                        'r2': reg.r2,
                        'col_resultado': col_resultado,
                        'tabela': amostras_limpas.copy(),
                    }
                except Exception as e: st.error(f"Erro na quantificação: {e}")
            else:
                st.warning("⚠️ Construa uma curva de calibração válida (pelo menos 2 pontos) antes de calcular as concentrações.")

        if st.session_state.get('curva_calibracao_resultado'):
            st.divider()
            if st.button("💾 Salvar resultados no laudo", use_container_width=True, key="salvar_curva_calib"):
                info = st.session_state['curva_calibracao_resultado']
                for _, linha in info['tabela'].iterrows():
                    utils.registrar_resultado(
                        tipo="Curva de Calibração",
                        nome=str(linha['Amostra']),
                        dados={
                            "Equação da curva": info['equacao'],
                            "R²": f"{info['r2']:.4f}",
                            "Resultado": f"{linha[info['col_resultado']]:.4f} {info['unidade_conc']}",
                        }
                    )
                st.success("✅ Resultados salvos no laudo técnico! Acesse o módulo 📄 Laudos e Relatórios.")

    # =========================================
    # 2. CONVERSÃO DE UNIDADES
    # =========================================
    elif ferramenta_escolhida == "🔄 Conversão de Unidades":
        st.title("🔄 Conversão de Unidades e Diluição")
        tipo_conversao = st.selectbox("Selecione o tipo de cálculo:", ["1. mg/mL ➔ ppm (ou µg/mL)", "2. ppm (ou µg/mL) ➔ mg/mL", "3. % (m/v) ➔ mg/mL", "4. mg/mL ➔ % (m/v)", "5. Preparo de Diluições (C1V1 = C2V2)"])
        st.divider()
        if tipo_conversao == "1. mg/mL ➔ ppm (ou µg/mL)":
            valor = st.number_input("Digite a concentração em mg/mL:", min_value=0.0, format="%.4f")
            if valor > 0: st.success(f"🧪 **Resultado:** {valor} mg/mL = **{valor * 1000:.2f} ppm**")
        elif tipo_conversao == "2. ppm (ou µg/mL) ➔ mg/mL":
            valor = st.number_input("Digite a concentração em ppm:", min_value=0.0, format="%.4f")
            if valor > 0: st.success(f"🧪 **Resultado:** {valor} ppm = **{valor / 1000:.4f} mg/mL**")
        elif tipo_conversao == "3. % (m/v) ➔ mg/mL":
            valor = st.number_input("Digite a porcentagem % (m/v):", min_value=0.0, format="%.4f")
            if valor > 0: st.success(f"🧪 **Resultado:** {valor}% = **{valor * 10:.2f} mg/mL**")
        elif tipo_conversao == "4. mg/mL ➔ % (m/v)":
            valor = st.number_input("Digite a concentração em mg/mL:", min_value=0.0, format="%.4f")
            if valor > 0: st.success(f"🧪 **Resultado:** {valor} mg/mL = **{valor / 10:.4f}% (m/v)**")
        elif tipo_conversao == "5. Preparo de Diluições (C1V1 = C2V2)":
            c1 = st.number_input("Concentração da solução ESTOQUE (C1):", min_value=0.0, format="%.4f")
            c2 = st.number_input("Concentração DESEJADA (C2):", min_value=0.0, format="%.4f")
            v2 = st.number_input("Volume final DESEJADO (V2):", min_value=0.0, format="%.4f")
            if c1 > 0 and c2 > 0 and v2 > 0:
                st.success(f"🧪 **Você precisa pipetar:** **{(c2 * v2) / c1:.4f}** da solução estoque.")
