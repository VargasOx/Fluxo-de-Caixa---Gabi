import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from datetime import date
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =========================
# LOGIN
# =========================

USUARIOS = st.secrets["USUARIOS"]

def login():

    st.title("🔐 Login")

    usuario = st.text_input("Usuário")

    senha = st.text_input(
        "Senha",
        type="password"
    )

    if st.button("Entrar"):

        if (
            usuario in USUARIOS
            and
            USUARIOS[usuario] == senha
        ):

            st.session_state["logado"] = True

            st.session_state["usuario"] = usuario

            st.rerun()

        else:

            st.error("Usuário ou senha inválidos")


def logout():

    st.session_state["logado"] = False

    st.rerun()

# =========================
# CONTROLE DE ACESSO
# =========================
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    login()
    st.stop()


st.set_page_config(layout="wide")

# =========================
# CONFIG
# =========================

SHEET_ID = "1Bn2NS9zIkpnJMe34gWIiQYPJoPWYU-9pSzooqf0-kys"
URL_PAGAR = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=pagar"
URL_RECEBER = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=receber"
# =========================
# LOAD DATA
# =========================

def tratar_valor(col):
    return pd.to_numeric(
        col.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )



@st.cache_data
def load_data():
    pagar = pd.read_csv(URL_PAGAR)
    receber = pd.read_csv(URL_RECEBER)
    

    for df in [pagar, receber]:
        # Converter datas
        for col in df.columns:
            if "Data" in col:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # 💰 Converter valor (ESSENCIAL)
        df["Valor"] = tratar_valor(df["Valor"])
    
    return pagar, receber

pagar, receber = load_data()

# =========================
# SIDEBAR
# =========================

st.sidebar.write(f"👤 Usuário: {st.session_state['usuario']}")

if st.sidebar.button("🚪 Sair"):
    logout()



st.sidebar.title("📊 Dashboard Financeiro")

pagina = st.sidebar.radio(
    "Escolha a visão:",
    ["Contas a Pagar", "Contas a Receber", "Fluxo de Caixa"]
)


# Lista de anos disponíveis
anos = sorted(
    pagar["Data Vencimento"].dt.year.dropna().unique()
)

ano_selecionado = st.sidebar.selectbox(
    "📅 Ano",
    anos,
    index=len(anos)-1
)

# Dicionário de meses
meses = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro"
}

# Opção Todos
meses_selecionados = st.sidebar.multiselect(
    "📆 Mês",
    options=list(meses.keys()),
    default=list(meses.keys()),
    format_func=lambda x: meses[x]
)

# =========================
# FILTROS
# =========================
def filtrar(df, coluna_data):

    filtro = (
        df[coluna_data].dt.year.isin([ano_selecionado])
    )

    # filtro de meses selecionados
    filtro &= (
        df[coluna_data].dt.month.isin(meses_selecionados)
    )

    return df[filtro]

# =========================
# CONTAS A PAGAR
# =========================
if pagina == "Contas a Pagar":

    st.title("💸 Contas a Pagar")

    df = filtrar(pagar, "Data Vencimento")

    total_pago = df[df["Status"] == "Pago"]["Valor"].sum() 
    total_pendente = df[df["Status"] == "Aberto"]["Valor"].sum() 

    df["Atrasado"] = (df["Data Vencimento"] < pd.Timestamp.now().normalize()) & (df["Status"] == "Aberto")
    total_atrasado = df[df["Atrasado"]]["Valor"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("💸 Pago", f"R$ {total_pago:,.2f}")
    col2.metric("⏳ Pendente", f"R$ {total_pendente:,.2f}")
    col3.metric("⚠️ Atrasado", f"R$ {total_atrasado:,.2f}")

    # 🔥 Separador visual
    st.divider()
    st.markdown("### 📊 Análises")

    # Gráfico categoria
    fig = px.pie(
        df,
        names="Categoria",
        values="Valor",
        title="Por Categoria",
        hole=0.5
    )

    fig.update_layout(
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )
    
    fig.update_traces(
        textfont_size=16,
        textinfo='percent+label'
    )

    # Evolução mensal
    df["Mes"] = df["Data Vencimento"].dt.month_name(locale='pt_BR')

    evolucao = df.groupby("Mes")["Valor"].sum().reset_index()

    fig2 = px.bar(
        evolucao,
        x="Mes",
        y="Valor",
        title="Evolução Mensal",
        text_auto=True
    )
    
    # Rótulos acima das barras
    fig2.update_traces(
        texttemplate='R$ %{y:,.2f}',
        textposition='outside',
        textfont_size=20
    )

    # Configurações adicionais para melhorar visualização
    fig2.update_layout(

        xaxis_title="",
        yaxis_title="Valor",

        uniformtext_minsize=15,
        uniformtext_mode='hide',

        xaxis=dict(
            tickfont=dict(size=16)
        )
    )



    # 🔥 GRÁFICOS LADO A LADO
    col_graf1, col_graf2 = st.columns([1, 2])

    with col_graf1:

        with st.container(border=True):
            st.plotly_chart(fig, use_container_width=True)

    with col_graf2:

        with st.container(border=True):
            st.plotly_chart(fig2, use_container_width=True)


    # =========================
# PRÓXIMOS VENCIMENTOS
# =========================

    hoje = pd.Timestamp.now().normalize()
    limite = hoje + pd.Timedelta(days=5)

    proximos_vencimentos = df.loc[
        (df["Status"] == "Aberto") &
        (df["Data Vencimento"] <= limite)
    ].copy()

# Data atual
    hoje = pd.Timestamp.now().normalize()

# Criar situação
    proximos_vencimentos["Situação"] = np.where(
        proximos_vencimentos["Data Vencimento"] < hoje,
        "🔴 Vencido",
        np.where(
            proximos_vencimentos["Data Vencimento"] == hoje,
            "🟡 Vence Hoje",
            "🟢 A Vencer"
        )
    )

# Ordenar por vencimento
    proximos_vencimentos = proximos_vencimentos.sort_values(
        "Data Vencimento"
    )

    st.divider()

    st.markdown("## ⏰ Contas a Pagar - Próximos 5 dias")

   # =========================
# FORMATAR TABELA
# =========================

    tabela = proximos_vencimentos[
        [
            "Situação",
            "Data Vencimento",
            "Fornecedor",
            "Categoria",
            "Valor"
        ]
    ].copy()

# Data BR
    tabela["Data Vencimento"] = pd.to_datetime(
        tabela["Data Vencimento"]
    ).dt.strftime("%d/%m/%Y")

# Moeda BR
    tabela["Valor"] = tabela["Valor"].apply(
        lambda x: f"R$ {x:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

# Estilo da tabela
    tabela = tabela.style.hide(axis="index").set_properties(**{
        'text-align': 'center'
    }).set_table_styles([
        {
            'selector': 'th',
            'props': [
                ('font-size', '20px'),
                ('font-weight', 'bold'),
                ('text-align', 'center'),
                ('background-color', '#262730'),
                ('color', 'white'),
                ('padding', '12px')
            ]
        },
        {
            'selector': 'td',
            'props': [
                ('font-size', '16px'),
                ('text-align', 'center'),
                ('padding', '10px')
            ]
        }

    ])

# Renderizar tabela
    st.table(tabela)


# =========================
# CONTAS A RECEBER
# =========================
elif pagina == "Contas a Receber":

    st.title("📥 Contas a Receber")

    df = filtrar(receber, "Data Vencimento")

    total_recebido = df[df["Status"] == "Pago"]["Valor"].sum()
    total_receber = df[df["Status"] == "Aberto"]["Valor"].sum()

    df["Atrasado"] = (df["Data Vencimento"] < pd.Timestamp.now().normalize()) & (df["Status"] == "Aberto")
    total_atrasado = df[df["Atrasado"]]["Valor"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Recebido", f"R$ {total_recebido:,.2f}")
    col2.metric("📥 A Receber", f"R$ {total_receber:,.2f}")
    col3.metric("⚠️ Inadimplência", f"R$ {total_atrasado:,.2f}")

    # 🔥 Separador visual
    st.divider()
    st.markdown("### 📊 Análises")

    # Gráfico categoria
    fig = px.pie(
        df,
        names="Categoria",
        values="Valor",
        title="Por Categoria",
        hole=0.5
    )

    fig.update_layout(
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )
    
    fig.update_traces(
        textfont_size=16,
        textinfo='percent+label'
    )

    # Evolução mensal
    df["Mes"] = df["Data Vencimento"].dt.month_name(locale='pt_BR')

    evolucao = df.groupby("Mes")["Valor"].sum().reset_index()

    fig2 = px.bar(
        evolucao,
        x="Mes",
        y="Valor",
        title="Evolução Mensal",
        text_auto=True
    )
    
    # Rótulos acima das barras
    fig2.update_traces(
        texttemplate='R$ %{y:,.2f}',
        textposition='outside',
        textfont_size=20
    )

    # Configurações adicionais para melhorar visualização
    fig2.update_layout(

        xaxis_title="",
        yaxis_title="Valor",

        uniformtext_minsize=15,
        uniformtext_mode='hide',

        xaxis=dict(
            tickfont=dict(size=16)
        )
    )



    # 🔥 GRÁFICOS LADO A LADO
    col_graf1, col_graf2 = st.columns([1, 2])

    with col_graf1:

        with st.container(border=True):
            st.plotly_chart(fig, use_container_width=True)

    with col_graf2:

        with st.container(border=True):
            st.plotly_chart(fig2, use_container_width=True)


    # =========================
# PRÓXIMOS RECEBIMENTOS
# =========================

    st.divider()

    st.markdown("## 💰 Contas a Receber - Próximos 5 dias")

# Data atual
    hoje = pd.Timestamp.now().normalize()

# Limite +5 dias
    limite = hoje + pd.Timedelta(days=5)

# Filtrar títulos
    proximos_recebimentos = df.loc[
        (df["Status"] == "Aberto") &
        (df["Data Vencimento"] <= limite)
    ].copy()

# Criar situação
    proximos_recebimentos["Situação"] = np.where(
        proximos_recebimentos["Data Vencimento"] < hoje,
        "🔴 Vencido",
        np.where(
            proximos_recebimentos["Data Vencimento"] == hoje,
            "🟡 Vence Hoje",
            "🟢 A Vencer"
        )
    )


# Ordenar por vencimento
    proximos_recebimentos = proximos_recebimentos.sort_values(
        "Data Vencimento"
    )

# =========================
# FORMATAR TABELA
# =========================

    tabela = proximos_recebimentos[
        [
            "Situação",
            "Data Vencimento",
            "Cliente",
            "Categoria",
            "Valor"
        ]
    ].copy()

# Data BR
    tabela["Data Vencimento"] = pd.to_datetime(
        tabela["Data Vencimento"]
    ).dt.strftime("%d/%m/%Y")

# Moeda BR
    tabela["Valor"] = tabela["Valor"].apply(
        lambda x: f"R$ {x:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

# Estilo
    tabela = tabela.style.hide(axis="index").set_properties(**{
        'text-align': 'center'
    }).set_table_styles([
        {
            'selector': 'th',
            'props': [
                ('font-size', '20px'),
                ('font-weight', 'bold'),
                ('text-align', 'center'),
                ('background-color', '#262730'),
                ('color', 'white'),
                ('padding', '12px')
            ]
        },
        {
            'selector': 'td',
            'props': [
                ('font-size', '16px'),
                ('text-align', 'center'),
                ('padding', '10px')
            ]
        }
       
    ])

# Renderizar tabela
    st.table(tabela)

# =========================
# FLUXO DE CAIXA
# =========================
elif pagina == "Fluxo de Caixa":

    st.title("📈 Fluxo de Caixa")

    # =========================
    # PREPARAR PAGAMENTOS
    # =========================

    pagar_fluxo = pagar.copy()

    pagar_fluxo = pagar_fluxo.rename(columns={
        "Data Pagamento": "Data"
    })

    pagar_fluxo["Tipo"] = "Saída"

    # Saídas negativas
    pagar_fluxo["Valor Fluxo"] = (
        pagar_fluxo["Valor"] * -1
    )

    # =========================
    # PREPARAR RECEBIMENTOS
    # =========================

    receber_fluxo = receber.copy()

    receber_fluxo = receber_fluxo.rename(columns={
        "Data Pagamento": "Data"
    })

    receber_fluxo["Tipo"] = "Entrada"

    receber_fluxo["Valor Fluxo"] = (
        receber_fluxo["Valor"]
    )

    # =========================
    # UNIR BASES
    # =========================

    fluxo = pd.concat([
        pagar_fluxo[
            ["Data", "Categoria", "Valor Fluxo", "Tipo"]
        ],

        receber_fluxo[
            ["Data", "Categoria", "Valor Fluxo", "Tipo"]
        ]
    ])

    # Garantir datetime
    fluxo["Data"] = pd.to_datetime(
        fluxo["Data"],
        dayfirst=True,
        errors="coerce"
    )

    # =========================
    # FILTROS
    # =========================

    fluxo = fluxo[
        fluxo["Data"].dt.year == ano_selecionado
    ]

    fluxo = fluxo[
        fluxo["Data"].dt.month.isin(meses_selecionados)
    ]

    # =========================
    # KPIs
    # =========================

    total_entrada = fluxo.loc[
        fluxo["Tipo"] == "Entrada",
        "Valor Fluxo"
    ].sum()

    total_saida = fluxo.loc[
        fluxo["Tipo"] == "Saída",
        "Valor Fluxo"
    ].sum()

    saldo = fluxo["Valor Fluxo"].sum()

    # KPIs no topo
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "💰 Entradas",
        f"R$ {total_entrada:,.2f}"
    )

    col2.metric(
        "💸 Saídas",
        f"R$ {abs(total_saida):,.2f}"
    )

    col3.metric(
        "📈 Saldo",
        f"R$ {saldo:,.2f}"
    )

    st.divider()

    # =========================
    # AGRUPAMENTO DIÁRIO
    # =========================

    fluxo_diario = fluxo.groupby(
        ["Data", "Tipo"]
    )["Valor Fluxo"].sum().reset_index()

    # Separar entradas e saídas
    entradas = fluxo_diario[
        fluxo_diario["Tipo"] == "Entrada"
    ]

    saidas = fluxo_diario[
        fluxo_diario["Tipo"] == "Saída"
    ]

    # Saldo acumulado
    saldo_diario = fluxo.groupby(
        "Data"
    )["Valor Fluxo"].sum().reset_index()

    saldo_diario = saldo_diario.sort_values(
        "Data"
    )

    saldo_diario["Saldo Acumulado"] = saldo_diario[
        "Valor Fluxo"
    ].cumsum()

    # =========================
    # GRÁFICO
    # =========================

    fig_fluxo = go.Figure()

    # Barras entradas
    fig_fluxo.add_trace(
        go.Bar(
            x=entradas["Data"],
            y=entradas["Valor Fluxo"],
            name="Entradas"
        )
    )

    # Barras saídas
    fig_fluxo.add_trace(
        go.Bar(
            x=saidas["Data"],
            y=saidas["Valor Fluxo"],
            name="Saídas"
        )
    )

    # Linha saldo acumulado
    fig_fluxo.add_trace(
        go.Scatter(
            x=saldo_diario["Data"],
            y=saldo_diario["Saldo Acumulado"],
            mode="lines+markers",
            name="Saldo Acumulado",
            yaxis="y2",
            line=dict(width=4)
        )
    )

    # Layout
    fig_fluxo.update_layout(

        title="Fluxo de Caixa",

        title_font_size=24,

        xaxis_title="",

        yaxis=dict(
            title="Entradas / Saídas",
            tickprefix="R$ "
        ),

        yaxis2=dict(
            title="Saldo Acumulado",
            overlaying="y",
            side="right",
            tickprefix="R$ "
        ),

        barmode="relative",

        height=600,

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Renderizar gráfico
    st.plotly_chart(
        fig_fluxo,
        use_container_width=True
    )