import streamlit as st
import pypdf
from docx import Document
import json
import re
import io
import time
import pandas as pd
from datetime import datetime
from groq import Groq
from openai import OpenAI

# Configuración de la página
st.set_page_config(page_title="Validador de Pagos UNAL - Centro de Prototipado", layout="wide")

# Estilos CSS Modernos (Tema Oscuro OLED para máxima legibilidad)
st.markdown("""
    <style>
    /* Fondo General */
    .main, .stApp { 
        background-color: #000c1a !important; 
        color: #e6f1ff !important; 
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #001529 !important;
        border-right: 1px solid #1890ff;
    }
    
    /* Contenedores de Información (Cards) */
    .card {
        background-color: #001a33;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #004b8d;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    
    /* Input Labels y Textos de Streamlit */
    label, p, span, .stMarkdown, .stSelectbox, div[data-baseweb="select"] {
        color: #e6f1ff !important;
    }
    
    /* Botón Principal */
    .stButton>button {
        background: linear-gradient(90deg, #1890ff 0%, #0050b3 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.7rem 2.5rem !important;
        font-weight: bold !important;
        box-shadow: 0 5px 15px rgba(24, 144, 255, 0.3);
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1890ff !important;
        font-family: 'Inter', sans-serif;
    }

    /* Tablas de Auditoría */
    .stTable {
        background-color: #001a33 !important;
        color: #e6f1ff !important;
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

# --- VARIABLES GLOBALES / CONFIG ---
MESES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04", 
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08", 
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
}

# --- UTILERÍAS DE NORMALIZACIÓN ---
def normalize_money(val):
    if not val: return 0
    return int(re.sub(r'\D', '', str(val)))

def normalize_date(date_str):
    if not date_str: return "-"
    clean = re.sub(r'[^\d/]', '', str(date_str))
    try: return datetime.strptime(clean, "%d/%m/%Y").strftime("%Y/%m/%d")
    except: pass
    try: return datetime.strptime(clean, "%Y/%m/%d").strftime("%Y/%m/%d")
    except: pass
    return clean

# --- FUNCIONES DE EXTRACCIÓN DE TEXTO ---
def extract_text_from_pdf(pdf_file):
    try:
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception: return ""

def extract_text_from_docx(docx_file):
    try:
        doc = Document(docx_file)
        full_text = []
        for para in doc.paragraphs: full_text.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells: full_text.append(cell.text)
        return "\n".join(full_text)
    except Exception: return ""

# --- LÓGICA DE IA (Análisis por Documento) ---
def extract_data_with_ai(text, doc_type, model, api_key, provider):
    if not api_key: return {"error": "API Key faltante"}
    
    contexto = {
        "contrato": "Extrae número de orden (OSE/CPS), vigencia inicial/final y valor total del contrato.",
        "4013": "Extrae planilla PILA (10 dígitos), fecha de pago real y empresa Quipu.",
        "constancia": "Extrae periodo de cumplimiento y número de pago parcial (consecutivo)."
    }.get(doc_type, "")

    prompt = f"""
    Eres un auditor experto de la UNAL. Analiza este documento ({doc_type}). 
    {contexto}
    
    Extrae en JSON puro:
    1. numero_contrato (Si es 'OSE-14-4013...', EXTRAE SOLO '14').
    2. riesgo_arl (dígito 1-5)
    3. valor_total (monto TOTAL del contrato)
    4. fecha_inicio (DD/MM/AAAA)
    5. fecha_terminacion (DD/MM/AAAA)
    6. nombre_contratista (Nombre completo)
    7. empresa_quipu (número, ej. 4013)
    8. parcial_no (consecutivo del pago actual, ej. 2)
    9. informe_entregado (bool)
    10. clave_planilla (10 dígitos de la planilla PILA)
    11. fecha_pago_ss (Busca la fecha de 'Pago' real, suele ser la segunda en las tablas de planilla).
    12. periodo_ss (Año-Mes del aporte, ej. 2026-02)

    CRÍTICO: Devuelve SOLO JSON puro.
    TEXTO: {text[:12000]}
    """

    try:
        if provider == "Groq":
            client = Groq(api_key=api_key)
        else: # OpenRouter
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

        for trial in range(2):
            try:
                params = {"model": model, "messages": [{"role": "user", "content": prompt}]}
                if provider == "Groq": params["response_format"] = {"type": "json_object"}
                
                response = client.chat.completions.create(**params)
                content = response.choices[0].message.content
                if "```json" in content: content = content.split("```json")[1].split("```")[0]
                elif "```" in content: content = content.split("```")[1].split("```")[0]
                return json.loads(content)
            except: time.sleep(4)
        return {"error": "Timeout"}
    except Exception as e: return {"error": str(e)}

# --- BARRA LATERAL ---
st.sidebar.title("🤖 Auditoría Multi-IA")
ai_provider = st.sidebar.selectbox("Proveedor", ["OpenRouter", "Groq"])

if ai_provider == "Groq":
    available_models = {"Súper-Auditor (120B)": "openai/gpt-oss-120b"}
    default_key = ""
else:
    tipo_filtro = st.sidebar.radio("Tipo de Modelos", ["Poderosos (SOTA)", "Versiones Gratis"])
    if tipo_filtro == "Poderosos (SOTA)":
        available_models = {
            "DeepSeek V3": "deepseek/deepseek-chat",
            "Gemini 2.0 Flash Lite (Paid)": "google/gemini-2.0-flash-lite-001"
        }
    else:
        available_models = {
            "GPT-OSS 120B (Free)": "openai/gpt-oss-120b:free",
            "Qwen 3.6 Plus": "qwen/qwen3.6-plus:free"
        }
    default_key = ""

selected_model_id = available_models[st.sidebar.selectbox("Modelo", list(available_models.keys()))]
user_api_key = st.sidebar.text_input(f"API Key {ai_provider}", value=default_key, type="password")

# --- UI PRINCIPAL ---
st.title("🛡️ Validador de Pagos - UNAL")
st.markdown("### Auditoría de Triple Cruce (Lógica Profunda)")

with st.expander("📖 Guía de Preparación de Auditoría", expanded=True):
    st.info("""
    Para que el **Súper-Auditor de 120B** funcione correctamente, asegúrate de seguir estas reglas:
    
    1.  **📄 Contrato (PDF)**: Debe ser el archivo original del contrato u orden (OSE/CPS). De aquí la IA extraerá el número oficial y la vigencia.
    2.  **📋 Formato 4013 (PDF)**: 
        *   **Composición**: Este archivo es la unión (PDF) de:
            1. El excel `U-FT-12.010.069_Certificacion_determinacion_cedular_Rentas_de_Trabajo_V.6.1_VF` debidamente diligenciado.
            2. El comprobante de pago de Salud, Pensión y ARL.
            3. El certificado de la ARL.
        *   **Regla de Oro**: La unión de estos archivos debe llamarse exactamente **`4013AnexosOSE[Número contrato].pdf`** (Ejemplo: `4013AnexosOSE14.pdf`).
        *   Asegúrate de que la tabla de fechas sea legible y contenga la columna de **'Pago'**.
    3.  **📝 Constancia (Docx)**: Debe ser el documento de cumplimiento en Word. El sistema verificará que el número de contrato y el periodo coincidan con los PDFs.
    
    *💡 El sistema realizará un **Triple Cruce** para asegurar que no haya discrepancias entre los tres archivos antes de que los radiques.*
    """)

c1, c2, c3 = st.columns(3)
with c1: f_contrato = st.file_uploader("1. Contrato", type=["pdf"])
with c2: f_4013 = st.file_uploader("2. Formato 4013", type=["pdf"])
with c3: f_constancia = st.file_uploader("3. Constancia", type=["docx"])

if st.button("🚀 Ejecutar Auditoría de Triple Cruce"):
    if not (f_contrato and f_4013 and f_constancia):
        st.error("⚠️ Faltan documentos.")
    else:
        with st.spinner("Ejecutando Triple Cruce..."):
            # 1. Leer Textos
            texts = {
                "contrato": extract_text_from_pdf(f_contrato),
                "4013": extract_text_from_pdf(f_4013),
                "constancia": extract_text_from_docx(f_constancia)
            }
            
            # 2. Análisis por IA
            extracted = {}
            for doc in ["contrato", "4013", "constancia"]:
                extracted[doc] = extract_data_with_ai(texts[doc], doc, selected_model_id, user_api_key, ai_provider)
            
            # 3. Validación de Negocio (Archivo)
            num_c = str(extracted["contrato"].get("numero_contrato") or "")
            expected_fn = f"4013AnexosOSE{num_c}"
            if actual_fn := f_4013.name.replace(".pdf", "").replace(" ", "") != expected_fn:
                st.error(f"❌ Error Nombre Archivo: Se esperaba '{expected_fn}.pdf'")

            # 4. Ficha Administrativa
            st.divider()
            st.subheader("📋 Ficha Administrativa de Control")
            admin_data = [
                ("Nombre Contratista", extracted["contrato"].get("nombre_contratista"), extracted["4013"].get("nombre_contratista"), extracted["constancia"].get("nombre_contratista")),
                ("N° Orden", num_c, extracted["4013"].get("numero_contrato"), extracted["constancia"].get("numero_contrato")),
                ("Quipu", "4013", extracted["4013"].get("empresa_quipu"), extracted["constancia"].get("empresa_quipu")),
                ("Valor Total", normalize_money(extracted["contrato"].get("valor_total")), normalize_money(extracted["4013"].get("valor_total")), "-"),
                ("F. Inicio", normalize_date(extracted["contrato"].get("fecha_inicio")), normalize_date(extracted["4013"].get("fecha_inicio")), "-")
            ]
            df = pd.DataFrame(admin_data, columns=["Atributo", "Contrato", "4013", "Constancia"]).astype(str)
            
            def styler(row):
                vals = [v.strip().lower() for v in [row.iloc[1], row.iloc[2], row.iloc[3]] if v != "-"]
                color = "#004d00" if len(set(vals)) <= 1 else "#800000"
                return [f"background-color: {color}; color: white"] * 4

            st.table(df.style.apply(styler, axis=1))

            # 5. Validación Pagos
            st.divider()
            st.subheader("💰 Validación de Seguridad Social")
            v1, v2, v3 = st.columns(3)
            
            with v1:
                st.write("**Planilla PILA**")
                pilla = str(extracted["4013"].get("clave_planilla") or "")
                if pilla and pilla in texts["constancia"].replace(" ", ""):
                    st.success(f"Planilla {pilla} OK")
                else: st.error(f"Planilla {pilla} no hallada")
            
            with v2:
                st.write("**Fecha Pago**")
                f4 = normalize_date(extracted["4013"].get("fecha_pago_ss"))
                fw = normalize_date(extracted["constancia"].get("fecha_pago_ss"))
                if f4 != "-" and f4 == fw: st.success(f"Fecha {f4} OK")
                else: st.error(f"Error: {f4} vs {fw}")

            with v3:
                st.write("**Parcial y Reporte**")
                st.success(f"Pago Parcial No. {extracted['constancia'].get('parcial_no')}")
                if extracted["constancia"].get("informe_entregado"): st.success("Informe Verificado")

            with st.expander("🔍 JSON Crudo"): st.json(extracted)
