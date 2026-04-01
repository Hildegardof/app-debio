import streamlit as st
import pandas as pd
import io
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------------------
# MENU LATERAL
# -----------------------------------------
st.sidebar.title("🧪 App DeBio")
st.sidebar.write("Navegação:")
ferramenta_escolhida = st.sidebar.radio(
    "Escolha o cálculo:",
    [
        "🌿 Rendimento de Extração", 
        "📊 Índice Aritmético e Identificação", 
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
# TELA 2: ÍNDICE ARITMÉTICO E IDENTIFICAÇÃO
# =========================================
elif ferramenta_escolhida == "📊 Índice Aritmético e Identificação":
    st.title("📊 Índice Aritmético (Kovats) e Identificação")
    st.write("Processamento de triplicatas e busca automática na biblioteca Adams.")

    # -----------------------------------------
    # GUIA RÁPIDO PARA INICIANTES (NOVO)
    # -----------------------------------------
    with st.expander("📖 **Como usar este módulo? (Passo a Passo para Iniciantes)**", expanded=False):
        st.markdown("""
        ### Bem-vindo à Identificação de Óleos Essenciais!
        Se este é o seu primeiro contato com cromatografia, siga este roteiro simples para processar seus dados:

        **1️⃣ A Régua (Alcanos):** Para descobrir quem é quem no seu óleo, o equipamento usa uma "régua" feita de Alcanos (carbonos puros). Vá na **Seção 2** e insira o Tempo de Retenção (TR) em que cada Alcano saiu no equipamento, e quantos carbonos ele tem (C8, C9, C10...).
        
        **2️⃣ A Amostra (Seu Óleo):**
        Vá na **Seção 1** e insira os dados do seu óleo. Você deve colocar o número do Pico, o Tempo de Retenção (TR) das três injeções, e a **Área Bruta (Absoluta)** de cada uma. Não se preocupe com a Área Relativa (%), o aplicativo vai calcular a média e a porcentagem de tudo sozinho!
        
        **3️⃣ A Biblioteca (O Dicionário):**
        Na **Seção 3**, defina a **Tolerância**. Na vida real, o índice da sua amostra quase nunca é perfeitamente igual ao do livro. Se você deixar a tolerância em `± 5`, o app vai procurar compostos no livro que estejam até 5 pontos para cima ou para baixo do seu resultado.
        
        **4️⃣ Processar e Escolher:**
        Clique no botão **"Processar"**. O aplicativo vai cruzar a sua amostra com a régua de alcanos (gerando o Índice de Kovats) e vai te dar uma lista de candidatos para cada pico.
        
        **5️⃣ Painel de Resolução:**
        Role até o final da página. Você verá várias caixinhas, uma para cada pico. Escolha o composto que faz mais sentido químico dentre as sugestões dadas. A Tabela Final vai se atualizar na mesma hora, pronta para você baixar e colocar no seu artigo!
        """)

    st.subheader("📥 0. Baixe os Templates Padrão")
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

    # 1. AMOSTRA
    st.subheader("1. Amostra (Triplicata)")
    metodo_amostra = st.radio("Inserir Amostra:", ["📂 Upload", "📋 Colar", "✍️ Digitar Manualmente"], horizontal=True, key="amo_radio")
    st.warning("⚠️ **ORDEM DA AMOSTRA:** Pico ➔ TR 1 ➔ TR 2 ➔ TR 3 ➔ Área Abs. 1 ➔ Área Abs. 2 ➔ Área Abs. 3")
    
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
        df_vazio_amo = pd.DataFrame(columns=['Pico', 'TR_1', 'TR_2', 'TR_3', 'Area_Abs_1', 'Area_Abs_2', 'Area_Abs_3'])
        for i in range(5): df_vazio_amo.loc[i] = [i+1, None, None, None, None, None, None]
        tabela_amostra = st.data_editor(df_vazio_amo, num_rows="dynamic", use_container_width=True, key="amo_editor")
        tabela_amostra = tabela_amostra.dropna(subset=['TR_1', 'TR_2', 'TR_3'], how='all').copy()
        tabela_amostra.columns = ['Pico', 'TR_1', 'TR_2', 'TR_3', 'Area_1', 'Area_2', 'Area_3']

    st.divider()

    # 2. ALCANOS
    st.subheader("2. Série Homóloga (Alcanos)")
    metodo_alcanos = st.radio("Inserir Alcanos:", ["📂 Upload", "📋 Colar", "✍️ Digitar Manualmente"], horizontal=True, key="alc_radio")
    st.warning("⚠️ **ORDEM DOS ALCANOS:** TR do Alcano ➔ Número de Carbonos")
    
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

    st.divider()

    # 3. BIBLIOTECA ADAMS
    st.subheader("📚 3. Identificação Automática")
    
    bib = None
    try:
        bib = pd.read_excel("Biblioteca_Adams.xlsx")
        st.success("✅ Biblioteca interna localizada automaticamente!")
    except Exception:
        st.info("💡 Não localizamos a biblioteca nos bastidores. Por favor, suba o arquivo 'Biblioteca_Adams.xlsx' abaixo:")
        arq_bib_upload = st.file_uploader("Suba a Tabela do Adams (.xlsx)", type=["xlsx"])
        if arq_bib_upload:
            bib = pd.read_excel(arq_bib_upload)
            st.success("✅ Biblioteca carregada com sucesso!")

    tolerancia = st.number_input("Tolerância do IRL (±)", min_value=0, max_value=20, value=5, help="Margem de erro para buscar o composto.")

    # PROCESSAMENTO MESTRE
    if tabela_amostra is not None and not tabela_amostra.empty and tabela_alcanos is not None and not tabela_alcanos.empty:
        st.divider()
        if st.button("🚀 Processar Cálculo e Identificação", use_container_width=True):
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
                
                candidatos_por_pico = {}
                classes_por_pico = {}
                
                if bib is not None:
                    bib['IRL'] = pd.to_numeric(bib['IRL'], errors='coerce')
                    irls_lit, sugestoes, identificacoes_finais, classes_finais = [], [], [], []
                    
                    for idx, irl_calc in enumerate(df_ident['IRL_Calculado']):
                        pico_atual = df_ident['Pico'].iloc[idx]
                        if pd.isna(irl_calc):
                            irls_lit.append("")
                            sugestoes.append("")
                            identificacoes_finais.append("")
                            classes_finais.append("")
                            candidatos_por_pico[pico_atual] = [""]
                            classes_por_pico[pico_atual] = {}
                            continue
                            
                        matches = bib[(bib['IRL'] >= irl_calc - tolerancia) & (bib['IRL'] <= irl_calc + tolerancia)]
                        
                        if not matches.empty:
                            irls_lit.append(" / ".join(matches['IRL'].astype(int).astype(str).tolist()))
                            sugestoes.append(" / ".join(matches['Composto'].astype(str).tolist()))
                            
                            lista_candidatos = [""] + matches['Composto'].astype(str).tolist() + ["Outro (Digitar Manualmente)"]
                            candidatos_por_pico[pico_atual] = lista_candidatos
                            
                            nome_col_classe = 'Classe_Quimica' if 'Classe_Quimica' in matches.columns else ('Classe' if 'Classe' in matches.columns else None)
                            mapa_classes = {"": ""}
                            if nome_col_classe:
                                for _, row_match in matches.iterrows():
                                    mapa_classes[str(row_match['Composto'])] = str(row_match[nome_col_classe])
                            classes_por_pico[pico_atual] = mapa_classes
                            
                            if len(matches) == 1:
                                identificacoes_finais.append(matches['Composto'].iloc[0])
                                classes_finais.append(mapa_classes.get(matches['Composto'].iloc[0], ""))
                            else:
                                identificacoes_finais.append("") 
                                classes_finais.append("")
                        else:
                            irls_lit.append("")
                            sugestoes.append("Nenhum na faixa")
                            identificacoes_finais.append("")
                            classes_finais.append("")
                            candidatos_por_pico[pico_atual] = ["", "Digitar Manualmente"]
                            classes_por_pico[pico_atual] = {}
                            
                    df_ident['IRL_Literatura'] = irls_lit
                    df_ident['Sugestoes_Adams'] = sugestoes
                    df_ident['Identificacao_Final'] = identificacoes_finais
                    df_ident['Classe_Quimica'] = classes_finais
                else:
                    df_ident['IRL_Literatura'] = ""
                    df_ident['Sugestoes_Adams'] = "Sem Biblioteca"
                    df_ident['Identificacao_Final'] = ""
                    df_ident['Classe_Quimica'] = ""
                    for p in df_ident['Pico']: candidatos_por_pico[p] = [""]
                    
                st.session_state['tabela_identificacao'] = df_ident
                st.session_state['candidatos'] = candidatos_por_pico
                st.session_state['mapa_classes'] = classes_por_pico
                
            except Exception as e:
                st.error(f"Erro no processamento. Verifique se digitou letras no lugar de números. Erro: {e}")

        if 'resultado_calculo' in st.session_state:
            st.success("✅ Processamento concluído!")
            
            container_tabela = st.container()
            container_resolucao = st.container()
            
            with container_resolucao:
                st.divider()
                st.subheader("🎯 Resolução de Identidade dos Picos")
                st.write("Use os menus abaixo para selecionar o composto final de cada pico. A tabela acima será atualizada automaticamente.")
                
                df_atual = st.session_state['tabela_identificacao']
                col1, col2 = st.columns(2)
                
                for idx, row in df_atual.iterrows():
                    pico = row['Pico']
                    irl = row['IRL_Calculado']
                    
                    opcoes_brutas = st.session_state['candidatos'].get(pico, [""])
                    if isinstance(opcoes_brutas, dict): 
                        opcoes_brutas = list(opcoes_brutas.keys())
                    elif not isinstance(opcoes_brutas, (list, tuple, np.ndarray)):
                        opcoes_brutas = [""]
                        
                    opcoes = [str(x) for x in opcoes_brutas]
                    valor_atual = str(row.get('Identificacao_Final', ""))
                    
                    with col1 if idx % 2 == 0 else col2:
                        escolha = st.selectbox(
                            f"Pico {pico} (IRL {irl})", 
                            options=opcoes, 
                            index=opcoes.index(valor_atual) if valor_atual in opcoes else 0,
                            key=f"pico_{pico}"
                        )
                        
                        st.session_state['tabela_identificacao'].at[idx, 'Identificacao_Final'] = escolha
                        if escolha and escolha != "Outro (Digitar Manualmente)" and escolha != "Digitar Manualmente":
                            classe = str(st.session_state['mapa_classes'].get(pico, {}).get(escolha, ""))
                            st.session_state['tabela_identificacao'].at[idx, 'Classe_Quimica'] = classe

            with container_tabela:
                st.divider()
                st.subheader("📋 Tabela Final de Resultados")
                st.write("Esta tabela reflete as suas escolhas e está pronta para ir direto para o artigo.")
                
                st.dataframe(st.session_state['tabela_identificacao'], use_container_width=True, hide_index=True)
                
                buffer_ident = io.BytesIO()
                with pd.ExcelWriter(buffer_ident, engine='openpyxl') as writer:
                    st.session_state['tabela_identificacao'].to_excel(writer, index=False, sheet_name='Identificacao_DeBio')
                st.download_button("🟢 Baixar Tabela Pronta em Excel", data=buffer_ident.getvalue(), file_name="Tabela_Final_Identificacao.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")

# =========================================
# TELA 3 e 4: (CURVA DE CALIBRAÇÃO E UNIDADES CONTINUAM INTACTAS)
# =========================================
elif ferramenta_escolhida == "📈 Curva de Calibração":
    st.title("📈 Curva de Calibração")
    with st.expander("⚙️ Escolha suas Unidades (Opcional)", expanded=True):
        col_u1, col_u2 = st.columns(2)
        with col_u1: unidade_conc = st.text_input("Unidade de Concentração (Ex: mg/L, ppm, %):", value="mg/L")
        with col_u2: unidade_sinal = st.text_input("Nome do Sinal (Ex: Área, Absorbância):", value="Área")

    st.divider()
    st.subheader("1. Construa a Curva do Padrão")
    df_padrao_vazio = pd.DataFrame({'Concentracao': [None]*5, 'Sinal': [None]*5})
    tabela_padrao = st.data_editor(df_padrao_vazio, column_config={"Concentracao": st.column_config.NumberColumn(f"Concentração ({unidade_conc})", format="%.4f"),"Sinal": st.column_config.NumberColumn(f"Sinal Lido ({unidade_sinal})", format="%.4f")},num_rows="dynamic", use_container_width=True, key="padrao_editor")
    
    padrao_limpo = tabela_padrao.dropna(how='any').copy()
    a, b, r2 = None, None, None 
    
    if not padrao_limpo.empty and len(padrao_limpo) >= 2:
        try:
            x = pd.to_numeric(padrao_limpo['Concentracao'].astype(str).str.replace(',', '.'), errors='coerce').dropna().values
            y = pd.to_numeric(padrao_limpo['Sinal'].astype(str).str.replace(',', '.'), errors='coerce').dropna().values
            if len(x) == len(y) and len(x) >= 2:
                coefs = np.polyfit(x, y, 1)
                a, b = coefs[0], coefs[1]
                y_calc = np.polyval(coefs, x)
                sq_reg, sq_tot = np.sum((y_calc - np.mean(y))**2), np.sum((y - np.mean(y))**2)
                r2 = sq_reg / sq_tot if sq_tot != 0 else 0
                
                col1, col2 = st.columns(2)
                with col1: st.metric(label="Equação da Reta", value=f"y = {a:.4f}x + {b:.4f}")
                with col2:
                    if r2 >= 0.99: st.metric(label="R²", value=f"{r2:.4f} 🟢")
                    elif r2 >= 0.95: st.metric(label="R²", value=f"{r2:.4f} 🟡")
                    else: st.metric(label="R²", value=f"{r2:.4f} 🔴")
                
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.scatter(x, y, color='#1f77b4')
                ax.plot(x, y_calc, color='#d62728', linestyle='--')
                ax.set_xlabel(f'Concentração ({unidade_conc})')
                ax.set_ylabel(f'{unidade_sinal}')
                ax.grid(True, linestyle=':', alpha=0.6)
                st.pyplot(fig)
        except Exception as e: st.error("Erro ao calcular a curva.")

    st.divider()
    st.subheader("2. Interpolação das Amostras")
    df_amostras_vazio = pd.DataFrame({'Amostra': ["Amostra 1", "Amostra 2", None], 'Sinal_Lido': [None, None, None], 'FD': [1, 1, 1]})
    tabela_amostras = st.data_editor(df_amostras_vazio, column_config={"Amostra": "Nome da Amostra", "Sinal_Lido": st.column_config.NumberColumn(f"Sinal Lido ({unidade_sinal})", format="%.4f"), "FD": st.column_config.NumberColumn("Fator de Diluição (FD)", format="%.2f")}, num_rows="dynamic", use_container_width=True)
    
    if st.button("🚀 Calcular Concentração das Amostras", use_container_width=True):
        if a is not None and b is not None:
            try:
                amostras_limpas = tabela_amostras.dropna(subset=['Sinal_Lido']).copy()
                sinais = pd.to_numeric(amostras_limpas['Sinal_Lido'].astype(str).str.replace(',', '.'), errors='coerce')
                fds = pd.to_numeric(amostras_limpas['FD'].astype(str).str.replace(',', '.'), errors='coerce')
                conc_lida = (sinais - b) / a
                amostras_limpas[f'Concentração Lida ({unidade_conc})'] = conc_lida.round(4)
                amostras_limpas[f'Concentração Real ({unidade_conc})'] = (conc_lida * fds).round(4)
                st.success("✅ Amostras quantificadas!")
                st.dataframe(amostras_limpas, use_container_width=True, hide_index=True)
            except Exception as e: st.error("Erro ao quantificar amostras.")

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
