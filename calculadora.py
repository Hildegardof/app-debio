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

    # -----------------------------------------
    # PASSO 0: GERADOR DE TEMPLATES EM EXCEL
    # -----------------------------------------
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

    # -----------------------------------------
    # PASSO 1 & 2: ENTRADA DE DADOS
    # -----------------------------------------
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

    # -----------------------------------------
    # PASSO 3: O CÉREBRO (CÁLCULOS AUTOMÁTICOS)
    # -----------------------------------------
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
                
                # Salva o resultado na memória do site para não sumir
                st.session_state['resultado_calculo'] = amostra
                
                # Prepara a tabela de identificação limpa
                df_ident = amostra[['Pico', 'TR_Medio', 'IRL_Calculado']].copy()
                df_ident['IRL_Literatura'] = None
                df_ident['Identificacao'] = ""
                df_ident['Classe'] = ""
                st.session_state['tabela_identificacao'] = df_ident

            except Exception as e:
                st.error(f"Erro no processamento: {e}")

        # Se o cálculo já foi feito e está na memória, mostra as tabelas e botões
        if 'resultado_calculo' in st.session_state:
            st.success("✅ Triplicatas processadas, Área Relativa e IRL calculados com sucesso!")
            st.dataframe(st.session_state['resultado_calculo'], use_container_width=True)
            
            # Botão Verde de Download da Tabela Bruta
            buffer_bruto = io.BytesIO()
            with pd.ExcelWriter(buffer_bruto, engine='openpyxl') as writer:
                st.session_state['resultado_calculo'].to_excel(writer, index=False, sheet_name='Resultados_IRL')
            
            st.download_button(
                label="🟢 Baixar Tabela de Resultados", 
                data=buffer_bruto.getvalue(), 
                file_name="Resultados_Brutos_IRL.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary" # Isso deixa o botão em destaque!
            )

            st.divider()

            # -----------------------------------------
            # PASSO 4: IDENTIFICAÇÃO MANUAL
            # -----------------------------------------
            st.subheader("🔍 Identificação dos Compostos")
            st.write("Dê um duplo-clique nas células das colunas vazias abaixo para digitar as informações. Quando terminar, baixe a tabela pronta.")
            
            # Tabela Editável
            tabela_editada = st.data_editor(
                st.session_state['tabela_identificacao'], 
                use_container_width=True,
                disabled=["Pico", "TR_Medio", "IRL_Calculado"], # Trava as colunas calculadas para ninguém estragar sem querer
                hide_index=True
            )

            # Botão de Download da Tabela Editada
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
# TELA 3: CONVERSÃO DE UNIDADES
# =========================================
elif ferramenta_escolhida == "🔄 Conversão de Unidades":
    st.title("🔄 Conversão")
    st.warning("🚧 Módulo em construção...")