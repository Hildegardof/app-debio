import streamlit as st
import pandas as pd
import io
import numpy as np

# -----------------------------------------
# MENU LATERAL
# -----------------------------------------
st.sidebar.title("🧪 App DeBio")
st.sidebar.write("Navegação:")
ferramenta_escolhida = st.sidebar.radio(
    "Escolha o cálculo:",
    ["🌿 Rendimento de Extração", "📊 Índice Aritmético e Áreas", "🔄 Conversão de Unidades"]
)
st.sidebar.divider()
st.sidebar.info("Desenvolvido para agilizar a bancada do DeBio - IFES.")

# =========================================
# TELA 1: RENDIMENTO DE EXTRAÇÃO
# =========================================
if ferramenta_escolhida == "🌿 Rendimento de Extração":
    st.title("🌿 Rendimento de Óleo Essencial")
    nome_amostra = st.text_input("Nome da Amostra (Ex: Schinus terebinthifolia):")
    massa_planta = st.number_input("Massa do material vegetal seco (g):", min_value=0.0, format="%.2f")
    massa_oleo = st.number_input("Massa do óleo obtido (g):", min_value=0.0, format="%.4f")
    if st.button("Calcular Rendimento"):
        if massa_planta > 0:
            rendimento = (massa_oleo / massa_planta) * 100
            st.success(f"✅ O rendimento da amostra '{nome_amostra}' é de {rendimento:.2f}% (m/m)")
        else:
            st.error("⚠️ A massa da planta deve ser maior que zero.")

# =========================================
# TELA 2: ÍNDICE ARITMÉTICO E ÁREAS
# =========================================
elif ferramenta_escolhida == "📊 Índice Aritmético e Áreas":
    st.title("📊 Índice Aritmético (Kovats) e Áreas")
    st.write("Processamento automático de triplicatas via Template DeBio.")

    st.subheader("📥 0. Baixe os Templates Padrão")
    st.write("Se for o seu primeiro acesso, baixe os arquivos abaixo e preencha com seus dados brutos.")
    
    col_temp1, col_temp2 = st.columns(2)
    
    df_temp_amostra = pd.DataFrame({
        'Pico': [1, 2], 'TR_1': [12.45, 15.10], 'TR_2': [12.46, 15.12], 'TR_3': [12.44, 15.11], 
        'Area_1': [150000, 340000], 'Area_2': [152000, 345000], 'Area_3': [148000, 338000]
    })
    buffer_amostra = io.BytesIO()
    with pd.ExcelWriter(buffer_amostra, engine='openpyxl') as writer:
        df_temp_amostra.to_excel(writer, index=False, sheet_name='Amostra')
    
    with col_temp1:
        st.download_button("📄 Baixar Template da Amostra", data=buffer_amostra.getvalue(), file_name="Template_Amostra_DeBio.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    df_temp_alcanos = pd.DataFrame({
        'TR_Alcano': [5.20, 8.45], 'Carbonos': [8, 9]
    })
    buffer_alcanos = io.BytesIO()
    with pd.ExcelWriter(buffer_alcanos, engine='openpyxl') as writer:
        df_temp_alcanos.to_excel(writer, index=False, sheet_name='Alcanos')
    
    with col_temp2:
        st.download_button("📄 Baixar Template de Alcanos", data=buffer_alcanos.getvalue(), file_name="Template_Alcanos_DeBio.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.divider()

    col_entrada1, col_entrada2 = st.columns(2)
    with col_entrada1:
        st.subheader("1. Amostra (Triplicata)")
        metodo_amostra = st.radio("Inserir Amostra:", ["📂 Upload", "📋 Colar"], horizontal=True, key="amo_radio")
        tabela_amostra = None
        if metodo_amostra == "📋 Colar":
            dados_amostra = st.text_area("Cole os dados da amostra:", height=100)
            if dados_amostra:
                try: tabela_amostra = pd.read_csv(io.StringIO(dados_amostra), sep="\t")
                except: pass
        else:
            arq_amostra = st.file_uploader("Suba o arquivo (.xlsx)", type=["xlsx"], key="up_amo")
            if arq_amostra: tabela_amostra = pd.read_excel(arq_amostra)

    with col_entrada2:
        st.subheader("2. Série Homóloga")
        metodo_alcanos = st.radio("Inserir Alcanos:", ["📂 Upload", "📋 Colar"], horizontal=True, key="alc_radio")
        tabela_alcanos = None
        if metodo_alcanos == "📋 Colar":
            dados_alcanos = st.text_area("Cole os alcanos:", height=100)
            if dados_alcanos:
                try: tabela_alcanos = pd.read_csv(io.StringIO(dados_alcanos), sep="\t")
                except: pass
        else:
            arq_alcanos = st.file_uploader("Suba o arquivo (.xlsx)", type=["xlsx"], key="up_alc")
            if arq_alcanos: tabela_alcanos = pd.read_excel(arq_alcanos)

    if tabela_amostra is not None and tabela_alcanos is not None:
        st.divider()
        if st.button("🚀 Processar o calculo de IRL", use_container_width=True):
            try:
                amostra = tabela_amostra.copy()
                alcanos = tabela_alcanos.copy()

                amostra['TR_Medio'] = amostra[['TR_1', 'TR_2', 'TR_3']].mean(axis=1)
                amostra['Area_Media'] = amostra[['Area_1', 'Area_2', 'Area_3']].mean(axis=1)
                
                soma_areas = amostra['Area_Media'].sum()
                amostra['Area_Relativa_%'] = (amostra['Area_Media'] / soma_areas) * 100

                alcanos['TR_Alcano'] = pd.to_numeric(alcanos['TR_Alcano'], errors='coerce')
                alcanos['Carbonos'] = pd.to_numeric(alcanos['Carbonos'], errors='coerce')
                alcanos = alcanos.dropna().sort_values(by='TR_Alcano').reset_index(drop=True)

                lista_irl = []
                for _, linha in amostra.iterrows():
                    tr_x = linha['TR_Medio']
                    if pd.isna(tr_x):
                        lista_irl.append(None)
                        continue

                    antes = alcanos[alcanos['TR_Alcano'] <= tr_x]
                    depois = alcanos[alcanos['TR_Alcano'] > tr_x]

                    if antes.empty or depois.empty:
                        lista_irl.append(None)
                    else:
                        tr_n = antes.iloc[-1]['TR_Alcano']
                        n = antes.iloc[-1]['Carbonos']
                        tr_n1 = depois.iloc[0]['TR_Alcano']
                        
                        irl = 100 * (n + ((tr_x - tr_n) / (tr_n1 - tr_n)))
                        lista_irl.append(round(irl))

                amostra['IRL_Calculado'] = lista_irl
                amostra['TR_Medio'] = amostra['TR_Medio'].round(3)
                amostra['Area_Media'] = amostra['Area_Media'].round(2)
                amostra['Area_Relativa_%'] = amostra['Area_Relativa_%'].round(2)

                colunas_finais = ['Pico', 'TR_Medio', 'Area_Media', 'Area_Relativa_%', 'IRL_Calculado', 'TR_1', 'TR_2', 'TR_3', 'Area_1', 'Area_2', 'Area_3']
                amostra = amostra[[c for c in colunas_finais if c in amostra.columns]]
                
                st.session_state['resultado_calculo'] = amostra
                
                df_ident = amostra[['Pico', 'TR_Medio', 'IRL_Calculado']].copy()
                df_ident['IRL_Literatura'] = None
                df_ident['Identificacao'] = ""
                df_ident['Classe'] = ""
                st.session_state['tabela_identificacao'] = df_ident

            except Exception as e:
                st.error(f"Erro no processamento: {e}")

        if 'resultado_calculo' in st.session_state:
            st.success("✅ Triplicatas processadas, Área Relativa e IRL calculados com sucesso!")
            st.dataframe(st.session_state['resultado_calculo'], use_container_width=True)
            
            buffer_bruto = io.BytesIO()
            with pd.ExcelWriter(buffer_bruto, engine='openpyxl') as writer:
                st.session_state['resultado_calculo'].to_excel(writer, index=False, sheet_name='Resultados_IRL')
            
            st.download_button(
                label="🟢 Baixar Tabela de Resultados", 
                data=buffer_bruto.getvalue(), 
                file_name="Resultados_Brutos_IRL.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

            st.divider()

            st.subheader("🔍 Identificação dos Compostos")
            st.write("Dê um duplo-clique nas células das colunas vazias abaixo para digitar as informações.")
            
            tabela_editada = st.data_editor(
                st.session_state['tabela_identificacao'], 
                use_container_width=True,
                disabled=["Pico", "TR_Medio", "IRL_Calculado"], 
                hide_index=True
            )

            buffer_ident = io.BytesIO()
            with pd.ExcelWriter(buffer_ident, engine='openpyxl') as writer:
                tabela_editada.to_excel(writer, index=False, sheet_name='Identificacao')
            
            st.download_button(
                label="🟢 Baixar Tabela de Identificação Preenchida", 
                data=buffer_ident.getvalue(), 
                file_name="Identificacao_Compostos.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

# =========================================
# TELA 3: CONVERSÃO DE UNIDADES (ATUALIZADO)
# =========================================
elif ferramenta_escolhida == "🔄 Conversão de Unidades":
    st.title("🔄 Conversão de Unidades e Diluição")
    st.write("Calculadora rápida para preparo de padrões e leitura de artigos.")
    
    tipo_conversao = st.selectbox(
        "Selecione o tipo de cálculo que deseja fazer:",
        [
            "1. mg/mL ➔ ppm (ou µg/mL)",
            "2. ppm (ou µg/mL) ➔ mg/mL",
            "3. % (m/v) ➔ mg/mL",
            "4. mg/mL ➔ % (m/v)",
            "5. % (v/v) ➔ µL/mL",
            "6. Molaridade (mol/L) ➔ Concentração Comum (g/L)",
            "7. Concentração Comum (g/L) ➔ Molaridade (mol/L)",
            "8. Preparo de Diluições (C1V1 = C2V2)"
        ]
    )
    
    st.divider()
    
    # 1. mg/mL para ppm
    if tipo_conversao == "1. mg/mL ➔ ppm (ou µg/mL)":
        valor = st.number_input("Digite a concentração em mg/mL:", min_value=0.0, format="%.4f")
        if valor > 0:
            st.success(f"🧪 **Resultado:** {valor} mg/mL = **{valor * 1000:.2f} ppm** (ou µg/mL)")
            
    # 2. ppm para mg/mL
    elif tipo_conversao == "2. ppm (ou µg/mL) ➔ mg/mL":
        valor = st.number_input("Digite a concentração em ppm (ou µg/mL):", min_value=0.0, format="%.4f")
        if valor > 0:
            st.success(f"🧪 **Resultado:** {valor} ppm = **{valor / 1000:.4f} mg/mL**")
            
    # 3. % (m/v) para mg/mL
    elif tipo_conversao == "3. % (m/v) ➔ mg/mL":
        valor = st.number_input("Digite a porcentagem % (m/v):", min_value=0.0, format="%.4f")
        if valor > 0:
            st.success(f"🧪 **Resultado:** {valor}% = **{valor * 10:.2f} mg/mL**")
            
    # 4. mg/mL para % (m/v)
    elif tipo_conversao == "4. mg/mL ➔ % (m/v)":
        valor = st.number_input("Digite a concentração em mg/mL:", min_value=0.0, format="%.4f")
        if valor > 0:
            st.success(f"🧪 **Resultado:** {valor} mg/mL = **{valor / 10:.4f}% (m/v)**")

    # 5. % (v/v) para µL/mL (Ideal para OEs)
    elif tipo_conversao == "5. % (v/v) ➔ µL/mL":
        valor = st.number_input("Digite a porcentagem em volume % (v/v):", min_value=0.0, format="%.4f")
        if valor > 0:
            st.success(f"🧪 **Resultado:** {valor}% (v/v) = **{valor * 10:.2f} µL/mL**")
            st.info("💡 Exemplo: 1% de óleo essencial significa pipetar 10 µL de óleo para cada 1 mL de solvente final.")

    # 6. Molaridade para Concentração
    elif tipo_conversao == "6. Molaridade (mol/L) ➔ Concentração Comum (g/L)":
        molaridade = st.number_input("Molaridade (mol/L):", min_value=0.0, format="%.4f")
        massa_molar = st.number_input("Massa Molar do composto (g/mol):", min_value=0.0, format="%.2f")
        if molaridade > 0 and massa_molar > 0:
            conc_gl = molaridade * massa_molar
            st.success(f"🧪 **Resultado:** A concentração é **{conc_gl:.4f} g/L** (ou {conc_gl:.4f} mg/mL)")

    # 7. Concentração para Molaridade
    elif tipo_conversao == "7. Concentração Comum (g/L) ➔ Molaridade (mol/L)":
        conc_gl = st.number_input("Concentração Comum (g/L ou mg/mL):", min_value=0.0, format="%.4f")
        massa_molar = st.number_input("Massa Molar do composto (g/mol):", min_value=0.0, format="%.2f")
        if conc_gl > 0 and massa_molar > 0:
            molaridade = conc_gl / massa_molar
            st.success(f"🧪 **Resultado:** A molaridade é **{molaridade:.6f} mol/L** (M)")

    # 8. Diluição (C1V1 = C2V2)
    elif tipo_conversao == "8. Preparo de Diluições (C1V1 = C2V2)":
        st.write("A famosa regra: $C_1 \cdot V_1 = C_2 \cdot V_2$")
        st.info("Mantenha as unidades de concentração e volume iguais nos dois lados (ex: se usar mL de um lado, o resultado será em mL).")
        
        descobrir = st.radio("O que você deseja calcular?", ["Volume Inicial (V1) - Quanto pipetar?", "Concentração Final (C2) - Após diluir"])
        
        if descobrir == "Volume Inicial (V1) - Quanto pipetar?":
            c1 = st.number_input("Concentração da solução ESTOQUE (C1):", min_value=0.0, format="%.4f")
            c2 = st.number_input("Concentração DESEJADA (C2):", min_value=0.0, format="%.4f")
            v2 = st.number_input("Volume final DESEJADO (V2):", min_value=0.0, format="%.4f")
            
            if c1 > 0 and c2 > 0 and v2 > 0:
                v1 = (c2 * v2) / c1
                st.success(f"🧪 **Você precisa pipetar:** **{v1:.4f}** da solução estoque e completar o volume até {v2}.")
                
        elif descobrir == "Concentração Final (C2) - Após diluir":
            c1 = st.number_input("Concentração da solução ESTOQUE (C1):", min_value=0.0, format="%.4f")
            v1 = st.number_input("Volume pipetado do estoque (V1):", min_value=0.0, format="%.4f")
            v2 = st.number_input("Volume TOTAL após adicionar solvente (V2):", min_value=0.0, format="%.4f")
            
            if c1 > 0 and v1 > 0 and v2 > 0:
                c2 = (c1 * v1) / v2
                st.success(f"🧪 **A Concentração Final (C2) será:** **{c2:.4f}**")
