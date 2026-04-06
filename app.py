import streamlit as st
import pypdf
from docx import Document
import json
import re
import io
import time
from datetime import datetime
from groq import Groq

# Configuración de la página
st.set_page_config(page_title="Validador de Pagos UNAL - Centro de Prototipado", layout="wide")

# Estilos CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stAlert { border-radius: 10px; }
    .card { background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Validador de Pagos Mensuales")
st.subheader("Centro de Prototipado - Universidad Nacional de Colombia")

# --- VARIABLES GLOBALES / CONFIG ---
# Deja la API Key vacía para que cada usuario ponga la suya
DEFAULT_GROQ_KEY = ""
DEFAULT_MODEL = "openai/gpt-oss-120b"

MESES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04", 
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08", 
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
}

# Sidebar ultra-simplificado
with st.sidebar:
    st.header("⚙️ Configuración")
    st.info(f"🚀 Motor: **GPT-OSS 120B**")
    # Mostrar la API Key precargada
    api_key = st.text_input("Groq API Key", value=DEFAULT_GROQ_KEY, type="password")
    model_pref = DEFAULT_MODEL
    st.divider()
    st.caption("Esta aplicación está bloqueada al motor GPT-OSS 120B de Groq por su máxima precisión en auditorías.")

# --- UTILERÍAS ---

def normalize_money(val):
    if not val: return 0
    return int(re.sub(r'\D', '', str(val)))

def normalize_date(date_str):
    if not date_str: return None
    clean = re.sub(r'[^\d/]', '', str(date_str))
    try: return datetime.strptime(clean, "%d/%m/%Y").strftime("%Y/%m/%d")
    except: pass
    try: return datetime.strptime(clean, "%Y/%m/%d").strftime("%Y/%m/%d")
    except: pass
    return clean

# --- FUNCIONES DE EXTRACCIÓN ---

def extract_text_from_pdf(file):
    reader = pypdf.PdfReader(file)
    return " ".join([p.extract_text() for p in reader.pages if p.extract_text()])

def extract_text_from_docx(file):
    try:
        doc = Document(file)
        full_text = []
        for para in doc.paragraphs: full_text.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells: full_text.append(cell.text)
        return "\n".join(full_text)
    except: return ""

def extract_data_with_groq(text, doc_type, api_key, model):
    client = Groq(api_key=api_key)
    # Dar contexto del tipo de documento para guiar la extracción
    contexto = {
        "contrato": "Este es el Contrato principal (PDF). El número de orden suele estar en un código largo como OSE-14-4013...",
        "4013": "Este es el Formato 4013 (PDF). El número de contrato suele estar en la parte superior.",
        "constancia": "Esta es la Constancia de Cumplimiento (Word). Busca donde diga 'Contrato No.' o similares."
    }.get(doc_type, "")

    prompt = f"""
    Eres un experto auditor de la UNAL. Analiza este documento ({doc_type}). 
    {contexto}
    
    Extrae en JSON puro:
    1. numero_contrato (Busca el número oficial, ej. '14'. Si ves códigos largos como 'OSE-14-4013-2026Sol401788', EXTRAE SOLO EL '14'. No extraigas códigos de 6 dígitos).
    2. riesgo_arl (solo dígito 1-5)
    3. valor_contrato (monto mensual o IBC)
    4. fecha_inicio (DD/MM/AAAA)
    5. fecha_terminacion (DD/MM/AAAA)
    6. valor_total (monto TOTAL del contrato antes de IVA)
    7. nombre_contratista (Nombre completo)
    8. tipo_orden (ej. OSE o CPS)
    9. empresa_quipu (número de empresa, ej. 4013)
    10. parcial_no (consecutivo del pago actual, ej. 2)
    11. informe_entregado (bool)
    12. clave_planilla (10 dígitos de la planilla PILA)
    13. periodo_ss (Año y Mes del aporte, ej. 2026-02)
    14. fecha_pago_ss (Busca en la sección 'Fecha'. Habrá dos fechas: 'Límite' y 'Pago'. La de 'Límite' suele ser del mes siguiente (ej. Marzo), la de 'Pago' es la real del trámite (ej. Febrero). TOMA SIEMPRE LA QUE ESTÁ BAJO 'PAGO' O LA SEGUNDA QUE APAREZCA EN ESA TABLA).

    CRÍTICO: 
    - En el texto verás algo como: 'Límite Pago 06/03/2026 27/02/2026'. El primer valor es Límite, el SEGUNDO es Pago. EXTRAE EL SEGUNDO.
    - Devuelve solo JSON puro.
    TEXTO: {text[:10000]}
    """
    for trial in range(3):
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                response_format={"type": "json_object"}
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            if "429" in str(e) and trial < 2:
                time.sleep((trial + 1) * 15)
            else: raise e

# --- UI PRINCIPAL ---
st.header("📂 Carga de Documentos")

with st.expander("📖 Guía de Preparación de Documentos (LEER PRIMERO)", expanded=True):
    st.markdown("""
    Para que el **Súper-Auditor de 120B** funcione correctamente, asegúrate de seguir estas reglas:
    
    1.  **📄 Contrato (PDF)**: Debe ser el archivo original del contrato u orden (OSE/CPS). De aquí la IA extraerá el número oficial y la vigencia.
    2.  **📋 Formato 4013 (PDF)**: 
        *   **Composición**: Este archivo es la unión (PDF) de:
            1. El excel `U-FT-12.010.069_Certificacion_determinacion_cedular_Rentas_de_Trabajo_V.6.1_VF` debidamente diligenciado.
            2. El comprobante de pago de Salud, Pensión y ARL.
            3. El certificado de la ARL.
        *   **Regla de Oro**: La unión de estos archivos debe llamarse exactamente **`4013AnexosOSE[Número].pdf`** (Ejemplo: `4013AnexosOSE14.pdf`).
        *   Asegúrate de que la tabla de fechas sea legible y contenga la columna de **'Pago'**.
    3.  **📝 Constancia (Docx)**: Debe ser el documento de cumplimiento en Word. El sistema verificará que el número de contrato y el periodo coincidan con los PDFs.
    
    *💡 El sistema realizará un **Triple Cruce** para asegurar que no haya discrepancias entre los tres archivos antes de que los radiques.*
    """)

c1, c2, c3 = st.columns(3)
with c1: f_contrato = st.file_uploader("1. Contrato (PDF)", type=["pdf"])
with c2: f_4013 = st.file_uploader("2. Formato 4013 (PDF)", type=["pdf"])
with c3: f_constancia = st.file_uploader("3. Constancia (DOCX)", type=["docx"])

if st.button("🚀 Iniciar Súper-Auditoría"):
    if not (f_contrato and f_4013 and f_constancia):
        st.warning("⚠️ Sube los 3 archivos obligatorios para auditar.")
    else:
        with st.spinner("Ejecutando Súper-Auditoría con GPT-OSS 120B..."):
            try:
                # 1. Leer texto
                raw_texts = {
                    "contrato": extract_text_from_pdf(f_contrato),
                    "4013": extract_text_from_pdf(f_4013),
                    "constancia": extract_text_from_docx(f_constancia)
                }
                
                # 2. Extraer Datos
                extracted = {}
                for key, text in raw_texts.items():
                    try:
                        extracted[key] = extract_data_with_groq(text, key, api_key, model_pref)
                    except:
                        extracted[key] = {}

                # --- VALIDACIÓN NOMBRE DE ARCHIVO ---
                num_c = str(extracted["contrato"].get("numero_contrato") or "")
                expected = f"4013AnexosOSE{num_c}"
                name_clean = f_4013.name.replace(".pdf", "").replace(" ", "")
                if name_clean != expected: st.error(f"❌ Error Nombre Archivo: Se esperaba '{expected}.pdf'")

                # --- FICHA ADMINISTRATIVA ---
                st.divider()
                st.subheader("📋 Ficha Administrativa de Control (Triple Cruce)")
                
                admin_rows = [
                    ("Nombre Contratista", extracted["contrato"].get("nombre_contratista"), extracted["4013"].get("nombre_contratista"), extracted["constancia"].get("nombre_contratista")),
                    ("Número de Orden/Contrato", num_c, extracted["4013"].get("numero_contrato"), extracted["constancia"].get("numero_contrato")),
                    ("Empresa en QUIPU", "4013", extracted["4013"].get("empresa_quipu"), extracted["constancia"].get("empresa_quipu")),
                    ("Tipo de Orden", extracted["contrato"].get("tipo_orden"), extracted["4013"].get("tipo_orden"), "OSE"),
                    ("Valor Total", normalize_money(extracted["contrato"].get("valor_total")), normalize_money(extracted["4013"].get("valor_total")), "-"),
                    ("F. Inicio", normalize_date(extracted["contrato"].get("fecha_inicio")), normalize_date(extracted["4013"].get("fecha_inicio")), "-"),
                    ("F. Terminación", normalize_date(extracted["contrato"].get("fecha_terminacion")), normalize_date(extracted["4013"].get("fecha_terminacion")), "-"),
                ]

                import pandas as pd
                df_admin = pd.DataFrame(admin_rows, columns=["Campo", "Contrato (PDF)", "Formato 4013", "Constancia (Word)"]).astype(str)
                
                def color_rows(row):
                    # Usar iloc para evitar FutureWarnings
                    v1 = str(row.iloc[1]).strip().lower()
                    v2 = str(row.iloc[2]).strip().lower()
                    v3 = str(row.iloc[3]).strip().lower()
                    
                    vals = [v for v in [v1, v2, v3] if v != "-"]
                    if len(set(vals)) <= 1: return ["background-color: #d4edda"] * 4
                    return ["background-color: #f8d7da"] * 4

                st.table(df_admin.style.apply(color_rows, axis=1))

                # --- VALIDACIÓN DE PAGO ---
                st.divider()
                st.subheader("💰 Validación de Pago Actual")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Consecutivo**")
                    p_det = extracted["constancia"].get("parcial_no")
                    try: 
                        s_m = int(str(extracted["contrato"].get("fecha_inicio") or "1/1").split("/")[1])
                        c_p = (3 - s_m) + 1
                        if int(str(extracted["contrato"].get("fecha_inicio") or "1").split("/")[0]) > 20: c_p -= 1
                    except: c_p = 2
                    if str(p_det) == str(c_p): st.success(f"Pago No. {p_det} OK")
                    else: st.error(f"Error: Pago {c_p}")

                with col2:
                    st.write("**Informes**")
                    p_det_val = int(p_det or 0)
                    if p_det_val % 3 == 0:
                        if extracted["constancia"].get("informe_entregado"): st.success("Informe OK")
                        else: st.error("¡FALTA INFORME!")
                    else: st.info("No requiere informe")

                with col3:
                    st.write("**Seguridad Social**")
                    p_4013 = re.sub(r'\D', '', str(extracted["4013"].get("clave_planilla") or ""))
                    if len(p_4013) < 10:
                        fb = re.findall(r'(9\d{9})', raw_texts["4013"])
                        if fb: p_4013 = fb[0]
                    
                    if p_4013 and p_4013 in raw_texts["constancia"].replace(" ", ""): st.success(f"Planilla {p_4013} OK")
                    else: st.error(f"Error Planilla {p_4013}")
                    
                    # Comparación de Periodo y Fecha
                    f_4 = normalize_date(extracted["4013"].get("fecha_pago_ss"))
                    f_w = normalize_date(extracted["constancia"].get("fecha_pago_ss"))
                    if f_4 and f_w and f_4 == f_w: st.success("Fecha Pago OK")
                    else: st.error(f"Fecha Dif: {f_4} vs {f_w}")
                    
                    # Periodo
                    per_4013 = extracted["4013"].get("periodo_ss")
                    found_month = False
                    if per_4013:
                        t_word = raw_texts["constancia"].lower()
                        if per_4013 in t_word: found_month = True
                        elif "-" in per_4013:
                            m_num = per_4013.split("-")[1]
                            for m_name, m_code in MESES.items():
                                if m_code == m_num and m_name in t_word: found_month = True
                    if found_month: st.success(f"Periodo OK")
                    else: st.error(f"Periodo {per_4013} no detectado")

                with st.expander("🔍 Ver Datos JSON"): st.json(extracted)

            except Exception as e:
                st.error(f"❌ Error Crítico: {e}")

st.caption("Fijado en GPT-OSS 120B - Máxima Precisión Centro de Prototipado")
