import streamlit as st
import modulo_oleos
import modulo_antioxidantes
import modulo_ferramentas
import modulo_relatorios

# Configuração global da página (sempre no arquivo principal)
st.set_page_config(page_title="App DeBio", layout="wide")

st.sidebar.title("🧪 App DeBio")
st.sidebar.write("Navegação:")

# Escolha da Categoria Mãe
categoria_mae = st.sidebar.selectbox(
    "Selecione o Módulo de Trabalho:",
    [
        "🌿 Óleos Essenciais",
        "🛡️ Ensaios Antioxidantes",
        "🔬 Outras Ferramentas Analíticas",
        "📄 Laudos e Relatórios",
    ]
)

st.sidebar.divider()

# Roteamento para os módulos
if categoria_mae == "🌿 Óleos Essenciais":
    modulo_oleos.renderizar_oleos()

elif categoria_mae == "🛡️ Ensaios Antioxidantes":
    modulo_antioxidantes.renderizar_antioxidantes()

elif categoria_mae == "🔬 Outras Ferramentas Analíticas":
    modulo_ferramentas.renderizar_ferramentas()

elif categoria_mae == "📄 Laudos e Relatórios":
    modulo_relatorios.renderizar_relatorios()

st.sidebar.divider()
st.sidebar.info("Desenvolvido para agilizar a rotina de bancada do DeBio - IFES.")
