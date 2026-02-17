"""
SISTEMA DE OFICINA - VERSÃO WEB COMPLETA COM AUTENTICAÇÃO
Desenvolvido para gestão completa de oficina mecânica
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import hashlib
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import os

# ================= CONFIGURAÇÃO DA PÁGINA =================

st.set_page_config(
    page_title="Sistema Oficina",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= VARIÁVEIS GLOBAIS =================

DB = "oficina.db"
LOGO_PATH = "logo.png"

MODELOS_POR_MARCA = {
    "FIAT": ["PALIO", "UNO", "STRADA", "ARGO", "TORO"],
    "FORD": ["KA", "FIESTA", "FOCUS", "ECOSPORT"],
    "VW": ["GOL", "POLO", "SAVEIRO", "T-CROSS"],
    "GM": ["CORSA", "CELTA", "ONIX", "PRISMA"],
    "TOYOTA": ["COROLLA", "ETIOS", "HILUX"],
    "HONDA": ["CIVIC", "FIT", "CITY", "HR-V"]
}

# ================= SISTEMA DE AUTENTICAÇÃO =================

def hash_password(password):
    """Cria hash da senha"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_usuarios():
    """Inicializa tabela de usuários"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            nome TEXT,
            nivel TEXT
        )
    """)
    
    # Criar usuário admin padrão se não existir
    c.execute("SELECT * FROM usuarios WHERE username='admin'")
    if not c.fetchone():
        senha_hash = hash_password("admin123")
        c.execute("""
            INSERT INTO usuarios (username, password, nome, nivel)
            VALUES ('admin', ?, 'Administrador', 'admin')
        """, (senha_hash,))
    
    conn.commit()
    conn.close()

def verificar_login(username, password):
    """Verifica credenciais do usuário"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    senha_hash = hash_password(password)
    c.execute("""
        SELECT id, nome, nivel FROM usuarios 
        WHERE username=? AND password=?
    """, (username, senha_hash))
    
    resultado = c.fetchone()
    conn.close()
    
    return resultado

def alterar_senha(user_id, senha_atual, nova_senha):
    """Altera a senha do usuário"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Verificar senha atual
    senha_hash_atual = hash_password(senha_atual)
    c.execute("SELECT id FROM usuarios WHERE id=? AND password=?",
              (user_id, senha_hash_atual))

    if not c.fetchone():
        conn.close()
        return False, "Senha atual incorreta!"

    # Atualizar para nova senha
    nova_hash = hash_password(nova_senha)
    c.execute("UPDATE usuarios SET password=? WHERE id=?",
              (nova_hash, user_id))
    conn.commit()
    conn.close()
    return True, "Senha alterada com sucesso!"

def tela_login():
    """Tela de login"""
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 2rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        
        st.title("🔧 Sistema Oficina")
        st.markdown("---")
        
        with st.form("login_form"):
            username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            password = st.text_input("🔒 Senha", type="password", placeholder="Digite sua senha")
            
            submit = st.form_submit_button("🚀 Entrar", use_container_width=True)
            
            if submit:
                if username and password:
                    resultado = verificar_login(username, password)
                    
                    if resultado:
                        st.session_state.logged_in = True
                        st.session_state.user_id = resultado[0]
                        st.session_state.user_nome = resultado[1]
                        st.session_state.user_nivel = resultado[2]
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos!")
                else:
                    st.warning("⚠️ Preencha todos os campos!")
        
        st.markdown("---")
        st.caption("💡 Usuário padrão: **admin** | Senha: **admin123**")
        st.caption("📝 Altere a senha após primeiro acesso!")

# ================= CSS CUSTOMIZADO =================

def load_css():
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #1a2634;
        }
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] small {
            color: #f0f4f8 !important;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: #2d3f53 !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            background-color: #c0392b !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: bold !important;
            width: 100%;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #a93226 !important;
        }
        .main { padding: 1rem; }
        h1 {
            color: #1f77b4;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #1f77b4;
            margin-bottom: 1.5rem;
        }
        h2 { color: #2c3e50; margin-top: 1.5rem; }
        .main .stButton > button {
            background-color: #1f77b4;
            color: white;
            border-radius: 6px;
            font-weight: bold;
            border: none;
        }
        .main .stButton > button:hover {
            background-color: #155a8a;
        }
        [data-testid="stMetric"] {
            background-color: #f7f9fc;
            border-radius: 10px;
            padding: 1rem;
            border: 1px solid #e2e8f0;
        }
    </style>
    """, unsafe_allow_html=True)

# ================= BANCO DE DADOS =================

def init_db():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            telefone TEXT,
            logradouro TEXT,
            numero TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS carros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            placa TEXT UNIQUE,
            marca TEXT,
            modelo TEXT,
            km INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS catalogo_servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            valor REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            carro_id INTEGER,
            data TEXT,
            status TEXT,
            total REAL,
            observacoes TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS itens_orcamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orcamento_id INTEGER,
            servico_id INTEGER,
            descricao TEXT,
            quantidade INTEGER,
            valor_unitario REAL,
            subtotal REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS servicos_realizados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orcamento_id INTEGER,
            cliente_id INTEGER,
            carro_id INTEGER,
            data TEXT,
            total REAL,
            observacoes TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS itens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            servico_id INTEGER,
            descricao TEXT,
            quantidade INTEGER,
            valor_unitario REAL,
            subtotal REAL
        )
    """)

    conn.commit()
    conn.close()

# ================= FUNÇÕES AUXILIARES =================

def formatar_moeda(valor):
    """Formata valor para moeda brasileira"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_telefone(telefone):
    """Formata telefone brasileiro"""
    if not telefone:
        return ""
    nums = "".join(filter(str.isdigit, telefone))
    if len(nums) == 11:
        return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"
    return telefone

def get_db_connection():
    """Retorna conexão com o banco"""
    return sqlite3.connect(DB)

# ================= FUNÇÕES DE DADOS =================

def get_clientes():
    """Retorna todos os clientes"""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM clientes ORDER BY nome", conn)
    conn.close()
    return df

def salvar_cliente(nome, telefone, logradouro, numero, cliente_id=None):
    """Salva ou atualiza cliente"""
    conn = get_db_connection()
    c = conn.cursor()
    
    if cliente_id:
        c.execute("""
            UPDATE clientes 
            SET nome=?, telefone=?, logradouro=?, numero=?
            WHERE id=?
        """, (nome, telefone, logradouro, numero, cliente_id))
    else:
        c.execute("""
            INSERT INTO clientes (nome, telefone, logradouro, numero)
            VALUES (?, ?, ?, ?)
        """, (nome, telefone, logradouro, numero))
    
    conn.commit()
    novo_id = c.lastrowid if not cliente_id else cliente_id
    conn.close()
    return novo_id

def get_carros_por_cliente(cliente_id):
    """Retorna carros de um cliente"""
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM carros WHERE cliente_id = ? ORDER BY placa",
        conn,
        params=(cliente_id,)
    )
    conn.close()
    return df

def salvar_carro(cliente_id, placa, marca, modelo, km, carro_id=None):
    """Salva ou atualiza carro"""
    conn = get_db_connection()
    c = conn.cursor()
    
    if carro_id:
        c.execute("""
            UPDATE carros
            SET placa=?, marca=?, modelo=?, km=?
            WHERE id=?
        """, (placa.upper(), marca, modelo, km, carro_id))
    else:
        c.execute("""
            INSERT INTO carros (cliente_id, placa, marca, modelo, km)
            VALUES (?, ?, ?, ?, ?)
        """, (cliente_id, placa.upper(), marca, modelo, km))
    
    conn.commit()
    novo_id = c.lastrowid if not carro_id else carro_id
    conn.close()
    return novo_id

def get_servicos():
    """Retorna todos os serviços do catálogo"""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM catalogo_servicos ORDER BY descricao", conn)
    conn.close()
    return df

def salvar_servico(descricao, valor, servico_id=None):
    """Salva ou atualiza serviço"""
    conn = get_db_connection()
    c = conn.cursor()
    
    if servico_id:
        c.execute("""
            UPDATE catalogo_servicos
            SET descricao=?, valor=?
            WHERE id=?
        """, (descricao.upper(), valor, servico_id))
    else:
        c.execute("""
            INSERT INTO catalogo_servicos (descricao, valor)
            VALUES (?, ?)
        """, (descricao.upper(), valor))
    
    conn.commit()
    novo_id = c.lastrowid if not servico_id else servico_id
    conn.close()
    return novo_id

def salvar_orcamento(cliente_id, carro_id, status, observacoes, itens):
    """Salva orçamento completo"""
    conn = get_db_connection()
    c = conn.cursor()
    
    data = datetime.now().strftime("%d/%m/%Y %H:%M")
    total = sum(item['subtotal'] for item in itens)
    
    c.execute("""
        INSERT INTO orcamentos (cliente_id, carro_id, data, status, total, observacoes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (cliente_id, carro_id, data, status, total, observacoes))
    
    orcamento_id = c.lastrowid
    
    for item in itens:
        c.execute("""
            INSERT INTO itens_orcamento 
            (orcamento_id, servico_id, descricao, quantidade, valor_unitario, subtotal)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (orcamento_id, item['servico_id'], item['descricao'], 
              item['quantidade'], item['valor_unitario'], item['subtotal']))
    
    # Se aprovado, criar serviço realizado
    if status == 'APROVADO':
        criar_servico_de_orcamento(c, orcamento_id, cliente_id, carro_id, data, total, observacoes, itens)
    
    conn.commit()
    conn.close()
    return orcamento_id

def criar_servico_de_orcamento(cursor, orc_id, cliente_id, carro_id, data, total, obs, itens):
    """Cria um serviço realizado a partir de um orçamento aprovado"""
    cursor.execute("""
        INSERT INTO servicos_realizados (orcamento_id, cliente_id, carro_id, data, total, observacoes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (orc_id, cliente_id, carro_id, data, total, obs))
    servico_id = cursor.lastrowid
    
    for item in itens:
        cursor.execute("""
            INSERT INTO itens_servico (servico_id, descricao, quantidade, valor_unitario, subtotal)
            VALUES (?, ?, ?, ?, ?)
        """, (servico_id, item['descricao'], item['quantidade'], item['valor_unitario'], item['subtotal']))

def get_orcamentos():
    """Retorna todos os orçamentos"""
    conn = get_db_connection()
    query = """
        SELECT o.id, c.nome, ca.placa, o.data, o.status, o.total
        FROM orcamentos o
        JOIN clientes c ON o.cliente_id = c.id
        JOIN carros ca ON o.carro_id = ca.id
        ORDER BY o.id DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_servicos_realizados(data_ini=None, data_fim=None):
    """Retorna serviços realizados com filtro opcional de data"""
    conn = get_db_connection()
    
    query = """
        SELECT s.id, c.nome, ca.placa, s.data, s.total
        FROM servicos_realizados s
        JOIN clientes c ON s.cliente_id = c.id
        JOIN carros ca ON s.carro_id = ca.id
    """
    
    params = []
    if data_ini and data_fim:
        query += " WHERE s.data BETWEEN ? AND ?"
        params = [data_ini, data_fim + " 23:59"]
    
    query += " ORDER BY s.id DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def gerar_pdf_orcamento(orcamento_id):
    """Gera PDF do orçamento"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Dados do orçamento
    c.execute("""
        SELECT o.id, c.nome, c.telefone, c.logradouro, c.numero,
               ca.placa, ca.marca, ca.modelo, ca.km,
               o.data, o.status, o.total, o.observacoes
        FROM orcamentos o
        JOIN clientes c ON o.cliente_id = c.id
        JOIN carros ca ON o.carro_id = ca.id
        WHERE o.id=?
    """, (orcamento_id,))
    orc = c.fetchone()
    
    # Itens
    c.execute("""
        SELECT descricao, quantidade, valor_unitario, subtotal
        FROM itens_orcamento WHERE orcamento_id=?
    """, (orcamento_id,))
    itens = c.fetchall()
    
    conn.close()
    
    # Criar PDF em memória
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()
    
    # Título
    style_titulo = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    titulo = Paragraph(f"ORÇAMENTO Nº {orc[0]:04d}", style_titulo)
    elementos.append(titulo)
    elementos.append(Spacer(1, 12))
    
    # Informações do cliente
    info_data = [
        ['Data:', orc[9], 'Status:', orc[10]],
        ['Cliente:', orc[1], '', ''],
        ['Telefone:', orc[2] or 'Não informado', '', ''],
        ['Endereço:', f"{orc[3] or ''} {orc[4] or ''}", '', ''],
        ['Veículo:', f"{orc[6]} {orc[7]}", 'Placa:', orc[5]],
        ['KM:', str(orc[8]), '', ''],
    ]
    
    info_table = Table(info_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1.5*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elementos.append(info_table)
    elementos.append(Spacer(1, 20))
    
    # Tabela de serviços
    servicos_data = [['Descrição', 'Qtd', 'Valor Unit.', 'Subtotal']]
    
    for item in itens:
        servicos_data.append([
            item[0],
            str(item[1]),
            f"R$ {item[2]:.2f}",
            f"R$ {item[3]:.2f}"
        ])
    
    servicos_table = Table(servicos_data, colWidths=[3.5*inch, 0.7*inch, 1.2*inch, 1.2*inch])
    servicos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elementos.append(servicos_table)
    elementos.append(Spacer(1, 12))
    
    # Total
    total_data = [['', '', 'TOTAL:', f"R$ {orc[11]:.2f}"]]
    total_table = Table(total_data, colWidths=[3.5*inch, 0.7*inch, 1.2*inch, 1.2*inch])
    total_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
    ]))
    elementos.append(total_table)
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# ================= INICIALIZAÇÃO =================

init_db()
init_usuarios()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'pagina' not in st.session_state:
    st.session_state.pagina = '🏠 Dashboard'
if 'itens_orcamento' not in st.session_state:
    st.session_state.itens_orcamento = []

# ================= VERIFICAR LOGIN =================

if not st.session_state.logged_in:
    tela_login()
    st.stop()

# ================= APLICAÇÃO PRINCIPAL =================

load_css()

# ================= SIDEBAR =================

with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.title("🔧 Oficina")
    
    st.markdown("---")
    st.write(f"👤 **{st.session_state.user_nome}**")
    
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    
    st.markdown("---")
    
    st.session_state.pagina = st.radio(
        "📋 Menu Principal",
        ["🏠 Dashboard", "👥 Clientes e Carros", "💰 Orçamentos",
         "📜 Histórico", "✅ Serviços Realizados", "📚 Catálogo",
         "🔑 Alterar Senha"]
    )
    
    st.markdown("---")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ================= PÁGINA: DASHBOARD =================

if st.session_state.pagina == "🏠 Dashboard":
    st.title("🏠 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    conn = get_db_connection()
    c = conn.cursor()
    
    total_clientes = c.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    total_carros = c.execute("SELECT COUNT(*) FROM carros").fetchone()[0]
    total_servicos_mes = c.execute("""
        SELECT COUNT(*) FROM servicos_realizados 
        WHERE strftime('%Y-%m', data) = strftime('%Y-%m', 'now')
    """).fetchone()[0]
    
    faturamento_mes = c.execute("""
        SELECT COALESCE(SUM(total), 0) FROM servicos_realizados 
        WHERE strftime('%Y-%m', data) = strftime('%Y-%m', 'now')
    """).fetchone()[0]
    
    conn.close()
    
    with col1:
        st.metric("👥 Clientes", total_clientes)
    
    with col2:
        st.metric("🚗 Veículos", total_carros)
    
    with col3:
        st.metric("✅ Serviços (mês)", total_servicos_mes)
    
    with col4:
        st.metric("💰 Faturamento (mês)", formatar_moeda(faturamento_mes))
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Orçamentos por Status")
        df_orcamentos = get_orcamentos()
        if len(df_orcamentos) > 0:
            status_counts = df_orcamentos['status'].value_counts()
            st.bar_chart(status_counts)
        else:
            st.info("Nenhum orçamento cadastrado ainda")
    
    with col2:
        st.subheader("📈 Últimos Serviços")
        df_servicos = get_servicos_realizados()
        if len(df_servicos) > 0:
            st.dataframe(
                df_servicos.head(5)[['nome', 'placa', 'data', 'total']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum serviço realizado")

# ================= PÁGINA: CLIENTES =================

elif st.session_state.pagina == "👥 Clientes e Carros":
    st.title("👥 Gestão de Clientes e Veículos")
    
    tab1, tab2 = st.tabs(["📋 Clientes", "🚗 Carros"])
    
    with tab1:
        st.subheader("Cadastro de Clientes")
        
        with st.form("form_cliente"):
            nome = st.text_input("Nome do Cliente*")
            
            col1, col2 = st.columns(2)
            with col1:
                telefone = st.text_input("Telefone", placeholder="(00) 00000-0000")
            with col2:
                logradouro = st.text_input("Logradouro")
            
            numero = st.text_input("Número")
            
            submitted = st.form_submit_button("💾 Salvar Cliente", use_container_width=True)
            
            if submitted:
                if nome:
                    salvar_cliente(nome.upper(), telefone, logradouro.upper(), numero)
                    st.success(f"✅ Cliente '{nome}' salvo!")
                    st.rerun()
                else:
                    st.error("⚠️ Nome é obrigatório!")
        
        st.markdown("---")
        st.subheader("📋 Clientes Cadastrados")
        
        df_clientes = get_clientes()
        if len(df_clientes) > 0:
            busca = st.text_input("🔍 Buscar", placeholder="Digite o nome...")
            if busca:
                df_clientes = df_clientes[df_clientes['nome'].str.contains(busca.upper(), na=False)]
            
            st.dataframe(df_clientes, use_container_width=True, hide_index=True)
        else:
            st.info("📭 Nenhum cliente cadastrado")
    
    with tab2:
        st.subheader("Cadastro de Veículos")
        
        df_clientes = get_clientes()
        if len(df_clientes) > 0:
            cliente_opcoes = {f"{row['id']} - {row['nome']}": row['id'] 
                            for _, row in df_clientes.iterrows()}
            
            cliente_sel = st.selectbox("Selecione o Cliente*", list(cliente_opcoes.keys()))
            cliente_id = cliente_opcoes[cliente_sel]
            
            with st.form("form_carro"):
                col1, col2 = st.columns(2)
                
                with col1:
                    placa = st.text_input("Placa*", placeholder="ABC1234")
                    marca = st.selectbox("Marca*", [""] + list(MODELOS_POR_MARCA.keys()))
                
                with col2:
                    modelos = MODELOS_POR_MARCA.get(marca, []) if marca else []
                    modelo = st.selectbox("Modelo*", [""] + modelos)
                    km = st.number_input("KM", min_value=0, step=1000)
                
                submitted = st.form_submit_button("💾 Salvar Veículo", use_container_width=True)
                
                if submitted and placa and marca and modelo:
                    try:
                        salvar_carro(cliente_id, placa, marca, modelo, km)
                        st.success(f"✅ Veículo {placa} salvo!")
                        st.rerun()
                    except:
                        st.error("❌ Placa já cadastrada!")
            
            st.markdown("---")
            st.subheader(f"🚗 Veículos")
            df_carros = get_carros_por_cliente(cliente_id)
            if len(df_carros) > 0:
                st.dataframe(df_carros, use_container_width=True, hide_index=True)
            else:
                st.info("📭 Nenhum veículo cadastrado")
        else:
            st.warning("⚠️ Cadastre um cliente primeiro!")

# ================= PÁGINA: ORÇAMENTOS =================

elif st.session_state.pagina == "💰 Orçamentos":
    st.title("💰 Novo Orçamento")
    
    df_clientes = get_clientes()
    df_servicos = get_servicos()
    
    if len(df_clientes) == 0:
        st.warning("⚠️ Cadastre clientes primeiro!")
        st.stop()
    
    if len(df_servicos) == 0:
        st.warning("⚠️ Cadastre serviços no catálogo primeiro!")
        st.stop()
    
    # Seleção de cliente e carro
    col1, col2 = st.columns(2)
    
    with col1:
        cliente_opcoes = {f"{row['id']} - {row['nome']}": row['id'] 
                        for _, row in df_clientes.iterrows()}
        cliente_sel = st.selectbox("1️⃣ Cliente*", list(cliente_opcoes.keys()))
        cliente_id = cliente_opcoes[cliente_sel]
    
    with col2:
        df_carros = get_carros_por_cliente(cliente_id)
        if len(df_carros) > 0:
            carro_opcoes = {f"{row['placa']} - {row['marca']} {row['modelo']}": row['id'] 
                          for _, row in df_carros.iterrows()}
            carro_sel = st.selectbox("2️⃣ Veículo*", list(carro_opcoes.keys()))
            carro_id = carro_opcoes[carro_sel]
        else:
            st.error("⚠️ Cliente não possui veículos cadastrados!")
            st.stop()
    
    st.markdown("---")
    st.subheader("3️⃣ Adicionar Serviços")
    
    # Adicionar item
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        servico_opcoes = {f"{row['id']} - {row['descricao']} - {formatar_moeda(row['valor'])}": 
                         (row['id'], row['descricao'], row['valor']) 
                         for _, row in df_servicos.iterrows()}
        servico_sel = st.selectbox("Serviço", list(servico_opcoes.keys()))
        servico_id, descricao, valor = servico_opcoes[servico_sel]
    
    with col2:
        quantidade = st.number_input("Qtd", min_value=1, value=1)
    
    with col3:
        valor_unit = st.number_input("Valor", value=float(valor), step=10.0)
    
    with col4:
        st.write("")
        st.write("")
        if st.button("➕ Adicionar", use_container_width=True):
            subtotal = quantidade * valor_unit
            st.session_state.itens_orcamento.append({
                'servico_id': servico_id,
                'descricao': descricao,
                'quantidade': quantidade,
                'valor_unitario': valor_unit,
                'subtotal': subtotal
            })
            st.rerun()
    
    # Mostrar itens
    if len(st.session_state.itens_orcamento) > 0:
        st.subheader("📋 Itens do Orçamento")
        
        itens_df = pd.DataFrame(st.session_state.itens_orcamento)
        itens_df['valor_formatado'] = itens_df['valor_unitario'].apply(formatar_moeda)
        itens_df['subtotal_formatado'] = itens_df['subtotal'].apply(formatar_moeda)
        
        st.dataframe(
            itens_df[['descricao', 'quantidade', 'valor_formatado', 'subtotal_formatado']],
            use_container_width=True,
            hide_index=True,
            column_config={
                'descricao': 'Descrição',
                'quantidade': 'Qtd',
                'valor_formatado': 'Valor Unit.',
                'subtotal_formatado': 'Subtotal'
            }
        )
        
        total = sum(item['subtotal'] for item in st.session_state.itens_orcamento)
        st.metric("💰 TOTAL", formatar_moeda(total))
        
        # Observações e Status
        col1, col2 = st.columns([3, 1])
        
        with col1:
            observacoes = st.text_area("Observações")
        
        with col2:
            status = st.selectbox("Status", ["PENDENTE", "APROVADO", "RECUSADO", "FINALIZADO"])
        
        # Botões
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Orçamento", use_container_width=True, type="primary"):
                orcamento_id = salvar_orcamento(
                    cliente_id, carro_id, status, observacoes,
                    st.session_state.itens_orcamento
                )
                st.success(f"✅ Orçamento #{orcamento_id} salvo com sucesso!")
                st.session_state.itens_orcamento = []
                st.rerun()
        
        with col2:
            if st.button("🗑️ Limpar Tudo", use_container_width=True):
                st.session_state.itens_orcamento = []
                st.rerun()
    else:
        st.info("➕ Adicione serviços ao orçamento")

# ================= PÁGINA: HISTÓRICO =================

elif st.session_state.pagina == "📜 Histórico":
    st.title("📜 Histórico de Orçamentos")
    
    df_orcamentos = get_orcamentos()
    
    if len(df_orcamentos) > 0:
        status_filtro = st.multiselect(
            "Filtrar por Status",
            options=df_orcamentos['status'].unique().tolist(),
            default=df_orcamentos['status'].unique().tolist()
        )
        
        df_filtrado = df_orcamentos[df_orcamentos['status'].isin(status_filtro)]
        
        # Adicionar botão de download PDF
        for idx, row in df_filtrado.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 3, 2, 2, 2, 2, 2])
            
            with col1:
                st.write(f"**#{row['id']}**")
            with col2:
                st.write(row['nome'])
            with col3:
                st.write(row['placa'])
            with col4:
                st.write(row['data'])
            with col5:
                st.write(row['status'])
            with col6:
                st.write(formatar_moeda(row['total']))
            with col7:
                if st.button("📄 PDF", key=f"pdf_{row['id']}"):
                    pdf_buffer = gerar_pdf_orcamento(row['id'])
                    st.download_button(
                        label="⬇️ Baixar",
                        data=pdf_buffer,
                        file_name=f"Orcamento_{row['id']:04d}.pdf",
                        mime="application/pdf",
                        key=f"download_{row['id']}"
                    )
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pendentes", len(df_filtrado[df_filtrado['status'] == 'PENDENTE']))
        with col2:
            st.metric("Aprovados", len(df_filtrado[df_filtrado['status'] == 'APROVADO']))
        with col3:
            st.metric("Total", formatar_moeda(df_filtrado['total'].sum()))
    else:
        st.info("📭 Nenhum orçamento cadastrado")

# ================= PÁGINA: SERVIÇOS REALIZADOS =================

elif st.session_state.pagina == "✅ Serviços Realizados":
    st.title("✅ Serviços Realizados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        data_ini = st.date_input("Data Inicial", value=datetime.now().replace(day=1))
    with col2:
        data_fim = st.date_input("Data Final", value=datetime.now())
    with col3:
        st.write("")
        st.write("")
        filtrar = st.button("🔍 Filtrar", use_container_width=True)
    
    data_ini_str = data_ini.strftime("%d/%m/%Y")
    data_fim_str = data_fim.strftime("%d/%m/%Y")
    
    df_servicos = get_servicos_realizados(data_ini_str, data_fim_str)
    
    if len(df_servicos) > 0:
        total_periodo = df_servicos['total'].sum()
        
        st.metric("💰 Total do Período", formatar_moeda(total_periodo), 
                 delta=f"{len(df_servicos)} serviço(s)")
        
        st.markdown("---")
        
        df_display = df_servicos.copy()
        df_display['total'] = df_display['total'].apply(formatar_moeda)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("📭 Nenhum serviço no período")

# ================= PÁGINA: CATÁLOGO =================

elif st.session_state.pagina == "📚 Catálogo":
    st.title("📚 Catálogo de Serviços")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Novo Serviço")
        
        with st.form("form_servico"):
            descricao = st.text_input("Descrição*")
            valor = st.number_input("Valor (R$)*", min_value=0.0, step=10.0, format="%.2f")
            
            submitted = st.form_submit_button("💾 Salvar", use_container_width=True)
            
            if submitted and descricao and valor > 0:
                salvar_servico(descricao, valor)
                st.success("✅ Serviço salvo!")
                st.rerun()
    
    with col2:
        st.subheader("Serviços Cadastrados")
        
        df_servicos = get_servicos()
        
        if len(df_servicos) > 0:
            df_display = df_servicos.copy()
            df_display['valor'] = df_display['valor'].apply(formatar_moeda)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("📭 Nenhum serviço cadastrado")

# ================= PÁGINA: ALTERAR SENHA =================

elif st.session_state.pagina == "🔑 Alterar Senha":
    st.title("🔑 Alterar Senha")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.info(f"👤 Usuário: **{st.session_state.user_nome}**")
        st.markdown("---")

        with st.form("form_alterar_senha"):
            senha_atual = st.text_input(
                "🔒 Senha Atual",
                type="password",
                placeholder="Digite sua senha atual"
            )

            nova_senha = st.text_input(
                "🔑 Nova Senha",
                type="password",
                placeholder="Mínimo 6 caracteres"
            )

            confirmar_senha = st.text_input(
                "✅ Confirmar Nova Senha",
                type="password",
                placeholder="Repita a nova senha"
            )

            submitted = st.form_submit_button(
                "💾 Salvar Nova Senha",
                use_container_width=True
            )

            if submitted:
                # Validações
                if not senha_atual or not nova_senha or not confirmar_senha:
                    st.error("⚠️ Preencha todos os campos!")

                elif len(nova_senha) < 6:
                    st.error("⚠️ A nova senha deve ter pelo menos 6 caracteres!")

                elif nova_senha != confirmar_senha:
                    st.error("⚠️ A nova senha e a confirmação não coincidem!")

                elif nova_senha == senha_atual:
                    st.warning("⚠️ A nova senha deve ser diferente da senha atual!")

                else:
                    ok, msg = alterar_senha(
                        st.session_state.user_id,
                        senha_atual,
                        nova_senha
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                        st.balloons()
                    else:
                        st.error(f"❌ {msg}")

        st.markdown("---")
        st.markdown("""
        **💡 Dicas para uma boa senha:**
        - Mínimo de 6 caracteres
        - Misture letras maiúsculas e minúsculas
        - Use números e símbolos (ex: @, #, !)
        - Evite datas de nascimento ou sequências óbvias
        """)

