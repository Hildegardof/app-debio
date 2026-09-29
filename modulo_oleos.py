import streamlit as st
import pandas as pd
import io
import numpy as np
import matplotlib.pyplot as plt
import os

import modulo_utils as utils

def renderizar_oleos():
    if 'amostras_salvas' not in st.session_state:
        st.session_state['amostras_salvas'] = {}

    ferramenta_escolhida = st.sidebar.radio(
        "Selecione a ferramenta:",
        ["Rendimento de Extração", "Índice Aritmético e Identificação", "Comparativo de Amostras"]
    )

    # =========================================
    # MÓDULO 1: RENDIMENTO DE EXTRAÇÃO
    # =========================================
    if ferramenta_escolhida == "Rendimento de Extração":
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
    # MÓDULO 2: ÍNDICE ARITMÉTICO E IDENTIFICAÇÃO
    # =========================================
    elif ferramenta_escolhida == "Índice Aritmético e Identificação":
        st.title("📊 Índice Aritmético (Kovats) e Identificação")
        st.write("Processamento de dados cromatográficos com injeções dinâmicas e suporte a arquivos Excel.")

        with st.expander("📖 **MANUAL DE USO: Passo a Passo Detalhado**", expanded=False):
            st.markdown("""
            ### 🗺️ Guia de Fluxo de Trabalho Cromatográfico
            Siga estas etapas cronológicas para processar sua corrida de CG-MS sem erros:

            #### 🔹 Passo 1: Configuração de Réplicas (O 'n' da Análise)
            * Digite quantas injeções foram feitas da **Amostra** e quantas foram feitas dos
              **Alcanos** — são dois números independentes, cada tabela se adapta ao seu próprio n
              (não precisam ser iguais). As colunas de ambas identificam o número da injeção
              (Injeção 1, Injeção 2...) para não haver dúvida de qual TR é qual.

            #### 🔹 Passo 2: Inserção dos Dados Brutos
            * Insira os dados dos Alcanos (TR de cada injeção e Carbonos) e da Amostra (TRs, Áreas).
            * Você pode digitar direto nas células da tabela, **colar dados copiados do Excel**
              (clique na célula onde quer começar e use Ctrl+V — funciona colando uma coluna
              inteira, uma linha inteira ou um bloco de células de uma vez) ou fazer upload de um
              arquivo `.xlsx` já pronto.
            * Na tabela da Amostra, o número do **Pico** é preenchido automaticamente pela ordem
              das linhas (não precisa digitar) — cole quantas linhas de TR/Área precisar que a
              numeração dos picos se ajusta sozinha.
            * **Importante:** nas colunas de TR e Área, use **vírgula** para separar as casas
              decimais (padrão brasileiro, ex.: 6,205) e não use ponto como separador de milhar —
              essas colunas são de texto justamente para aceitar o formato brasileiro sem erro.

            #### 🔹 Passo 3: O Processamento Mestre
            * Clique no botão **"Processar Cálculo"**. O sistema calculará médias, DP/RSD% das réplicas
              (tanto da amostra quanto dos alcanos), % de Área, IRL e fará o Match com o Adams.

            #### 🔹 Passo 4: A Tabela Interativa de Identificação
            * Role até **"Tabela Interativa de Identificação"**: cada pico aparece em uma linha, já
              com os dados calculados, e uma caixa de seleção — clique nela para ver os compostos
              candidatos do Adams (cada um já mostrando o seu IRL de literatura) e escolha o correto.
              O IRL de literatura e a Classe Química daquela linha são preenchidos automaticamente.
            * Se depois disso você mudar a **Tolerância do IRL (±)** e clicar em "Processar Cálculo"
              novamente, o sistema tenta preservar todas as identificações já feitas (avisando quando
              algum composto escolhido deixou de ser candidato válido na nova tolerância).

            #### 🔹 Passo 5: Exportação e Salvamento
            * Baixe a Tabela Pronta em Excel.
            * **Dica:** Use o bloco "💾 Salvar para Comparação" no final da tela para mandar essa amostra direto para a aba de Comparativos ou para o módulo de Laudos!
            """)

        st.subheader("⚙️ Configuração Analítica")
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            num_leituras = st.number_input("Nº de injeções/leituras da AMOSTRA (n):", min_value=1, max_value=10, value=3, step=1, key="num_leituras_amo")
        with col_n2:
            num_leituras_alc = st.number_input("Nº de injeções/leituras dos ALCANOS (n):", min_value=1, max_value=10, value=3, step=1, key="num_leituras_alc")

        cols_tr = [f'TR_{i}' for i in range(1, num_leituras + 1)]
        cols_area = [f'Area_Abs_{i}' for i in range(1, num_leituras + 1)]
        todas_cols_amostra = ['Pico'] + cols_tr + cols_area

        # A série de alcanos agora tem seu próprio número de injeções (n), independente do
        # configurado para a amostra — cada tabela pode ter uma quantidade diferente de réplicas.
        cols_tr_alc = [f'TR_Alcano_{i}' for i in range(1, num_leituras_alc + 1)]
        todas_cols_alcanos = cols_tr_alc + ['Carbonos']

        # As colunas de TR e Área usam TextColumn (texto), e não NumberColumn, de propósito:
        # o NumberColumn do Streamlit interpreta o número digitado/colado com a convenção
        # americana (vírgula = separador de milhar, ponto = decimal) — ao colar um valor no
        # padrão brasileiro como "6,205" ele vira 6205 antes mesmo de chegar ao nosso código.
        # Com TextColumn o texto chega intacto e é o `utils.parse_numero_br()` (chamado no
        # processamento) quem converte a vírgula brasileira para o ponto decimal corretamente.
        # 'Pico' não é mais uma coluna editável na tabela interativa: ela é numerada
        # automaticamente pela ordem das linhas depois que os dados são coletados, logo abaixo.
        # Isso evita picos com número em branco quando se cola uma coluna de TR/Área maior do
        # que o número de linhas já preenchidas (o Streamlit adiciona linhas automaticamente).
        dica_decimal = "Use vírgula para decimais, como no padrão brasileiro (ex.: 6,205). Não use ponto de milhar."
        config_cols_amostra = {}
        for _i, _c in enumerate(cols_tr, start=1):
            config_cols_amostra[_c] = st.column_config.TextColumn(f"TR (min) — Injeção {_i}", help=dica_decimal)
        for _i, _c in enumerate(cols_area, start=1):
            config_cols_amostra[_c] = st.column_config.TextColumn(f"Área — Injeção {_i}", help=dica_decimal)

        config_cols_alcanos = {'Carbonos': st.column_config.NumberColumn("Nº de Carbonos", format="%d")}
        for _i, _c in enumerate(cols_tr_alc, start=1):
            config_cols_alcanos[_c] = st.column_config.TextColumn(f"TR (min) — Injeção {_i}", help=dica_decimal)

        st.subheader("📥 0. Baixe os Templates Padrão")
        col_temp1, col_temp2 = st.columns(2)

        dados_ex_amo = {'Pico': [1, 2]}
        for c_tr in cols_tr: dados_ex_amo[c_tr] = [12.45, 15.10]
        for c_ar in cols_area: dados_ex_amo[c_ar] = [150000, 340000]
        df_temp_amostra = pd.DataFrame(dados_ex_amo)

        with col_temp1:
            st.download_button(
                f"📄 Baixar Template da Amostra (.xlsx, n={num_leituras})",
                data=utils.exportar_excel_bytes(df_temp_amostra, sheet_name='Amostra'),
                file_name=f"Template_Amostra_{num_leituras}x_DeBio.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        dados_ex_alc = {}
        for c_tr in cols_tr_alc: dados_ex_alc[c_tr] = [5.20, 8.45]
        dados_ex_alc['Carbonos'] = [8, 9]
        df_temp_alcanos = pd.DataFrame(dados_ex_alc)
        with col_temp2:
            st.download_button(
                f"📄 Baixar Template de Alcanos (.xlsx, n={num_leituras_alc})",
                data=utils.exportar_excel_bytes(df_temp_alcanos, sheet_name='Alcanos'),
                file_name=f"Template_Alcanos_{num_leituras_alc}x_DeBio.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.divider()

        st.subheader("1. Dados da Amostra")
        metodo_amostra = st.radio("Inserir Amostra:", ["📂 Upload", "✍️ Digitar ou Colar (Tabela Interativa)"], horizontal=True, key="amo_radio")

        tabela_amostra = None
        if metodo_amostra == "📂 Upload":
            arq_amostra = st.file_uploader("Suba o arquivo Excel da Amostra (.xlsx)", type=["xlsx"], key="up_amo")
            if arq_amostra:
                try:
                    tabela_amostra = pd.read_excel(arq_amostra)
                    if len(tabela_amostra.columns) >= len(todas_cols_amostra):
                        tabela_amostra = tabela_amostra.iloc[:, :len(todas_cols_amostra)]
                        tabela_amostra.columns = todas_cols_amostra
                    else:
                        st.warning(f"⚠️ **Atenção:** Configuração exige {len(todas_cols_amostra)} colunas para n={num_leituras}.")
                        tabela_amostra = None
                except Exception as e:
                    st.error(f"Erro: {e}")
                    tabela_amostra = None
        elif metodo_amostra == "✍️ Digitar ou Colar (Tabela Interativa)":
            st.caption(
                "💡 Digite direto nas células ou copie do Excel e cole (Ctrl+V) na tabela abaixo — "
                "funciona colando uma coluna inteira, uma linha inteira ou um bloco de células de "
                "uma vez, a partir da célula selecionada. Use **vírgula** para separar as casas "
                "decimais (padrão brasileiro, ex.: 6,205) — não use ponto como separador de milhar. "
                "O número do **Pico** é preenchido automaticamente pela ordem das linhas."
            )
            # Apenas as colunas de TR/Área são editáveis aqui — 'Pico' é calculado depois, pela
            # ordem final das linhas, então nunca fica em branco mesmo colando uma coluna maior
            # do que o número de linhas já preenchidas. Começam com "" (texto), não None: um
            # valor None faz o pandas inferir a coluna inteira como float64, o que o Streamlit
            # recusa combinar com TextColumn (necessário para aceitar vírgula decimal).
            df_vazio_amo = pd.DataFrame(columns=cols_tr + cols_area)
            for i in range(5): df_vazio_amo.loc[i] = ['']*num_leituras + ['']*num_leituras
            df_vazio_amo = df_vazio_amo.reset_index(drop=True)  # RangeIndex "real", exigido para hide_index funcionar com num_rows dinâmico
            tabela_amostra = st.data_editor(
                df_vazio_amo, num_rows="dynamic", use_container_width=True, hide_index=True,
                column_config=config_cols_amostra, key="amo_editor",
            )
            tabela_amostra = tabela_amostra[
                tabela_amostra[cols_tr[0]].fillna('').astype(str).str.strip() != ''
            ].reset_index(drop=True).copy()
            tabela_amostra.insert(0, 'Pico', range(1, len(tabela_amostra) + 1))

        st.divider()

        st.subheader("2. Série Homóloga (Alcanos)")
        st.caption(f"Configurada para n={num_leituras_alc} injeção(ões) por alcano — número independente do definido para a amostra.")
        metodo_alcanos = st.radio("Inserir Alcanos:", ["📂 Upload", "✍️ Digitar ou Colar (Tabela Interativa)"], horizontal=True, key="alc_radio")

        tabela_alcanos = None
        if metodo_alcanos == "📂 Upload":
            arq_alcanos = st.file_uploader("Suba o arquivo Excel de Alcanos (.xlsx)", type=["xlsx"], key="up_alc")
            if arq_alcanos:
                try:
                    tabela_alcanos = pd.read_excel(arq_alcanos)
                    if len(tabela_alcanos.columns) >= len(todas_cols_alcanos):
                        tabela_alcanos = tabela_alcanos.iloc[:, :len(todas_cols_alcanos)]
                        tabela_alcanos.columns = todas_cols_alcanos
                    else:
                        st.warning(f"⚠️ **Atenção:** Configuração exige {len(todas_cols_alcanos)} coluna(s) (TR de cada injeção + Carbonos) para n={num_leituras_alc}.")
                        tabela_alcanos = None
                except Exception as e:
                    st.error(f"🚫 Não foi possível ler o arquivo de alcanos: {e}")
                    tabela_alcanos = None
        elif metodo_alcanos == "✍️ Digitar ou Colar (Tabela Interativa)":
            st.caption(
                "💡 Digite direto nas células ou copie do Excel e cole (Ctrl+V) na tabela abaixo — "
                "funciona colando uma coluna inteira, uma linha inteira ou um bloco de células de "
                "uma vez, a partir da célula selecionada. Use **vírgula** para separar as casas "
                "decimais (padrão brasileiro, ex.: 8,45) — não use ponto como separador de milhar."
            )
            # Mesma lógica da amostra: "" (texto) em vez de None, para o Streamlit aceitar
            # TextColumn nessas colunas (necessário para a vírgula decimal brasileira).
            df_vazio_alc = pd.DataFrame(columns=todas_cols_alcanos)
            carbonos_padrao = [8, 9, 10, 11, 12]
            for i in range(5):
                df_vazio_alc.loc[i] = [''] * num_leituras_alc + [carbonos_padrao[i]]
            df_vazio_alc = df_vazio_alc.reset_index(drop=True)  # RangeIndex "real", exigido para hide_index funcionar com num_rows dinâmico
            tabela_alcanos = st.data_editor(
                df_vazio_alc, num_rows="dynamic", use_container_width=True, hide_index=True,
                column_config=config_cols_alcanos, key="alc_editor",
            )
            tabela_alcanos = tabela_alcanos[
                tabela_alcanos[cols_tr_alc[0]].fillna('').astype(str).str.strip() != ''
            ].copy()

        st.divider()

        st.subheader("📚 3. Identificação Automática")
        bib = None
        try:
            pasta_atual = os.path.dirname(os.path.abspath(__file__))
            caminho_biblioteca = os.path.join(pasta_atual, "Biblioteca_Adams.xlsx")
            bib = pd.read_excel(caminho_biblioteca)
            st.success("✅ Biblioteca interna localizada automaticamente!")
        except Exception:
            arq_bib_upload = st.file_uploader("Suba a Tabela do Adams (.xlsx)", type=["xlsx"])
            if arq_bib_upload: bib = pd.read_excel(arq_bib_upload)

        tolerancia = st.number_input("Tolerância do IRL (±)", min_value=0, max_value=20, value=5)

        if tabela_amostra is not None and not tabela_amostra.empty and tabela_alcanos is not None and not tabela_alcanos.empty:
            st.divider()
            if st.button("🚀 Processar Cálculo e Identificação", use_container_width=True):
                colunas_presentes = tabela_amostra.columns.tolist()
                colunas_faltantes = [c for c in cols_tr + cols_area if c not in colunas_presentes]
                colunas_faltantes_alc = [c for c in cols_tr_alc + ['Carbonos'] if c not in tabela_alcanos.columns.tolist()]

                if colunas_faltantes:
                    st.error(f"🚫 **Erro de Estrutura (Amostra):** Colunas ausentes para n={num_leituras}: {', '.join(colunas_faltantes)}")
                elif colunas_faltantes_alc:
                    st.error(f"🚫 **Erro de Estrutura (Alcanos):** Colunas ausentes para n={num_leituras_alc}: {', '.join(colunas_faltantes_alc)}")
                else:
                    try:
                        amostra = tabela_amostra.copy()
                        alcanos = tabela_alcanos.copy()

                        for col in cols_tr + cols_area:
                            amostra[col] = utils.parse_numero_br(amostra[col])

                        # Estatística das réplicas de injeção (TR e Área): média, DP e RSD% —
                        # critério de qualidade cromatográfica padrão (RSD do TR tipicamente
                        # aceito até 5% na literatura de validação de métodos por CG).
                        stats_tr = utils.estatisticas_replicatas(amostra, cols_tr)
                        stats_area = utils.estatisticas_replicatas(amostra, cols_area)

                        amostra['TR_Medio'] = stats_tr['Media']
                        amostra['DP_TR'] = stats_tr['DP']
                        amostra['RSD_TR_%'] = stats_tr['RSD_%']

                        amostra['Area_Media'] = stats_area['Media']
                        amostra['RSD_Area_%'] = stats_area['RSD_%']

                        soma_areas = amostra['Area_Media'].sum()
                        amostra['Area_Relativa_%'] = (amostra['Area_Media'] / soma_areas) * 100

                        # Estatística das réplicas de injeção dos ALCANOS (TR): mesma lógica de
                        # DP/RSD% usada na amostra, agora também aplicada ao padrão homólogo.
                        for col in cols_tr_alc:
                            alcanos[col] = utils.parse_numero_br(alcanos[col])
                        alcanos['Carbonos'] = utils.parse_numero_br(alcanos['Carbonos'])

                        stats_alc = utils.estatisticas_replicatas(alcanos, cols_tr_alc)
                        alcanos['TR_Alcano'] = stats_alc['Media']
                        alcanos['RSD_Alcano_%'] = stats_alc['RSD_%'].round(2)

                        alcanos = alcanos.dropna(subset=['TR_Alcano', 'Carbonos']).sort_values(by='TR_Alcano').reset_index(drop=True)
                        st.session_state['alcanos_stats'] = alcanos[['Carbonos', 'TR_Alcano', 'RSD_Alcano_%']].copy()

                        lista_irl = []
                        for _, linha in amostra.iterrows():
                            tr_x = linha['TR_Medio']
                            if pd.isna(tr_x):
                                lista_irl.append(None)
                                continue
                            antes = alcanos[alcanos['TR_Alcano'] <= tr_x]
                            depois = alcanos[alcanos['TR_Alcano'] > tr_x]
                            if antes.empty or depois.empty: lista_irl.append(None)
                            else:
                                tr_n = antes.iloc[-1]['TR_Alcano']
                                n = antes.iloc[-1]['Carbonos']
                                tr_n1 = depois.iloc[0]['TR_Alcano']
                                irl = 100 * (n + ((tr_x - tr_n) / (tr_n1 - tr_n)))
                                lista_irl.append(round(irl))

                        amostra['IRL_Calculado'] = lista_irl
                        amostra['TR_Medio'] = amostra['TR_Medio'].round(3)
                        amostra['DP_TR'] = amostra['DP_TR'].round(4)
                        amostra['RSD_TR_%'] = amostra['RSD_TR_%'].round(2)
                        amostra['Area_Media'] = amostra['Area_Media'].round(2)
                        amostra['Area_Relativa_%'] = amostra['Area_Relativa_%'].round(2)
                        amostra['RSD_Area_%'] = amostra['RSD_Area_%'].round(2)

                        # Captura as identificações já feitas antes de reconstruir a tabela do zero
                        # (ex.: usuário mudou a Tolerância do IRL e clicou em "Processar Cálculo" de
                        # novo) — sem isso, todo reprocessamento apagaria as escolhas manuais já feitas.
                        selecao_anterior = {}
                        tabela_anterior = st.session_state.get('tabela_identificacao')
                        if tabela_anterior is not None:
                            for _, linha_ant in tabela_anterior.iterrows():
                                escolha_ant = str(linha_ant.get('Identificacao_Final', '') or '')
                                if escolha_ant:
                                    selecao_anterior[linha_ant['Pico']] = escolha_ant

                        st.session_state['resultado_calculo'] = amostra
                        df_ident = amostra[['Pico', 'TR_Medio', 'RSD_TR_%', 'IRL_Calculado', 'Area_Relativa_%', 'RSD_Area_%']].copy()

                        opcoes_por_pico = {}
                        escolhas_preservadas, escolhas_perdidas = [], []
                        opcao_vazia = {"label": "— selecione —", "composto": "", "irl_lit": None, "classe": ""}

                        if bib is not None:
                            bib['IRL'] = pd.to_numeric(bib['IRL'], errors='coerce')
                            nome_col_classe = 'Classe_Quimica' if 'Classe_Quimica' in bib.columns else ('Classe' if 'Classe' in bib.columns else None)
                            irls_lit, sugestoes, identificacoes_finais, classes_finais = [], [], [], []

                            for idx, irl_calc in enumerate(df_ident['IRL_Calculado']):
                                pico_atual = df_ident['Pico'].iloc[idx]
                                escolha_previa = selecao_anterior.get(pico_atual, "")

                                if pd.isna(irl_calc):
                                    irls_lit.append(""); sugestoes.append(""); identificacoes_finais.append(""); classes_finais.append("")
                                    opcoes_por_pico[pico_atual] = [dict(opcao_vazia, label="(sem IRL calculado)")]
                                    continue

                                matches = bib[(bib['IRL'] >= irl_calc - tolerancia) & (bib['IRL'] <= irl_calc + tolerancia)].copy()

                                if not matches.empty:
                                    matches['dif_irl'] = (matches['IRL'] - irl_calc).abs()
                                    # Biblioteca_Adams.xlsx contém entradas duplicadas (mesmo Composto+IRL) —
                                    # removidas aqui para não repetir o mesmo candidato na lista de seleção.
                                    matches = matches.sort_values('dif_irl').drop_duplicates(subset=['Composto', 'IRL'])

                                    candidatos = [dict(opcao_vazia)]
                                    for _, m in matches.iterrows():
                                        classe_m = str(m[nome_col_classe]) if nome_col_classe else ""
                                        candidatos.append({
                                            "label": f"{m['Composto']}  (IRL Lit.: {m['IRL']:.0f})",
                                            "composto": str(m['Composto']),
                                            "irl_lit": float(m['IRL']),
                                            "classe": classe_m,
                                        })
                                    candidatos.append({"label": "Outro/Não Identificado", "composto": "Outro/Não Identificado", "irl_lit": None, "classe": ""})
                                    opcoes_por_pico[pico_atual] = candidatos

                                    lista_irl_candidatas = " / ".join(matches['IRL'].round(0).astype(int).astype(str).tolist())
                                    lista_compostos_candidatos = " / ".join(matches['Composto'].astype(str).tolist())

                                    escolha_resolvida = None
                                    if escolha_previa and escolha_previa in [c['composto'] for c in candidatos if c['composto']]:
                                        escolha_resolvida = next(c for c in candidatos if c['composto'] == escolha_previa)
                                        escolhas_preservadas.append(pico_atual)
                                    elif len(matches) == 1:
                                        escolha_resolvida = next(c for c in candidatos if c['composto'] == str(matches['Composto'].iloc[0]))
                                        if escolha_previa:
                                            # A escolha manual anterior não está mais entre os candidatos
                                            # (mudou de faixa), mas agora há um único match automático —
                                            # ainda assim, avisa o usuário de que a escolha anterior mudou.
                                            escolhas_perdidas.append((pico_atual, escolha_previa))
                                    elif escolha_previa:
                                        escolhas_perdidas.append((pico_atual, escolha_previa))

                                    if escolha_resolvida is not None and escolha_resolvida['composto']:
                                        identificacoes_finais.append(escolha_resolvida['composto'])
                                        classes_finais.append(escolha_resolvida['classe'])
                                        irls_lit.append(f"{escolha_resolvida['irl_lit']:.0f}" if escolha_resolvida['irl_lit'] is not None else "")
                                    else:
                                        identificacoes_finais.append("")
                                        classes_finais.append("")
                                        irls_lit.append(lista_irl_candidatas)
                                    sugestoes.append(lista_compostos_candidatos)
                                else:
                                    irls_lit.append(""); sugestoes.append("Nenhum na faixa"); identificacoes_finais.append(""); classes_finais.append("")
                                    opcoes_por_pico[pico_atual] = [
                                        dict(opcao_vazia),
                                        {"label": "Digitar Manualmente", "composto": "Digitar Manualmente", "irl_lit": None, "classe": ""},
                                    ]
                                    if escolha_previa:
                                        escolhas_perdidas.append((pico_atual, escolha_previa))

                            df_ident['IRL_Literatura'] = irls_lit
                            df_ident['Sugestoes_Adams'] = sugestoes
                            df_ident['Identificacao_Final'] = identificacoes_finais
                            df_ident['Classe_Quimica'] = classes_finais
                        else:
                            df_ident['IRL_Literatura'] = ""; df_ident['Sugestoes_Adams'] = "Sem Biblioteca"; df_ident['Identificacao_Final'] = ""; df_ident['Classe_Quimica'] = ""
                            for p in df_ident['Pico']:
                                opcoes_por_pico[p] = [dict(opcao_vazia)]

                        st.session_state['tabela_identificacao'] = df_ident
                        st.session_state['opcoes_identificacao'] = opcoes_por_pico

                        if escolhas_preservadas:
                            st.caption(f"✅ {len(escolhas_preservadas)} identificação(ões) já feita(s) foram mantidas após o reprocessamento.")
                        if escolhas_perdidas:
                            texto_perdidas = "; ".join(f"Pico {p} (era '{c}')" for p, c in escolhas_perdidas)
                            st.warning(
                                "⚠️ Não foi possível manter automaticamente a identificação anterior para: "
                                f"{texto_perdidas} — o composto escolhido não está mais entre os candidatos na "
                                "faixa de tolerância atual. Selecione novamente, se necessário."
                            )
                    except Exception as e: st.error(f"Erro: {e}")

            if 'resultado_calculo' in st.session_state:
                st.success("✅ Processamento concluído com sucesso!")

                df_qc = st.session_state.get('tabela_identificacao')
                if df_qc is not None and 'RSD_TR_%' in df_qc.columns:
                    picos_rsd_alto = df_qc[df_qc['RSD_TR_%'] > 5.0]['Pico'].tolist()
                    if picos_rsd_alto:
                        st.warning(
                            f"⚠️ **Controle de Qualidade (Amostra):** RSD do tempo de retenção acima de 5% nos picos "
                            f"{picos_rsd_alto} — precisão das réplicas fora do critério usual para CG. "
                            "Considere repetir as injeções desses picos antes de validar o resultado."
                        )

                df_qc_alc = st.session_state.get('alcanos_stats')
                if df_qc_alc is not None and 'RSD_Alcano_%' in df_qc_alc.columns:
                    alcanos_rsd_alto = df_qc_alc[df_qc_alc['RSD_Alcano_%'] > 5.0]['Carbonos'].tolist()
                    if alcanos_rsd_alto:
                        st.warning(
                            f"⚠️ **Controle de Qualidade (Alcanos):** RSD do TR acima de 5% no(s) alcano(s) com "
                            f"C{alcanos_rsd_alto} — considere repetir essas injeções da série homóloga antes de "
                            "validar o IRL calculado."
                        )

                st.divider()
                st.subheader("🎯 Tabela Interativa de Identificação dos Compostos")
                st.info(
                    "💡 Clique na caixa de seleção de cada pico para ver os compostos candidatos do Adams "
                    "(cada um já mostrando o seu IRL de literatura) e escolha o composto correto. O IRL de "
                    "literatura e a Classe Química da linha são preenchidos automaticamente com a sua escolha."
                )

                opcoes_por_pico = st.session_state.get('opcoes_identificacao', {})
                df_atual = st.session_state['tabela_identificacao']

                larguras_grade = [0.6, 1.1, 0.9, 1.3, 1.0, 2.6, 1.3]
                cabecalho = st.columns(larguras_grade)
                for c, titulo in zip(cabecalho, ["Pico", "TR médio (RSD%)", "IRL Calc.", "Área % (RSD%)", "IRL Lit.", "Composto (Adams) 🔽", "Classe Química"]):
                    c.markdown(f"**{titulo}**")

                opcao_vazia = {"label": "— selecione —", "composto": "", "irl_lit": None, "classe": ""}
                for idx, row in df_atual.iterrows():
                    pico = row['Pico']
                    candidatos = opcoes_por_pico.get(pico, [opcao_vazia])
                    labels = [c['label'] for c in candidatos]
                    composto_atual = str(row.get('Identificacao_Final', "") or "")

                    idx_atual = 0
                    for i_c, c in enumerate(candidatos):
                        if c['composto'] == composto_atual:
                            idx_atual = i_c
                            break

                    linha = st.columns(larguras_grade)
                    linha[0].write(f"**{pico}**")
                    linha[1].write(f"{row['TR_Medio']} ({row['RSD_TR_%']}%)")
                    linha[2].write(f"{row['IRL_Calculado']}")
                    linha[3].write(f"{row['Area_Relativa_%']}% ({row['RSD_Area_%']}%)")

                    escolha_label = linha[5].selectbox(
                        f"Composto — Pico {pico}", options=labels, index=idx_atual,
                        key=f"pico_{pico}", label_visibility="collapsed",
                    )
                    candidato_escolhido = candidatos[labels.index(escolha_label)]

                    st.session_state['tabela_identificacao'].at[idx, 'Identificacao_Final'] = candidato_escolhido['composto']
                    st.session_state['tabela_identificacao'].at[idx, 'Classe_Quimica'] = candidato_escolhido['classe']
                    if candidato_escolhido['irl_lit'] is not None:
                        st.session_state['tabela_identificacao'].at[idx, 'IRL_Literatura'] = f"{candidato_escolhido['irl_lit']:.0f}"
                    elif candidato_escolhido['composto'] != "":
                        # Opções sem IRL de literatura próprio (ex.: "Outro/Não Identificado").
                        st.session_state['tabela_identificacao'].at[idx, 'IRL_Literatura'] = ""
                    # Se nenhuma escolha foi feita ainda (composto == ""), mantém a lista de IRLs
                    # candidatos calculada no processamento, como referência para o usuário decidir.

                    linha[4].write(str(st.session_state['tabela_identificacao'].at[idx, 'IRL_Literatura']) or "—")
                    linha[6].write(candidato_escolhido['classe'] or "—")

                st.divider()
                st.subheader("📋 Tabela Final de Resultados (Resumo para Exportação)")
                st.dataframe(st.session_state['tabela_identificacao'], use_container_width=True, hide_index=True)

                st.download_button(
                    "🟢 Baixar Tabela Pronta em Excel",
                    data=utils.exportar_excel_bytes(st.session_state['tabela_identificacao'], sheet_name='Identificacao_DeBio'),
                    file_name="Tabela_Final_Identificacao.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                )

                st.divider()
                st.subheader("💾 Salvar para Comparação")
                col_s1, col_s2 = st.columns([3, 1])
                with col_s1: nome_salvar = st.text_input("Dê um nome para esta Amostra (Ex: Óleo de Folha Seca):")
                with col_s2:
                    st.write("")
                    st.write("")
                    if st.button("Salvar no Carrinho", use_container_width=True):
                        if nome_salvar:
                            st.session_state['amostras_salvas'][nome_salvar] = st.session_state['tabela_identificacao'].copy()
                            st.success(f"Amostra '{nome_salvar}' salva! Ela também já aparece disponível no módulo 📄 Laudos e Relatórios.")
                        else: st.warning("Digite um nome.")

    # =========================================
    # MÓDULO 3: COMPARATIVO DE AMOSTRAS
    # =========================================
    elif ferramenta_escolhida == "Comparativo de Amostras":
        st.title("⚖️ Comparativo de Perfis Cromatográficos")
        st.write("Gere e faça download de gráficos de alta qualidade comparando as amostras de óleos essenciais.")

        df_comp_vazio = pd.DataFrame(columns=['Composto', 'Classe_Quimica', 'Amostra A', 'Amostra B'])

        amostras_salvas = st.session_state.get('amostras_salvas', {})
        if len(amostras_salvas) > 0:
            st.success(f"✅ Encontramos {len(amostras_salvas)} amostra(s) salva(s) no carrinho!")
            df_final_cruzado = pd.DataFrame()
            for nome_am, df_am in amostras_salvas.items():
                df_temp = df_am[['Identificacao_Final', 'Classe_Quimica', 'Area_Relativa_%']].copy()
                df_temp = df_temp[df_temp['Identificacao_Final'] != ""]
                df_temp = df_temp.rename(columns={'Area_Relativa_%': nome_am, 'Identificacao_Final': 'Composto'})

                if df_final_cruzado.empty: df_final_cruzado = df_temp
                else: df_final_cruzado = pd.merge(df_final_cruzado, df_temp, on=['Composto', 'Classe_Quimica'], how='outer')

            df_comp_vazio = df_final_cruzado.fillna(0.0)
        else:
            st.info("💡 Você pode colar ou preencher sua matriz diretamente abaixo caso não tenha salvos na aba anterior:")

        st.divider()
        st.subheader("📊 Matriz de Dados (Visualização e Edição)")
        tabela_comp = st.data_editor(df_comp_vazio, num_rows="dynamic", use_container_width=True, key="editor_comp")
        df_comp_limpo = tabela_comp.dropna(subset=['Composto']).copy()

        if st.button("🚀 Gerar Dashboard de Gráficos", use_container_width=True):
            if not df_comp_limpo.empty:
                try:
                    colunas_dados = [c for c in df_comp_limpo.columns if c not in ['Composto', 'Classe_Quimica']]
                    for col in colunas_dados:
                        df_comp_limpo[col] = utils.parse_numero_br(df_comp_limpo[col]).fillna(0.0)

                    compostos = df_comp_limpo['Composto'].values
                    num_amostras = len(colunas_dados)

                    st.divider()
                    st.subheader("📊 1. Gráfico de Barras Agrupadas (Majoritários > 1%)")
                    df_major = df_comp_limpo[df_comp_limpo[colunas_dados].max(axis=1) > 1.0].copy()
                    comp_major = df_major['Composto'].values
                    x = np.arange(len(comp_major))
                    width = 0.8 / num_amostras

                    fig1, ax1 = plt.subplots(figsize=(10, 5))
                    for i, nome_am in enumerate(colunas_dados):
                        ax1.bar(x + i*width, df_major[nome_am].values, width, label=nome_am)
                    ax1.set_ylabel('Área Relativa (%)')
                    ax1.set_xticks(x + (width * (num_amostras - 1) / 2))
                    ax1.set_xticklabels(comp_major, rotation=45, ha='right')
                    ax1.legend()
                    ax1.grid(True, linestyle=':', alpha=0.5)
                    plt.tight_layout()
                    st.pyplot(fig1)

                    buf1 = io.BytesIO()
                    fig1.savefig(buf1, format="png", dpi=300)
                    st.download_button("💾 Baixar Gráfico de Barras (PNG)", data=buf1.getvalue(), file_name="grafico_barras_debio.png", mime="image/png")

                    st.divider()
                    st.subheader("🔥 2. Mapa de Calor (Heatmap Químico)")
                    fig2, ax2 = plt.subplots(figsize=(8, max(4, len(compostos)*0.3)))
                    matriz_valores = df_comp_limpo[colunas_dados].values
                    cax = ax2.imshow(matriz_valores, cmap='YlOrRd', aspect='auto')
                    ax2.set_xticks(np.arange(len(colunas_dados)))
                    ax2.set_yticks(np.arange(len(compostos)))
                    ax2.set_xticklabels(colunas_dados, rotation=45, ha='right')
                    ax2.set_yticklabels(compostos)

                    for i in range(len(compostos)):
                        for j in range(len(colunas_dados)):
                            valor = matriz_valores[i, j]
                            if valor > 0: ax2.text(j, i, f'{valor:.1f}', ha="center", va="center", color="black" if valor < np.max(matriz_valores)*0.6 else "white", fontsize=8)
                    fig2.colorbar(cax, ax=ax2, label='Área Relativa (%)')
                    plt.tight_layout()
                    st.pyplot(fig2)

                    buf2 = io.BytesIO()
                    fig2.savefig(buf2, format="png", dpi=300)
                    st.download_button("💾 Baixar Mapa de Calor (PNG)", data=buf2.getvalue(), file_name="heatmap_debio.png", mime="image/png")

                    if 'Classe_Quimica' in df_comp_limpo.columns:
                        st.divider()
                        st.subheader("🧬 3. Composição por Classe Química")
                        df_classes = df_comp_limpo.groupby('Classe_Quimica')[colunas_dados].sum()
                        fig3, ax3 = plt.subplots(figsize=(8, 6))
                        bottom = np.zeros(num_amostras)
                        for classe in df_classes.index:
                            valores_classe = df_classes.loc[classe].values
                            ax3.bar(colunas_dados, valores_classe, label=classe, bottom=bottom)
                            bottom += valores_classe
                        ax3.set_ylabel('Soma da Área Relativa (%)')
                        ax3.legend(title="Classes Químicas", bbox_to_anchor=(1.05, 1), loc='upper left')
                        plt.tight_layout()
                        st.pyplot(fig3)

                        buf3 = io.BytesIO()
                        fig3.savefig(buf3, format="png", dpi=300)
                        st.download_button("💾 Baixar Gráfico de Classes Químicas (PNG)", data=buf3.getvalue(), file_name="classes_quimicas_debio.png", mime="image/png")

                    st.divider()
                    st.subheader("📈 4. Gráfico de Tendência (Trend Plot)")
                    fig4, ax4 = plt.subplots(figsize=(10, 5))
                    for idx, row in df_major.iterrows():
                        ax4.plot(colunas_dados, row[colunas_dados].values, marker='o', label=row['Composto'])
                    ax4.set_ylabel('Área Relativa (%)')
                    ax4.grid(True, linestyle=':', alpha=0.5)
                    ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
                    plt.tight_layout()
                    st.pyplot(fig4)

                    buf4 = io.BytesIO()
                    fig4.savefig(buf4, format="png", dpi=300)
                    st.download_button("💾 Baixar Gráfico de Tendência (PNG)", data=buf4.getvalue(), file_name="tendencia_debio.png", mime="image/png")

                except Exception as e: st.error(f"Erro ao gerar gráficos: {e}")
