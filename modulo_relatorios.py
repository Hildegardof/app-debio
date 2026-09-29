"""
modulo_relatorios.py
---------------------
Módulo novo: consolida os resultados calculados nos demais módulos
(Óleos Essenciais, Ensaios Antioxidantes, Ferramentas) em um laudo técnico
único, exportado em Word (.docx), pronto para arquivar ou anexar a um
processo/relatório do laboratório.

Fontes de dados (todas em st.session_state, preenchidas pelos outros módulos):
- 'amostras_salvas'  -> dict {nome_amostra: DataFrame} salvo em
  modulo_oleos.py (botão "Salvar no Carrinho" da aba Índice Aritmético).
- 'laudo_dados'       -> lista de resultados registrados via
  modulo_utils.registrar_resultado(), usada por modulo_antioxidantes.py e
  modulo_ferramentas.py (botões "Salvar no laudo").

Este módulo só lê esses dados — nunca recalcula nada — para manter uma única
fonte de verdade para cada resultado analítico.
"""

import io
from datetime import datetime

import pandas as pd
import streamlit as st

import modulo_utils as utils


def _adicionar_tabela_dataframe(doc, df: pd.DataFrame):
    """Insere um DataFrame como tabela formatada em um documento python-docx."""
    colunas = list(df.columns)
    tabela = doc.add_table(rows=1, cols=len(colunas))
    try:
        tabela.style = 'Light Grid Accent 1'
    except KeyError:
        pass  # template sem esse estilo -> mantém o padrão

    hdr_cells = tabela.rows[0].cells
    for i, col in enumerate(colunas):
        hdr_cells[i].text = str(col)
        for p in hdr_cells[i].paragraphs:
            for run in p.runs:
                run.bold = True

    for _, row in df.iterrows():
        cells = tabela.add_row().cells
        for i, col in enumerate(colunas):
            valor = row[col]
            cells[i].text = "" if pd.isna(valor) else str(valor)
    return tabela


def renderizar_relatorios():
    st.title("📄 Laudos e Relatórios Técnicos")
    st.write("Consolide os resultados já calculados nos demais módulos em um laudo técnico único, para download em Word (.docx).")

    amostras_oleos = st.session_state.get('amostras_salvas', {})
    resultados_gerais = utils.listar_resultados_laudo()

    if not amostras_oleos and not resultados_gerais:
        st.info(
            "💡 Nenhum resultado disponível ainda. Calcule uma análise e clique em "
            "**'Salvar no Carrinho'** (módulo Óleos Essenciais → Índice Aritmético) ou "
            "**'Salvar no laudo'** (módulos Antioxidantes / Ferramentas) para trazer os "
            "dados até aqui."
        )
        return

    st.divider()
    st.subheader("⚙️ Identificação do Laudo")
    col1, col2 = st.columns(2)
    with col1:
        titulo_laudo = st.text_input("Título do Laudo:", value="Laudo Técnico de Análise")
        responsavel = st.text_input("Responsável Técnico:", value="")
    with col2:
        instituicao = st.text_input("Instituição:", value="DeBio - IFES")
        data_laudo = st.date_input("Data:", value=datetime.now())
    observacoes = st.text_area("Observações Gerais (opcional):", height=80)

    st.divider()
    st.subheader("📦 Amostras de Óleos Essenciais Disponíveis")
    amostras_selecionadas = []
    if amostras_oleos:
        amostras_selecionadas = st.multiselect(
            "Selecione as amostras de óleos essenciais a incluir:",
            options=list(amostras_oleos.keys()),
            default=list(amostras_oleos.keys()),
        )
    else:
        st.caption("Nenhuma amostra de óleo essencial salva no carrinho ainda.")

    st.subheader("🧪 Outros Resultados Disponíveis (Antioxidantes / Curvas de Calibração)")
    resultados_selecionados = []
    if resultados_gerais:
        opcoes_resultados = [f"{i}: {r['tipo']} — {r['nome']}" for i, r in enumerate(resultados_gerais)]
        escolha = st.multiselect(
            "Selecione os resultados a incluir:",
            options=opcoes_resultados,
            default=opcoes_resultados,
        )
        indices_escolhidos = [int(e.split(":")[0]) for e in escolha]
        resultados_selecionados = [resultados_gerais[i] for i in indices_escolhidos]

        if st.button("🗑️ Limpar todos os resultados salvos deste tipo"):
            st.session_state['laudo_dados'] = []
            st.rerun()
    else:
        st.caption("Nenhum resultado de antioxidantes/curvas de calibração salvo ainda.")

    st.divider()

    if st.button("🚀 Gerar Laudo Técnico (.docx)", use_container_width=True, type="primary"):
        if not amostras_selecionadas and not resultados_selecionados:
            st.warning("⚠️ Selecione pelo menos um item para incluir no laudo.")
        else:
            try:
                from docx import Document
                from docx.enum.text import WD_ALIGN_PARAGRAPH

                doc = Document()

                titulo = doc.add_heading(titulo_laudo, level=0)
                titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER

                p = doc.add_paragraph()
                p.add_run("Instituição: ").bold = True
                p.add_run(f"{instituicao}\n")
                p.add_run("Responsável Técnico: ").bold = True
                p.add_run(f"{responsavel or '—'}\n")
                p.add_run("Data: ").bold = True
                p.add_run(f"{data_laudo.strftime('%d/%m/%Y')}")

                if observacoes:
                    doc.add_heading("Observações Gerais", level=1)
                    doc.add_paragraph(observacoes)

                if amostras_selecionadas:
                    doc.add_heading("1. Óleos Essenciais — Identificação Cromatográfica (IRL/Kovats)", level=1)
                    for nome_am in amostras_selecionadas:
                        df_am = amostras_oleos[nome_am]
                        doc.add_heading(nome_am, level=2)
                        colunas_preferidas = [
                            'Pico', 'TR_Medio', 'RSD_TR_%', 'IRL_Calculado', 'IRL_Literatura',
                            'Identificacao_Final', 'Classe_Quimica',
                            'Area_Relativa_%', 'RSD_Area_%',
                        ]
                        colunas_relatorio = [c for c in colunas_preferidas if c in df_am.columns]
                        if not colunas_relatorio:
                            colunas_relatorio = list(df_am.columns)
                        _adicionar_tabela_dataframe(doc, df_am[colunas_relatorio])
                        doc.add_paragraph("")

                if resultados_selecionados:
                    doc.add_heading("2. Outras Análises (Antioxidantes / Curvas de Calibração)", level=1)
                    linhas = [
                        {"Tipo": r['tipo'], "Amostra": r['nome'], **r['dados']}
                        for r in resultados_selecionados
                    ]
                    df_outros = pd.DataFrame(linhas)
                    _adicionar_tabela_dataframe(doc, df_outros)

                doc.add_paragraph("")
                rodape = doc.add_paragraph()
                rodape.add_run(
                    f"Laudo gerado automaticamente pelo App DeBio em {datetime.now().strftime('%d/%m/%Y %H:%M')}."
                ).italic = True

                buffer = io.BytesIO()
                doc.save(buffer)

                st.success("✅ Laudo gerado com sucesso!")
                st.download_button(
                    "🟢 Baixar Laudo Técnico (.docx)",
                    data=buffer.getvalue(),
                    file_name=f"Laudo_DeBio_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                )
            except ImportError:
                st.error(
                    "🚫 A biblioteca **python-docx** não está instalada neste ambiente. "
                    "Rode `pip install -r requirements.txt` (já inclui `python-docx`) e recarregue o app."
                )
            except Exception as e:
                st.error(f"🚫 Erro ao gerar o laudo: {e}")
