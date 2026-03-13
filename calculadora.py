import streamlit as st
import pandas as pd
import io
import numpy as np
import matplotlib.pyplot as plt # Nova ferramenta: O motor de gráficos!

# -----------------------------------------
# MENU LATERAL
# -----------------------------------------
st.sidebar.title("🧪 App DeBio")
st.sidebar.write("Navegação:")
ferramenta_escolhida = st.sidebar.radio(
    "Escolha o cálculo:",
    [
        "🌿 Rendimento de Extração", 
        "📊 Índice Aritmético e Áreas", 
        "📈 Curva de Calibração",
        "🔄 Conversão de Unidades"
    ]
)
st.sidebar.divider()
st.sidebar.info("Desenvolvido para agilizar a rotina de bancada do DeBio - IFES.")

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
    st.write("Processamento de triplicatas via Template ou Digitação Manual.")

    st.subheader("📥 0. Baixe os Templates Padrão")
    st.write("Se for o seu primeiro acesso, baixe os arquivos abaixo e preencha com seus dados brutos.")
    col_temp1, col_temp2 = st.columns(2)
    
    df_temp_amostra = pd.DataFrame({'Pico': [1, 2], 'TR_1': [12.45, 15.10], 'TR_2': [12.46, 15.12], 'TR_3': [12.44, 15.11], 'Area_1': [150000, 340000], 'Area_2': [152000, 345000], 'Area_3': [148000, 338000]})
    buffer_amostra = io.BytesIO()
    with pd.ExcelWriter(buffer_amostra, engine='openpyxl') as writer:
        df_temp_amostra.to_excel(writer, index=False, sheet_name='Amostra')
    with col_temp1:
        st.download_button("📄 Baixar Template da Amostra", data=buffer_amostra.getvalue(), file_name="Template_Amostra_DeBio.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    df_temp_alcanos = pd.DataFrame({'TR_Alcano': [5.20, 8.45], 'Carbonos': [8, 9]})
    buffer_alcanos = io.BytesIO()
    with pd.ExcelWriter(buffer_alcanos, engine='openpyxl') as writer:
        df_temp_alcanos.to_excel(writer, index=False, sheet_name='Alcanos')
    with col_temp2:
        st.download_button("📄 Baixar Template de Alcanos", data=buffer_alcanos.getvalue(), file_name="Template_Alcanos_DeBio.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.divider()

    st.subheader("1. Amostra (Triplicata)")
    metodo_amostra = st.radio("Inserir Amostra:", ["📂 Upload", "📋 Colar", "✍️ Digitar Manualmente"], horizontal=True, key="amo_radio")
    tabela_amostra = None
    if metodo_amostra == "📋 Colar":
        dados_amostra = st.text_area("Cole os dados da amostra:", height=100)
        if dados_amostra:
            try: tabela_amostra = pd.read_csv(io.StringIO(dados_amostra), sep="\t")
            except: pass
    elif metodo_amostra == "📂 Upload":
        arq_amostra = st.file_uploader("Suba o arquivo (.xlsx)", type=["xlsx"], key="up_amo")
        if arq_amostra: tabela_amostra = pd.read_excel(arq_amostra)
    elif metodo_amostra == "✍️ Digitar Manualmente":
        df_vazio_amo = pd.DataFrame(columns=['Pico', 'TR_1', 'TR_2', 'TR_3', 'Area_1', 'Area_2', 'Area_3'])
        for i in range(5): df_vazio_amo.loc[i] = [i+1, None, None, None, None, None, None]
        tabela_amostra = st.data_editor(df_vazio_amo, num_rows="dynamic", use_container_width=True, key="amo_editor")
        tabela_amostra = tabela_amostra.dropna(subset=['TR_1', 'TR_2', 'TR_3'], how='all').copy()

    st.divider()

    st.subheader("2. Série Homóloga")
    metodo_alcanos = st.radio("Inserir Alcanos:", ["📂 Upload", "📋 Colar", "✍️ Digitar Manualmente"], horizontal=True, key="alc_radio")
    tabela_alcanos = None
    if metodo_alcanos == "📋 Colar":
        dados_alcanos = st.text_area("Cole os alcanos:", height=100)
        if dados_alcanos:
            try: tabela_alcanos = pd.read_csv(io.StringIO(dados_alcanos), sep="\t")
            except: pass
    elif metodo_alcanos == "📂 Upload":
        arq_alcanos = st.file_uploader("Suba o arquivo (.xlsx)", type=["xlsx"], key="up_alc")
        if arq_alcanos: tabela_alcanos = pd.read_excel(arq_alcanos)
    elif metodo_alcanos == "✍️ Digitar Manualmente":
        df_vazio_alc = pd.DataFrame({'TR_Alcano': [None]*5, 'Carbonos': [8, 9, 10, 11, 12]})
        tabela_alcanos = st.data_editor(df_vazio_alc, num_rows="dynamic", use_container_width=True, key="alc_editor")
        tabela_alcanos = tabela_alcanos.dropna(subset=['TR_Alcano']).copy()

    if tabela_amostra is not None and not tabela_amostra.empty and tabela_alcanos is not None and not tabela_alcanos.empty:
        st.divider()
        if st.button("🚀 Processar o calculo de IRL", use_container_width=True):
            try:
                amostra = tabela_amostra.copy()
                alcanos = tabela_alcanos.copy()
                for col in ['TR_1', 'TR_2', 'TR_3', 'Area_1', 'Area_2', 'Area_3']:
                    amostra[col] = pd.to_numeric(amostra[col].astype(str).str.replace(',', '.'), errors='coerce')

                amostra['TR_Medio'] = amostra[['TR_1', 'TR_2', 'TR_3']].mean(axis=1)
                amostra['Area_Media'] = amostra[['Area_1', 'Area_2', 'Area_3']].mean(axis=1)
                soma_areas = amostra['Area_Media'].sum()
                amostra['Area_Relativa_%'] = (amostra['Area_Media'] / soma_areas) * 100
                alcanos['TR_Alcano'] = pd.to_numeric(alcanos['TR_Alcano'].astype(str).str.replace(',', '.'), errors='coerce')
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
            st.success("✅ Processamento concluído com sucesso!")
            st.dataframe(st.session_state['resultado_calculo'], use_container_width=True)
            
            buffer_bruto = io.BytesIO()
            with pd.ExcelWriter(buffer_bruto, engine='openpyxl') as writer:
                st.session_state['resultado_calculo'].to_excel(writer, index=False, sheet_name='Resultados_IRL')
            st.download_button("🟢 Baixar Tabela de Resultados", data=buffer_bruto.getvalue(), file_name="Resultados_Brutos_IRL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")

            st.divider()
            st.subheader("🔍 Identificação dos Compostos")
            tabela_editada = st.data_editor(st.session_state['tabela_identificacao'], use_container_width=True, disabled=["Pico", "TR_Medio", "IRL_Calculado"], hide_index=True)
            
            buffer_ident = io.BytesIO()
            with pd.ExcelWriter(buffer_ident, engine='openpyxl') as writer:
                tabela_editada.to_excel(writer, index=False, sheet_name='Identificacao')
            st.download_button("🟢 Baixar Tabela de Identificação Preenchida", data=buffer_ident.getvalue(), file_name="Identificacao_Compostos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")


# =========================================
# TELA 3: CURVA DE CALIBRAÇÃO (COM GRÁFICO E UNIDADES LIVRES)
# =========================================
elif ferramenta_escolhida == "📈 Curva de Calibração":
    st.title("📈 Curva de Calibração")
    st.write("Determine a concentração de amostras desconhecidas usando regressão linear.")

    # 0. CONFIGURAÇÃO DAS UNIDADES
    with st.expander("⚙️ Escolha suas Unidades (Opcional)", expanded=True):
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            unidade_conc = st.text_input("Unidade de Concentração (Ex: mg/L, ppm, %):", value="mg/L")
        with col_u2:
            unidade_sinal = st.text_input("Nome do Sinal (Ex: Área, Absorbância):", value="Área")

    st.divider()

    # 1. DADOS DO PADRÃO
    st.subheader("1. Construa a Curva do Padrão")
    st.write("Digite os valores da curva:")
    
    # Tabela vazia genérica (sem a unidade no nome base para não quebrar a memória do site)
    df_padrao_vazio = pd.DataFrame({'Concentracao': [None]*5, 'Sinal': [None]*5})
    
    # Mas aqui nós mostramos a coluna de forma elegante com as unidades escolhidas!
    tabela_padrao = st.data_editor(
        df_padrao_vazio, 
        column_config={
            "Concentracao": st.column_config.NumberColumn(f"Concentração ({unidade_conc})", format="%.4f"),
            "Sinal": st.column_config.NumberColumn(f"Sinal Lido ({unidade_sinal})", format="%.4f")
        },
        num_rows="dynamic", 
        use_container_width=True, 
        key="padrao_editor"
    )
    
    padrao_limpo = tabela_padrao.dropna(how='any').copy()
    a, b, r2 = None, None, None 
    
    if not padrao_limpo.empty and len(padrao_limpo) >= 2:
        try:
            # Tratamento caso o usuário digite com vírgula
            x = pd.to_numeric(padrao_limpo['Concentracao'].astype(str).str.replace(',', '.'), errors='coerce').dropna().values
            y = pd.to_numeric(padrao_limpo['Sinal'].astype(str).str.replace(',', '.'), errors='coerce').dropna().values
            
            if len(x) == len(y) and len(x) >= 2:
                # Matemática da Regressão Linear
                coefs = np.polyfit(x, y, 1)
                a = coefs[0] 
                b = coefs[1] 
                
                y_calc = np.polyval(coefs, x)
                sq_reg = np.sum((y_calc - np.mean(y))**2)
                sq_tot = np.sum((y - np.mean(y))**2)
                r2 = sq_reg / sq_tot if sq_tot != 0 else 0
                
                st.success("✅ Curva calculada com sucesso!")
                
                # Mostra Equação e R2
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Equação da Reta", value=f"y = {a:.4f}x + {b:.4f}")
                with col2:
                    if r2 >= 0.99: st.metric(label="R² (Coef. de Determinação)", value=f"{r2:.4f} 🟢")
                    elif r2 >= 0.95: st.metric(label="R² (Coef. de Determinação)", value=f"{r2:.4f} 🟡")
                    else: st.metric(label="R² (Coef. de Determinação)", value=f"{r2:.4f} 🔴 (Atenção)")
                
                # DESENHANDO O GRÁFICO
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.scatter(x, y, color='#1f77b4', label='Pontos do Padrão', zorder=3)
                ax.plot(x, y_calc, color='#d62728', linestyle='--', label='Reta Ajustada', zorder=2)
                ax.set_xlabel(f'Concentração ({unidade_conc})')
                ax.set_ylabel(f'{unidade_sinal}')
                ax.set_title('Curva de Calibração')
                ax.legend()
                ax.grid(True, linestyle=':', alpha=0.6, zorder=1)
                st.pyplot(fig) # Comando que joga a imagem na tela do site!
                
        except Exception as e:
            st.error("Erro ao calcular a curva. Verifique os dados digitados.")

    st.divider()

    # 2. DADOS DAS AMOSTRAS E DILUIÇÕES
    st.subheader("2. Interpolação das Amostras")
    st.write("Insira o sinal de cada amostra. O Fator de Diluição multiplicará o resultado final para encontrar a concentração real original.")
    
    df_amostras_vazio = pd.DataFrame({
        'Amostra': ["Amostra 1", "Amostra 2", None],
        'Sinal_Lido': [None, None, None],
        'FD': [1, 1, 1] 
    })
    
    tabela_amostras = st.data_editor(
        df_amostras_vazio, 
        column_config={
            "Amostra": "Nome da Amostra",
            "Sinal_Lido": st.column_config.NumberColumn(f"Sinal Lido ({unidade_sinal})", format="%.4f"),
            "FD": st.column_config.NumberColumn("Fator de Diluição (FD)", format="%.2f")
        },
        num_rows="dynamic", 
        use_container_width=True, 
        key="amostras_editor"
    )
    
    if st.button("🚀 Calcular Concentração das Amostras", use_container_width=True):
        if a is not None and b is not None:
            try:
                amostras_limpas = tabela_amostras.dropna(subset=['Sinal_Lido']).copy()
                
                sinais = pd.to_numeric(amostras_limpas['Sinal_Lido'].astype(str).str.replace(',', '.'), errors='coerce')
                fds = pd.to_numeric(amostras_limpas['FD'].astype(str).str.replace(',', '.'), errors='coerce')
                
                # x = (y - b) / a
                conc_lida = (sinais - b) / a
                conc_real = conc_lida * fds
                
                amostras_limpas[f'Concentração Lida ({unidade_conc})'] = conc_lida.round(4)
                amostras_limpas[f'Concentração Real ({unidade_conc})'] = conc_real.round(4)
                
                st.success("✅ Amostras quantificadas!")
                st.dataframe(amostras_limpas, use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error("Erro ao quantificar amostras. Verifique os dados.")
        else:
            st.error("⚠️ Você precisa preencher a Curva do Padrão primeiro e obter a equação da reta!")


# =========================================
# TELA 4: CONVERSÃO DE UNIDADES
# =========================================
elif ferramenta_escolhida == "🔄 Conversão de Unidades":
    st.title("🔄 Conversão de Unidades e Diluição")
    tipo_conversao = st.selectbox("Selecione o tipo de cálculo:", ["1. mg/mL ➔ ppm (ou µg/mL)", "2. ppm (ou µg/mL) ➔ mg/mL", "3. % (m/v) ➔ mg/mL", "4. mg/mL ➔ % (m/v)", "5. % (v/v) ➔ µL/mL", "6. Molaridade (mol/L) ➔ Concentração Comum (g/L)", "7. Concentração Comum (g/L) ➔ Molaridade (mol/L)", "8. Preparo de Diluições (C1V1 = C2V2)"])
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
    elif tipo_conversao == "5. % (v/v) ➔ µL/mL":
        valor = st.number_input("Digite a porcentagem em volume % (v/v):", min_value=0.0, format="%.4f")
        if valor > 0: st.success(f"🧪 **Resultado:** {valor}% (v/v) = **{valor * 10:.2f} µL/mL**")
    elif tipo_conversao == "6. Molaridade (mol/L) ➔ Concentração Comum (g/L)":
        molaridade = st.number_input("Molaridade (mol/L):", min_value=0.0, format="%.4f")
        massa_molar = st.number_input("Massa Molar do composto (g/mol):", min_value=0.0, format="%.2f")
        if molaridade > 0 and massa_molar > 0:
            conc_gl = molaridade * massa_molar
            st.success(f"🧪 **Resultado:** A concentração é **{conc_gl:.4f} g/L**")
    elif tipo_conversao == "7. Concentração Comum (g/L) ➔ Molaridade (mol/L)":
        conc_gl = st.number_input("Concentração Comum (g/L ou mg/mL):", min_value=0.0, format="%.4f")
        massa_molar = st.number_input("Massa Molar do composto (g/mol):", min_value=0.0, format="%.2f")
        if conc_gl > 0 and massa_molar > 0:
            molaridade = conc_gl / massa_molar
            st.success(f"🧪 **Resultado:** A molaridade é **{molaridade:.6f} mol/L** (M)")
    elif tipo_conversao == "8. Preparo de Diluições (C1V1 = C2V2)":
        descobrir = st.radio("O que você deseja calcular?", ["Volume Inicial (V1)", "Concentração Final (C2)"])
        if descobrir == "Volume Inicial (V1)":
            c1 = st.number_input("Concentração da solução ESTOQUE (C1):", min_value=0.0, format="%.4f")
            c2 = st.number_input("Concentração DESEJADA (C2):", min_value=0.0, format="%.4f")
            v2 = st.number_input("Volume final DESEJADO (V2):", min_value=0.0, format="%.4f")
            if c1 > 0 and c2 > 0 and v2 > 0:
                v1 = (c2 * v2) / c1
                st.success(f"🧪 **Você precisa pipetar:** **{v1:.4f}** da solução estoque.")
        elif descobrir == "Concentração Final (C2)":
            c1 = st.number_input("Concentração da solução ESTOQUE (C1):", min_value=0.0, format="%.4f")
            v1 = st.number_input("Volume pipetado (V1):", min_value=0.0, format="%.4f")
            v2 = st.number_input("Volume TOTAL final (V2):", min_value=0.0, format="%.4f")
            if c1 > 0 and v1 > 0 and v2 > 0:
                c2 = (c1 * v1) / v2
                st.success(f"🧪 **A Concentração Final (C2) será:** **{c2:.4f}**")
