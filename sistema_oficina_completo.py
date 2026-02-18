"""
SISTEMA DE OFICINA - VERSÃO WEB COMPLETA
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import io
import hashlib
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import os
import qrcode

st.set_page_config(page_title="Sistema Oficina", page_icon="🔧",
                   layout="wide", initial_sidebar_state="expanded")

DB        = "oficina.db"
LOGO_PATH = "logo.png"

MODELOS_POR_MARCA = {
    "CHEVROLET":  ["AGILE","ASTRA","BLAZER","CELTA","COBALT","CRUZE","EQUINOX","KADETT","MERIVA",
                   "MONTANA","ONIX","ONIX PLUS","PRISMA","S10","SPIN","TRACKER","TRAILBLAZER","VECTRA","ZAFIRA"],
    "FIAT":       ["ARGO","BRAVO","CRONOS","DOBLO","DUCATO","FIORINO","GRAND SIENA","IDEA","LINEA",
                   "MAREA","MOBI","PALIO","PALIO WEEKEND","PUNTO","SIENA","STRADA","TORO","UNO"],
    "FORD":       ["BRONCO","COURIER","ECOSPORT","EDGE","ESCORT","F-150","F-250","FIESTA","FLEX",
                   "FOCUS","FUSION","KA","KA+","MAVERICK","MUSTANG","RANGER","TERRITORY"],
    "HONDA":      ["ACCORD","CITY","CIVIC","CR-V","FIT","HR-V","WR-V"],
    "HYUNDAI":    ["AZERA","CRETA","ELANTRA","HB20","HB20S","HB20X","IX35","SANTA FE","TUCSON","VELOSTER"],
    "JEEP":       ["COMMANDER","COMPASS","GLADIATOR","GRAND CHEROKEE","RENEGADE","WRANGLER"],
    "KIA":        ["CADENZA","CARNIVAL","CERATO","NIRO","OPTIMA","PICANTO","SOUL","SPORTAGE","STINGER","STONIC"],
    "MERCEDES":   ["A 200","C 180","C 200","C 300","CLA 200","E 200","GLA 200","GLC 250","SPRINTER"],
    "MITSUBISHI": ["ASX","ECLIPSE CROSS","L200","LANCER","OUTLANDER","PAJERO","PAJERO SPORT"],
    "NISSAN":     ["FRONTIER","KICKS","LEAF","LIVINA","MARCH","SENTRA","TIIDA","VERSA","X-TRAIL"],
    "PEUGEOT":    ["2008","207","208","3008","308","408","5008","BOXER","EXPERT","PARTNER"],
    "RENAULT":    ["CAPTUR","CLIO","DUSTER","FLUENCE","KARDIAN","KWID","LOGAN","OROCH","SANDERO","STEPWAY"],
    "TOYOTA":     ["CAMRY","COROLLA","COROLLA CROSS","ETIOS","HILUX","LAND CRUISER","PRIUS","RAV4","SW4","YARIS"],
    "VW":         ["AMAROK","ARTEON","BORA","CROSSFOX","FOX","FUSCA","GOL","GOLF","JETTA","KOMBI",
                   "NIVUS","PASSAT","POLO","SAVEIRO","T-CROSS","TAOS","TIGUAN","TOUAREG","UP","VIRTUS","VOYAGE"],
    "BMW":        ["116i","118i","120i","125i","218i","220i","320i","328i","330i","520i","X1","X3","X5","X6"],
    "AUDI":       ["A1","A3","A4","A5","A6","A7","Q2","Q3","Q5","Q7","TT"],
    "OUTRA":      [],
}

TODOS_MENUS = ["🏠 Dashboard","👥 Clientes e Carros","💰 Orçamentos",
               "📜 Histórico","✅ Serviços Realizados","📚 Catálogo",
               "🔑 Alterar Senha","👤 Usuários","⚙️ Configurações"]

# ═══════════════════════════ BANCO ═══════════════════════════

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, telefone TEXT, logradouro TEXT, numero TEXT);
        CREATE TABLE IF NOT EXISTS carros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER, placa TEXT UNIQUE,
            marca TEXT, modelo TEXT, km INTEGER);
        CREATE TABLE IF NOT EXISTS catalogo_servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT, valor REAL);
        CREATE TABLE IF NOT EXISTS orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER, carro_id INTEGER,
            data TEXT, status TEXT, total REAL, observacoes TEXT);
        CREATE TABLE IF NOT EXISTS itens_orcamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orcamento_id INTEGER, servico_id INTEGER,
            descricao TEXT, quantidade INTEGER,
            valor_unitario REAL, subtotal REAL);
        CREATE TABLE IF NOT EXISTS servicos_realizados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orcamento_id INTEGER, cliente_id INTEGER, carro_id INTEGER,
            data TEXT, total REAL, observacoes TEXT);
        CREATE TABLE IF NOT EXISTS itens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            servico_id INTEGER, descricao TEXT,
            quantidade INTEGER, valor_unitario REAL, subtotal REAL);
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT,
            nome TEXT, nivel TEXT, menus_permitidos TEXT);
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT);
    """)
    c.execute("SELECT id FROM usuarios WHERE username='admin'")
    if not c.fetchone():
        c.execute("""INSERT INTO usuarios(username,password,nome,nivel,menus_permitidos)
                     VALUES('admin',?,  'Administrador','admin',?)""",
                  (hashlib.sha256("admin123".encode()).hexdigest(), ",".join(TODOS_MENUS)))
    # Config padrão PIX
    c.execute("SELECT valor FROM configuracoes WHERE chave='chave_pix'")
    if not c.fetchone():
        c.execute("INSERT INTO configuracoes(chave,valor) VALUES('chave_pix','19995056708')")
    conn.commit(); conn.close()

def get_conn(): return sqlite3.connect(DB)

def get_config(chave, padrao=""):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT valor FROM configuracoes WHERE chave=?", (chave,))
    r = c.fetchone(); conn.close()
    return r[0] if r else padrao

def set_config(chave, valor):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO configuracoes(chave,valor) VALUES(?,?)", (chave,valor))
    conn.commit(); conn.close()

# ═══════════════════════════ AUTENTICAÇÃO ═══════════════════════════

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def verificar_login(username, password):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id,nome,nivel,menus_permitidos FROM usuarios WHERE username=? AND password=?",
              (username, hash_pw(password)))
    r = c.fetchone(); conn.close(); return r

def alterar_senha(user_id, atual, nova):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id FROM usuarios WHERE id=? AND password=?", (user_id, hash_pw(atual)))
    if not c.fetchone():
        conn.close(); return False, "Senha atual incorreta!"
    c.execute("UPDATE usuarios SET password=? WHERE id=?", (hash_pw(nova), user_id))
    conn.commit(); conn.close(); return True, "Senha alterada com sucesso!"

def tela_login():
    _, col, _ = st.columns([1,2,1])
    with col:
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, use_container_width=True)
        st.title("🔧 Sistema Oficina")
        st.markdown("---")
        with st.form("login_form"):
            username = st.text_input("👤 Usuário")
            password = st.text_input("🔒 Senha", type="password")
            if st.form_submit_button("🚀 Entrar", use_container_width=True):
                if username and password:
                    r = verificar_login(username, password)
                    if r:
                        st.session_state.update(logged_in=True, user_id=r[0],
                            user_nome=r[1], user_nivel=r[2],
                            menus_permitidos=(r[3] or "").split(","))
                        st.rerun()
                    else: st.error("❌ Usuário ou senha incorretos!")
                else: st.warning("⚠️ Preencha todos os campos!")
        st.caption("💡 Padrão: admin / admin123")

# ═══════════════════════════ CSS ═══════════════════════════

def load_css():
    st.markdown("""<style>
    [data-testid="stSidebar"]           {background-color:#1a2634;}
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] small     {color:#f0f4f8 !important;}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3        {color:#fff !important;}
    [data-testid="stSidebar"] hr        {border-color:#2d3f53 !important;}
    [data-testid="stSidebar"] .stButton>button{
        background:#c0392b!important;color:#fff!important;
        border:none!important;border-radius:6px!important;
        font-weight:bold!important;width:100%;}
    [data-testid="stSidebar"] .stButton>button:hover{background:#a93226!important;}
    .main{padding:1rem;}
    h1{color:#1f77b4;padding-bottom:.5rem;border-bottom:3px solid #1f77b4;margin-bottom:1.5rem;}
    h2{color:#2c3e50;margin-top:1.5rem;}
    .main .stButton>button{background:#1f77b4;color:white;border-radius:6px;font-weight:bold;border:none;}
    .main .stButton>button:hover{background:#155a8a;}
    [data-testid="stMetric"]{background:#f7f9fc;border-radius:10px;padding:1rem;border:1px solid #e2e8f0;}
    </style>""", unsafe_allow_html=True)

# ═══════════════════════════ HELPERS ═══════════════════════════

def fmt_moeda(v):
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def fmt_km(v):
    try: return f"{int(v):,} km".replace(",",".")
    except: return str(v)

def agora_br(): return datetime.now().strftime("%d/%m/%Y %H:%M")

def gerar_qrcode_pix(chave_pix, valor, nome_beneficiario="Oficina"):
    """Gera QR Code PIX no formato EMV (padrão brasileiro válido)"""
    
    # Limpar chave (remover espaços e caracteres especiais de formatação)
    chave_limpa = chave_pix.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
    
    # Para telefone, adicionar +55 se não tiver
    if chave_limpa.isdigit() and len(chave_limpa) >= 10:
        # É um número de telefone
        if not chave_limpa.startswith("55"):
            chave_limpa = "55" + chave_limpa
        chave_limpa = "+" + chave_limpa
    
    # Construir payload PIX no formato EMV (BRCode)
    # ID 00: Payload Format Indicator
    pfi = "000201"
    
    # ID 26: Merchant Account Information
    gui = "0014br.gov.bcb.pix"
    chave_field = f"01{len(chave_limpa):02d}{chave_limpa}"
    mai_content = gui + chave_field
    mai = f"26{len(mai_content):02d}{mai_content}"
    
    # ID 52: Merchant Category Code
    mcc = "52040000"
    
    # ID 53: Transaction Currency (986 = BRL)
    currency = "5303986"
    
    # ID 54: Transaction Amount
    valor_str = f"{valor:.2f}"
    amount = f"54{len(valor_str):02d}{valor_str}"
    
    # ID 58: Country Code
    country = "5802BR"
    
    # ID 59: Merchant Name
    nome_clean = nome_beneficiario[:25].upper()
    merchant = f"59{len(nome_clean):02d}{nome_clean}"
    
    # ID 60: Merchant City
    city = "6009SAO PAULO"
    
    # ID 62: Additional Data Field
    ref = "***"
    adf_content = f"05{len(ref):02d}{ref}"
    adf = f"62{len(adf_content):02d}{adf_content}"
    
    # Montar payload sem CRC
    payload_sem_crc = pfi + mai + mcc + currency + amount + country + merchant + city + adf + "6304"
    
    # Calcular CRC16-CCITT
    def crc16_ccitt(data):
        crc = 0xFFFF
        for byte in data.encode('utf-8'):
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        return f"{crc:04X}"
    
    # Payload final com CRC
    crc = crc16_ccitt(payload_sem_crc)
    payload_completo = payload_sem_crc + crc
    
    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2
    )
    qr.add_data(payload_completo)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# ═══════════════════════════ DADOS — CLIENTES ═══════════════════════════

def get_clientes():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM clientes ORDER BY nome", conn)
    conn.close(); return df

def salvar_cliente(nome, telefone, logradouro, numero, cid=None):
    conn = get_conn(); c = conn.cursor()
    if cid:
        c.execute("UPDATE clientes SET nome=?,telefone=?,logradouro=?,numero=? WHERE id=?",
                  (nome, telefone, logradouro, numero, cid))
    else:
        c.execute("INSERT INTO clientes(nome,telefone,logradouro,numero) VALUES(?,?,?,?)",
                  (nome, telefone, logradouro, numero))
    conn.commit(); conn.close()

def pode_excluir_cliente(cid):
    conn = get_conn(); c = conn.cursor()
    carros = c.execute("SELECT COUNT(*) FROM carros WHERE cliente_id=?", (cid,)).fetchone()[0]
    orc    = c.execute("SELECT COUNT(*) FROM orcamentos WHERE cliente_id=?", (cid,)).fetchone()[0]
    serv   = c.execute("SELECT COUNT(*) FROM servicos_realizados WHERE cliente_id=?", (cid,)).fetchone()[0]
    conn.close()
    if carros: return False, f"possui {carros} veículo(s) cadastrado(s)"
    if orc:    return False, f"possui {orc} orçamento(s) cadastrado(s)"
    if serv:   return False, f"possui {serv} serviço(s) realizado(s)"
    return True, ""

def excluir_cliente(cid):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM clientes WHERE id=?", (cid,))
    conn.commit(); conn.close()

# ═══════════════════════════ DADOS — CARROS ═══════════════════════════

def get_carros_por_cliente(cid):
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM carros WHERE cliente_id=? ORDER BY placa", conn, params=(cid,))
    conn.close(); return df

def salvar_carro(cliente_id, placa, marca, modelo, km, carro_id=None):
    conn = get_conn(); c = conn.cursor()
    if carro_id:
        c.execute("UPDATE carros SET placa=?,marca=?,modelo=?,km=? WHERE id=?",
                  (placa.upper(), marca, modelo, int(km), carro_id))
    else:
        c.execute("INSERT INTO carros(cliente_id,placa,marca,modelo,km) VALUES(?,?,?,?,?)",
                  (cliente_id, placa.upper(), marca, modelo, int(km)))
    conn.commit(); conn.close()

# ═══════════════════════════ DADOS — SERVIÇOS ═══════════════════════════

def get_servicos():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM catalogo_servicos ORDER BY descricao", conn)
    conn.close(); return df

def salvar_servico(descricao, valor, sid=None):
    conn = get_conn(); c = conn.cursor()
    if sid:
        c.execute("UPDATE catalogo_servicos SET descricao=?,valor=? WHERE id=?",
                  (descricao.upper(), valor, sid))
    else:
        c.execute("INSERT INTO catalogo_servicos(descricao,valor) VALUES(?,?)",
                  (descricao.upper(), valor))
    conn.commit(); conn.close()

def excluir_servico(sid):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM catalogo_servicos WHERE id=?", (sid,))
    conn.commit(); conn.close()

def salvar_orcamento(cliente_id, carro_id, status, observacoes, itens):
    conn = get_conn(); c = conn.cursor()
    data  = agora_br()
    total = sum(i['subtotal'] for i in itens)
    c.execute("INSERT INTO orcamentos(cliente_id,carro_id,data,status,total,observacoes) VALUES(?,?,?,?,?,?)",
              (cliente_id, carro_id, data, status, total, observacoes))
    oid = c.lastrowid
    for i in itens:
        c.execute("""INSERT INTO itens_orcamento(orcamento_id,servico_id,descricao,
                     quantidade,valor_unitario,subtotal) VALUES(?,?,?,?,?,?)""",
                  (oid, i['servico_id'], i['descricao'], i['quantidade'],
                   i['valor_unitario'], i['subtotal']))
    if status == 'APROVADO':
        c.execute("INSERT INTO servicos_realizados(orcamento_id,cliente_id,carro_id,data,total,observacoes) VALUES(?,?,?,?,?,?)",
                  (oid, cliente_id, carro_id, data, total, observacoes))
        sid2 = c.lastrowid
        for i in itens:
            c.execute("INSERT INTO itens_servico(servico_id,descricao,quantidade,valor_unitario,subtotal) VALUES(?,?,?,?,?)",
                      (sid2, i['descricao'], i['quantidade'], i['valor_unitario'], i['subtotal']))
    conn.commit(); conn.close(); return oid

def get_orcamentos():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT o.id,c.nome,ca.placa,o.data,o.status,o.total
        FROM orcamentos o
        JOIN clientes c ON o.cliente_id=c.id
        JOIN carros ca  ON o.carro_id=ca.id
        ORDER BY o.id DESC""", conn)
    conn.close(); return df

def get_servicos_realizados(data_ini=None, data_fim=None):
    conn = get_conn()
    q = """SELECT s.id,c.nome,ca.placa,s.data,s.total
           FROM servicos_realizados s
           JOIN clientes c ON s.cliente_id=c.id
           JOIN carros ca  ON s.carro_id=ca.id"""
    params = []
    if data_ini and data_fim:
        q += " WHERE s.data >= ? AND s.data <= ?"
        params = [data_ini, data_fim + " 23:59"]
    q += " ORDER BY s.id DESC"
    df = pd.read_sql_query(q, conn, params=params)
    conn.close(); return df

def gerar_pdf_orcamento(oid):
    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT o.id,c.nome,c.telefone,c.logradouro,c.numero,
                        ca.placa,ca.marca,ca.modelo,ca.km,
                        o.data,o.status,o.total,o.observacoes
                 FROM orcamentos o
                 JOIN clientes c ON o.cliente_id=c.id
                 JOIN carros ca  ON o.carro_id=ca.id
                 WHERE o.id=?""", (oid,))
    orc = c.fetchone()
    c.execute("SELECT descricao,quantidade,valor_unitario,subtotal FROM itens_orcamento WHERE orcamento_id=?", (oid,))
    itens = c.fetchall(); conn.close()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    st_t = ParagraphStyle('T',parent=styles['Heading1'],fontSize=18,
                          textColor=colors.HexColor('#1a1a1a'),spaceAfter=20,alignment=TA_CENTER)
    elems = [Paragraph(f"ORÇAMENTO Nº {orc[0]:04d}", st_t), Spacer(1,10)]
    info = [['Data:',orc[9],'Status:',orc[10]],
            ['Cliente:',orc[1],'',''],
            ['Telefone:',orc[2] or '—','',''],
            ['Endereço:',f"{orc[3] or ''} {orc[4] or ''}".strip(),'',''],
            ['Veículo:',f"{orc[6]} {orc[7]}",'Placa:',orc[5]],
            ['KM:',fmt_km(orc[8]),'','']]
    t = Table(info, colWidths=[1.5*inch,2.5*inch,1*inch,1.5*inch])
    t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Helvetica'),
                            ('FONTSIZE',(0,0),(-1,-1),10),
                            ('GRID',(0,0),(-1,-1),.5,colors.grey)]))
    elems += [t, Spacer(1,14)]
    rows = [['Descrição','Qtd','Valor Unit.','Subtotal']]
    for i in itens:
        rows.append([i[0],str(i[1]),f"R$ {i[2]:.2f}",f"R$ {i[3]:.2f}"])
    st2 = Table(rows, colWidths=[3.5*inch,.7*inch,1.2*inch,1.2*inch])
    st2.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#2c3e50')),
                              ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                              ('ALIGN',(0,0),(-1,-1),'CENTER'),
                              ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                              ('GRID',(0,0),(-1,-1),1,colors.black)]))
    elems += [st2, Spacer(1,10)]
    tot = Table([['','','TOTAL:',f"R$ {orc[11]:.2f}"]],
                colWidths=[3.5*inch,.7*inch,1.2*inch,1.2*inch])
    tot.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'),
                              ('FONTSIZE',(0,0),(-1,-1),13),
                              ('ALIGN',(2,0),(-1,-1),'RIGHT')]))
    elems.append(tot)
    elems.append(Spacer(1, 20))
    
    # ─── QR CODE PIX ───
    chave_pix = get_config('chave_pix', '19995056708')
    qr_img_buf = gerar_qrcode_pix(chave_pix, orc[11])
    
    pix_txt = Paragraph(f"<b>Pagamento via PIX</b><br/>Chave: {chave_pix}<br/>Valor: R$ {orc[11]:.2f}",
                        styles['Normal'])
    elems.append(pix_txt)
    elems.append(Spacer(1, 10))
    
    qr_img = RLImage(qr_img_buf, width=1.5*inch, height=1.5*inch)
    elems.append(qr_img)
    
    doc.build(elems); buf.seek(0); return buf

# ═══════════════════════════ DADOS — USUÁRIOS ═══════════════════════════

def get_usuarios():
    conn = get_conn()
    df = pd.read_sql_query("SELECT id,username,nome,nivel,menus_permitidos FROM usuarios ORDER BY nome", conn)
    conn.close(); return df

def salvar_usuario(username, nome, nivel, menus, uid=None, senha=None):
    conn = get_conn(); c = conn.cursor()
    menus_str = ",".join(menus)
    try:
        if uid:
            # Editando usuário existente
            if senha:
                c.execute("UPDATE usuarios SET username=?,nome=?,nivel=?,menus_permitidos=?,password=? WHERE id=?",
                          (username, nome, nivel, menus_str, hash_pw(senha), uid))
            else:
                c.execute("UPDATE usuarios SET username=?,nome=?,nivel=?,menus_permitidos=? WHERE id=?",
                          (username, nome, nivel, menus_str, uid))
        else:
            # Criando novo usuário
            if not senha:
                conn.close()
                return False, "Informe a senha para novo usuário!"
            
            # Verificar se username já existe
            c.execute("SELECT id FROM usuarios WHERE username=?", (username,))
            if c.fetchone():
                conn.close()
                return False, f"Login '{username}' já existe! Escolha outro."
            
            # Inserir novo usuário
            c.execute("INSERT INTO usuarios(username,nome,nivel,menus_permitidos,password) VALUES(?,?,?,?,?)",
                      (username, nome, nivel, menus_str, hash_pw(senha)))
        
        conn.commit()
        conn.close()
        return True, "Usuário salvo com sucesso!"
        
    except sqlite3.IntegrityError as e:
        conn.close()
        return False, f"Erro: Login já existe ou dados inválidos. ({str(e)})"
    except Exception as e:
        conn.close()
        return False, f"Erro ao salvar usuário: {str(e)}"

def excluir_usuario(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM usuarios WHERE id=?", (uid,))
    conn.commit(); conn.close()

# ═══════════════════════════ INICIALIZAÇÃO ═══════════════════════════

init_db()
for k, v in [("logged_in",False),("pagina","🏠 Dashboard"),
             ("itens_orcamento",[]),("menus_permitidos",TODOS_MENUS)]:
    if k not in st.session_state: st.session_state[k] = v

if not st.session_state.logged_in:
    tela_login(); st.stop()

load_css()

# ═══════════════════════════ SIDEBAR ═══════════════════════════

menus_user = [m for m in TODOS_MENUS if m in st.session_state.menus_permitidos]

with st.sidebar:
    if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, use_container_width=True)
    else: st.title("🔧 Oficina")
    st.markdown("---")
    st.write(f"👤 **{st.session_state.user_nome}**")
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()
    st.markdown("---")
    if st.session_state.pagina not in menus_user:
        st.session_state.pagina = menus_user[0]
    st.session_state.pagina = st.radio("📋 Menu", menus_user)
    st.markdown("---")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

pag = st.session_state.pagina

# ═══════════════════════════ DASHBOARD ═══════════════════════════

if pag == "🏠 Dashboard":
    st.title("🏠 Dashboard")
    conn = get_conn(); c = conn.cursor()
    tot_cli  = c.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    tot_car  = c.execute("SELECT COUNT(*) FROM carros").fetchone()[0]
    tot_serv = c.execute("SELECT COUNT(*) FROM servicos_realizados").fetchone()[0]
    fat_mes  = c.execute("SELECT COALESCE(SUM(total),0) FROM servicos_realizados").fetchone()[0]
    conn.close()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("👥 Clientes", tot_cli)
    c2.metric("🚗 Veículos", tot_car)
    c3.metric("✅ Serviços Realizados", tot_serv)
    c4.metric("💰 Faturamento Total", fmt_moeda(fat_mes))
    st.markdown("---")
    l, r = st.columns(2)
    with l:
        st.subheader("📊 Orçamentos por Status")
        df_o = get_orcamentos()
        if len(df_o): st.bar_chart(df_o['status'].value_counts())
        else: st.info("Nenhum orçamento ainda")
    with r:
        st.subheader("📈 Últimos Serviços")
        df_s = get_servicos_realizados()
        if len(df_s):
            st.dataframe(df_s.head(5)[['nome','placa','data','total']],
                         use_container_width=True, hide_index=True)
        else: st.info("Nenhum serviço realizado")

# ═══════════════════════════ CLIENTES E CARROS ═══════════════════════════

elif pag == "👥 Clientes e Carros":
    st.title("👥 Clientes e Veículos")
    tab1, tab2 = st.tabs(["📋 Clientes", "🚗 Carros"])

    with tab1:
        st.subheader("Cadastro de Clientes")
        with st.form("form_cliente"):
            nome = st.text_input("Nome do Cliente *")
            col1, col2 = st.columns(2)
            with col1: telefone   = st.text_input("Telefone", placeholder="(00) 00000-0000")
            with col2: logradouro = st.text_input("Endereço")
            numero = st.text_input("Número")
            if st.form_submit_button("💾 Salvar Cliente", use_container_width=True):
                if nome:
                    salvar_cliente(nome.upper(), telefone, logradouro.upper(), numero)
                    st.success(f"✅ Cliente '{nome.upper()}' salvo!"); st.rerun()
                else: st.error("⚠️ Nome é obrigatório!")

        st.markdown("---")
        st.subheader("📋 Clientes Cadastrados")
        df_cli = get_clientes()
        if len(df_cli):
            busca = st.text_input("🔍 Buscar cliente", placeholder="Digite o nome...")
            if busca:
                df_cli = df_cli[df_cli['nome'].str.contains(busca.upper(), na=False)]
            # Montar exibição: unir logradouro + numero como "Endereço", remover colunas separadas
            df_show = df_cli.copy()
            df_show['Endereço'] = df_show.apply(
                lambda r: f"{r['logradouro'] or ''} {r['numero'] or ''}".strip(), axis=1)
            df_show = df_show[['id','nome','telefone','Endereço']]
            df_show.columns = ['ID','Nome','Telefone','Endereço']
            st.dataframe(df_show, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("🗑️ Excluir Cliente")
            del_opts = {f"{r['ID']} — {r['Nome']}": r['ID'] for _, r in df_show.iterrows()}
            sel_del  = st.selectbox("Selecione o cliente para excluir", list(del_opts.keys()))
            cid_del  = del_opts[sel_del]
            pode, motivo = pode_excluir_cliente(cid_del)
            if not pode:
                st.warning(f"⚠️ Não é possível excluir: cliente {motivo}.")
            else:
                if st.button("🗑️ Confirmar Exclusão", type="primary"):
                    excluir_cliente(cid_del)
                    st.success("✅ Cliente excluído com sucesso!"); st.rerun()
        else:
            st.info("📭 Nenhum cliente cadastrado")

    with tab2:
        st.subheader("Cadastro de Veículos")
        df_cli2 = get_clientes()
        if not len(df_cli2): st.warning("⚠️ Cadastre um cliente primeiro!"); st.stop()

        cli_opts = {f"{r['id']} - {r['nome']}": r['id'] for _, r in df_cli2.iterrows()}
        cli_sel  = st.selectbox("Cliente *", list(cli_opts.keys()))
        cli_id   = cli_opts[cli_sel]

        st.markdown("---")

        # ── Marca e Modelo FORA do form: reagem instantaneamente ──
        col1, col2 = st.columns(2)
        with col1:
            marca = st.selectbox(
                "Marca *",
                [""] + sorted(MODELOS_POR_MARCA.keys()),
                key="sel_marca"
            )
        with col2:
            mods = MODELOS_POR_MARCA.get(marca, []) if marca else []
            if not marca:
                # Nenhuma marca selecionada ainda
                st.selectbox("Modelo *", ["— selecione a marca primeiro —"],
                             disabled=True, key="sel_modelo_vazio")
                modelo = ""
            elif marca == "OUTRA" or not mods:
                # Marca sem lista → campo livre
                modelo = st.text_input("Modelo *", placeholder="Digite o modelo",
                                       key="modelo_livre")
            else:
                opcoes_mod = mods + ["✏️ Outro (digitar)"]
                sel_mod = st.selectbox("Modelo *", [""] + opcoes_mod, key="sel_modelo")
                if sel_mod == "✏️ Outro (digitar)":
                    modelo = st.text_input("Digite o modelo:", key="modelo_outro")
                else:
                    modelo = sel_mod

        # ── Placa, KM e botão salvar dentro do form ──
        with st.form("form_carro"):
            col1, col2 = st.columns(2)
            with col1:
                placa = st.text_input("Placa *", placeholder="ABC1D23")
            with col2:
                km = st.number_input("Quilometragem", min_value=0, step=1000)

            if st.form_submit_button("💾 Salvar Veículo", use_container_width=True):
                if placa and marca and modelo:
                    try:
                        salvar_carro(cli_id, placa, marca, modelo.upper(), km)
                        st.success(f"✅ Veículo {placa.upper()} salvo!"); st.rerun()
                    except Exception:
                        st.error("❌ Placa já cadastrada!")
                else:
                    st.error("⚠️ Preencha placa, marca e modelo!")

        st.markdown("---")
        st.subheader("🚗 Veículos Cadastrados")
        df_car = get_carros_por_cliente(cli_id)
        if len(df_car):
            df_c = df_car.copy()
            df_c['km'] = df_c['km'].apply(fmt_km)
            df_c = df_c[['id','placa','marca','modelo','km']]
            df_c.columns = ['ID','Placa','Marca','Modelo','KM']
            st.dataframe(df_c, use_container_width=True, hide_index=True)
        else: st.info("📭 Nenhum veículo cadastrado para este cliente")

# ═══════════════════════════ ORÇAMENTOS ═══════════════════════════

elif pag == "💰 Orçamentos":
    st.title("💰 Novo Orçamento")
    df_cli = get_clientes(); df_srv = get_servicos()
    if not len(df_cli): st.warning("⚠️ Cadastre clientes primeiro!"); st.stop()
    if not len(df_srv): st.warning("⚠️ Cadastre serviços no catálogo!"); st.stop()

    col1, col2 = st.columns(2)
    with col1:
        cli_opts = {f"{r['id']} - {r['nome']}": r['id'] for _, r in df_cli.iterrows()}
        cli_sel  = st.selectbox("1️⃣ Cliente *", list(cli_opts.keys()))
        cli_id   = cli_opts[cli_sel]
    with col2:
        df_c = get_carros_por_cliente(cli_id)
        if not len(df_c): st.error("⚠️ Cliente sem veículos cadastrados!"); st.stop()
        car_opts = {f"{r['placa']} — {r['marca']} {r['modelo']}": r['id'] for _, r in df_c.iterrows()}
        car_sel  = st.selectbox("2️⃣ Veículo *", list(car_opts.keys()))
        car_id   = car_opts[car_sel]

    st.markdown("---")
    st.subheader("3️⃣ Adicionar Serviços")
    col1, col2, col3, col4 = st.columns([3,1,1,1])
    with col1:
        srv_opts = {f"{r['id']} — {r['descricao']}  ({fmt_moeda(r['valor'])})":
                    (r['id'], r['descricao'], r['valor']) for _, r in df_srv.iterrows()}
        srv_sel = st.selectbox("Serviço", list(srv_opts.keys()))
        sid, desc, val = srv_opts[srv_sel]
    with col2: qtd   = st.number_input("Qtd", min_value=1, value=1)
    with col3: vunit = st.number_input("Valor", value=float(val), step=10.0)
    with col4:
        st.write(""); st.write("")
        if st.button("➕ Adicionar", use_container_width=True):
            st.session_state.itens_orcamento.append(
                {'servico_id':sid,'descricao':desc,'quantidade':qtd,
                 'valor_unitario':vunit,'subtotal':qtd*vunit})
            st.rerun()

    if st.session_state.itens_orcamento:
        st.subheader("📋 Itens do Orçamento")
        df_it = pd.DataFrame(st.session_state.itens_orcamento)
        df_it['vu_fmt'] = df_it['valor_unitario'].apply(fmt_moeda)
        df_it['st_fmt'] = df_it['subtotal'].apply(fmt_moeda)
        st.dataframe(df_it[['descricao','quantidade','vu_fmt','st_fmt']],
                     use_container_width=True, hide_index=True,
                     column_config={'descricao':'Descrição','quantidade':'Qtd',
                                    'vu_fmt':'Valor Unit.','st_fmt':'Subtotal'})
        total = sum(i['subtotal'] for i in st.session_state.itens_orcamento)
        st.metric("💰 TOTAL", fmt_moeda(total))
        col1, col2 = st.columns([3,1])
        with col1: obs    = st.text_area("Observações")
        with col2: status = st.selectbox("Status",["PENDENTE","APROVADO","RECUSADO","FINALIZADO"])
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Orçamento", use_container_width=True, type="primary"):
                oid = salvar_orcamento(cli_id, car_id, status, obs, st.session_state.itens_orcamento)
                st.success(f"✅ Orçamento #{oid} salvo!")
                st.session_state.itens_orcamento = []; st.rerun()
        with col2:
            if st.button("🗑️ Limpar Tudo", use_container_width=True):
                st.session_state.itens_orcamento = []; st.rerun()
    else: st.info("➕ Adicione serviços ao orçamento")

# ═══════════════════════════ HISTÓRICO ═══════════════════════════

elif pag == "📜 Histórico":
    st.title("📜 Histórico de Orçamentos")
    df_o = get_orcamentos()
    if not len(df_o): st.info("📭 Nenhum orçamento cadastrado"); st.stop()
    filtro = st.multiselect("Filtrar por Status", df_o['status'].unique().tolist(),
                            default=df_o['status'].unique().tolist())
    df_f = df_o[df_o['status'].isin(filtro)]
    for _, row in df_f.iterrows():
        cols = st.columns([1,3,2,2,2,2,2])
        cols[0].write(f"**#{row['id']}**")
        cols[1].write(row['nome']); cols[2].write(row['placa'])
        cols[3].write(row['data']); cols[4].write(row['status'])
        cols[5].write(fmt_moeda(row['total']))
        with cols[6]:
            pdf = gerar_pdf_orcamento(row['id'])
            st.download_button("📄 PDF", pdf,
                               file_name=f"Orcamento_{row['id']:04d}.pdf",
                               mime="application/pdf", key=f"dl_{row['id']}")
    st.markdown("---")
    c1,c2,c3 = st.columns(3)
    c1.metric("Pendentes", len(df_f[df_f['status']=='PENDENTE']))
    c2.metric("Aprovados",  len(df_f[df_f['status']=='APROVADO']))
    c3.metric("Total Geral", fmt_moeda(df_f['total'].sum()))

# ═══════════════════════════ SERVIÇOS REALIZADOS ═══════════════════════════

elif pag == "✅ Serviços Realizados":
    st.title("✅ Serviços Realizados")
    col1, col2, col3 = st.columns(3)
    with col1:
        d_ini = st.date_input("Data Inicial", value=date.today().replace(day=1), format="DD/MM/YYYY")
    with col2:
        d_fim = st.date_input("Data Final",   value=date.today(),                format="DD/MM/YYYY")
    with col3:
        st.write(""); st.write("")
        st.button("🔍 Filtrar", use_container_width=True)

    ini_str = d_ini.strftime("%d/%m/%Y")
    fim_str = d_fim.strftime("%d/%m/%Y")
    df_s = get_servicos_realizados(ini_str, fim_str)

    if len(df_s):
        st.metric("💰 Total do Período", fmt_moeda(df_s['total'].sum()),
                  delta=f"{len(df_s)} serviço(s)")
        st.markdown("---")
        df_show = df_s.copy()
        df_show['total'] = df_show['total'].apply(fmt_moeda)
        df_show.columns = ['Nº','Cliente','Placa','Data','Total']
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    else: st.info("📭 Nenhum serviço no período selecionado")

# ═══════════════════════════ CATÁLOGO ═══════════════════════════

elif pag == "📚 Catálogo":
    st.title("📚 Catálogo de Serviços")
    
    tab1, tab2 = st.tabs(["➕ Novo Serviço", "📋 Gerenciar Serviços"])
    
    with tab1:
        st.subheader("Cadastrar Novo Serviço")
        with st.form("form_srv_novo"):
            desc  = st.text_input("Descrição *")
            valor = st.number_input("Valor (R$) *", min_value=0.0, step=10.0, format="%.2f")
            if st.form_submit_button("💾 Salvar Novo Serviço", use_container_width=True):
                if desc and valor > 0:
                    salvar_servico(desc, valor)
                    st.success("✅ Serviço salvo!")
                    st.rerun()
                else:
                    st.warning("⚠️ Preencha todos os campos!")
    
    with tab2:
        st.subheader("Serviços Cadastrados")
        df_srv = get_servicos()
        
        if len(df_srv):
            # Exibir com opções de editar/excluir
            for _, row in df_srv.iterrows():
                with st.expander(f"🔧 {row['descricao']}  — {fmt_moeda(row['valor'])}"):
                    with st.form(f"edit_srv_{row['id']}"):
                        nova_desc = st.text_input("Descrição", value=row['descricao'], key=f"desc_{row['id']}")
                        novo_valor = st.number_input("Valor (R$)", value=float(row['valor']),
                                                     min_value=0.0, step=10.0, format="%.2f",
                                                     key=f"val_{row['id']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                                salvar_servico(nova_desc, novo_valor, row['id'])
                                st.success("✅ Serviço atualizado!")
                                st.rerun()
                        with col2:
                            if st.form_submit_button("🗑️ Excluir Serviço", use_container_width=True):
                                excluir_servico(row['id'])
                                st.success("✅ Serviço excluído!")
                                st.rerun()
        else:
            st.info("📭 Nenhum serviço cadastrado")

# ═══════════════════════════ ALTERAR SENHA ═══════════════════════════

elif pag == "🔑 Alterar Senha":
    st.title("🔑 Alterar Senha")
    _, col, _ = st.columns([1,2,1])
    with col:
        st.info(f"👤 Usuário logado: **{st.session_state.user_nome}**")
        st.markdown("---")
        with st.form("form_senha"):
            atual    = st.text_input("🔒 Senha Atual",          type="password")
            nova     = st.text_input("🔑 Nova Senha",           type="password")
            confirma = st.text_input("✅ Confirmar Nova Senha",  type="password")
            if st.form_submit_button("💾 Salvar Nova Senha", use_container_width=True):
                if not (atual and nova and confirma): st.error("⚠️ Preencha todos os campos!")
                elif len(nova) < 6:                  st.error("⚠️ Mínimo 6 caracteres!")
                elif nova != confirma:               st.error("⚠️ Confirmação não coincide!")
                elif nova == atual:                  st.warning("⚠️ Nova senha igual à atual!")
                else:
                    ok, msg = alterar_senha(st.session_state.user_id, atual, nova)
                    if ok: st.success(f"✅ {msg}"); st.balloons()
                    else:  st.error(f"❌ {msg}")
        st.markdown("---")
        st.markdown("**💡 Dicas:** mínimo 6 caracteres, misture letras, números e símbolos.")

# ═══════════════════════════ GERENCIAR USUÁRIOS ═══════════════════════════

elif pag == "👤 Usuários":
    st.title("👤 Gerenciar Usuários")
    if st.session_state.user_nivel != "admin":
        st.error("🚫 Acesso restrito ao administrador."); st.stop()

    tab1, tab2 = st.tabs(["➕ Novo / Editar Usuário", "📋 Usuários Cadastrados"])

    with tab1:
        st.subheader("Cadastrar Novo Usuário")
        
        # Usar key única para forçar reset do form após salvar
        if 'form_user_key' not in st.session_state:
            st.session_state.form_user_key = 0
        
        with st.form(f"form_usuario_{st.session_state.form_user_key}"):
            col1, col2 = st.columns(2)
            with col1:
                u_username = st.text_input("Login (usuário) *")
                u_nome     = st.text_input("Nome Completo *")
            with col2:
                u_nivel = st.selectbox("Nível de Acesso", ["operador","admin"])
                u_senha = st.text_input("Senha *", type="password")

            st.markdown("**🔐 Menus permitidos para este usuário:**")
            col_a, col_b = st.columns(2)
            menus_sel = []
            for idx, menu in enumerate(TODOS_MENUS):
                col = col_a if idx % 2 == 0 else col_b
                default = True if menu in ["🏠 Dashboard","🔑 Alterar Senha"] else True
                if col.checkbox(menu, value=default, key=f"ck_{menu}_{st.session_state.form_user_key}"):
                    menus_sel.append(menu)

            if st.form_submit_button("💾 Salvar Usuário", use_container_width=True):
                if not u_username:
                    st.error("⚠️ Digite um login para o usuário!")
                elif not u_nome:
                    st.error("⚠️ Digite o nome completo do usuário!")
                elif not u_senha:
                    st.error("⚠️ Digite uma senha para o usuário!")
                elif len(u_senha) < 4:
                    st.error("⚠️ A senha deve ter pelo menos 4 caracteres!")
                else:
                    # Tudo preenchido, tentar salvar
                    ok, msg = salvar_usuario(u_username, u_nome, u_nivel, menus_sel, senha=u_senha)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.balloons()
                        st.session_state.form_user_key += 1  # Incrementa para resetar form
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                        st.warning("💡 Se o problema persistir, verifique se o login já existe.")

    with tab2:
        st.subheader("Usuários Cadastrados")
        df_u = get_usuarios()
        if len(df_u):
            st.dataframe(df_u[['id','username','nome','nivel']],
                         use_container_width=True, hide_index=True,
                         column_config={'id':'ID','username':'Login',
                                        'nome':'Nome','nivel':'Nível'})
            st.markdown("---")
            st.subheader("🔐 Permissões por Usuário")
            for _, row in df_u.iterrows():
                with st.expander(f"👤 {row['nome']}  ({row['username']})"):
                    menus_atuais = (row['menus_permitidos'] or "").split(",")
                    col_a, col_b = st.columns(2)
                    novos = []
                    for idx, menu in enumerate(TODOS_MENUS):
                        col = col_a if idx % 2 == 0 else col_b
                        if col.checkbox(menu, value=(menu in menus_atuais),
                                        key=f"perm_{row['id']}_{idx}"):
                            novos.append(menu)
                    if st.button(f"💾 Salvar Permissões", key=f"sv_{row['id']}"):
                        salvar_usuario(row['username'], row['nome'], row['nivel'],
                                       novos, uid=row['id'])
                        st.success("✅ Permissões salvas!"); st.rerun()

            st.markdown("---")
            st.subheader("🗑️ Excluir Usuário")
            del_opts = {f"{r['id']} — {r['nome']}  ({r['username']})": r['id']
                        for _, r in df_u.iterrows() if r['username'] != 'admin'}
            if del_opts:
                del_sel = st.selectbox("Selecione o usuário", list(del_opts.keys()))
                del_id  = del_opts[del_sel]
                if st.button("🗑️ Excluir Usuário Selecionado", type="primary"):
                    excluir_usuario(del_id); st.success("✅ Excluído!"); st.rerun()
            else:
                st.info("Nenhum usuário disponível para exclusão (admin não pode ser excluído)")
        else:
            st.info("📭 Nenhum usuário cadastrado")

# ═══════════════════════════ CONFIGURAÇÕES ═══════════════════════════

elif pag == "⚙️ Configurações":
    st.title("⚙️ Configurações do Sistema")
    
    if st.session_state.user_nivel != "admin":
        st.error("🚫 Acesso restrito ao administrador.")
        st.stop()
    
    st.subheader("💳 Configurações de Pagamento PIX")
    
    chave_atual = get_config('chave_pix', '19995056708')
    
    with st.form("form_pix"):
        st.info("📱 Esta chave PIX será exibida no QR Code dos orçamentos em PDF")
        
        st.markdown("""
        **📌 Formatos aceitos de Chave PIX:**
        - **Telefone:** Digite só os números (ex: `19995056708` ou `5519995056708`)
        - **E-mail:** Digite completo (ex: `oficina@email.com`)
        - **CPF/CNPJ:** Digite só os números (ex: `12345678900`)
        - **Chave Aleatória:** Cole a chave completa
        
        ⚠️ **IMPORTANTE para Telefone:** 
        - Se seu telefone tem DDD 19 e número 99505-6708
        - Digite: `19995056708` (sem espaços, parênteses ou traços)
        - O sistema adiciona automaticamente o +55 no QR Code
        """)
        
        nova_chave = st.text_input(
            "Chave PIX",
            value=chave_atual,
            placeholder="Ex: 19995056708 (telefone) ou email@dominio.com"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("💡 O QR Code será gerado automaticamente no padrão correto para cada tipo de chave")
        with col2:
            if st.form_submit_button("💾 Salvar Configuração", use_container_width=True):
                if nova_chave and len(nova_chave) >= 8:
                    set_config('chave_pix', nova_chave)
                    st.success("✅ Chave PIX atualizada com sucesso!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("⚠️ Informe uma chave PIX válida (mínimo 8 caracteres)!")
    
    st.markdown("---")
    st.subheader("ℹ️ Informações do Sistema")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📦 Versão", "2.0")
        st.metric("🗄️ Banco de Dados", "SQLite")
    with col2:
        st.metric("👥 Total de Usuários", len(get_usuarios()))
        st.metric("🔧 Serviços Cadastrados", len(get_servicos()))
    
    st.markdown("---")
    st.caption("💡 Outras configurações podem ser adicionadas aqui conforme necessário")
