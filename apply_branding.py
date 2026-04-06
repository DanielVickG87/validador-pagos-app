import base64
import re
import os

id_path = r'd:/Documents/skills antigravity/centro de prototipado/Identificador_CentroPrototipado_VersiónPrincipal.png'
bg_path = r'd:/Documents/skills antigravity/centro de prototipado/RECURSO-GRÁFICO-CENTRO-DE-PROTOTIPADO.png'
app_path = r'd:/Documents/skills antigravity/validador-pagos-app/app.py'

if not os.path.exists(id_path) or not os.path.exists(bg_path):
    print("Error: Brand assets not found")
    exit(1)

id_b64 = base64.b64encode(open(id_path, 'rb').read()).decode()
bg_b64 = base64.b64encode(open(bg_path, 'rb').read()).decode()

with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

# CSS Branded
css_content = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bg_b64}");
        background-size: cover;
        background-attachment: fixed;
    }}
    .stApp > div:first-child {{
        background-color: rgba(255, 255, 255, 0.88);
    }}
    h1, h2, h3, h4 {{ color: #003366 !important; font-family: 'Outfit', sans-serif; }}
    .stButton>button {{
        background-color: #003366 !important;
        color: white !important;
        border-radius: 25px !important;
        padding: 0.5rem 2rem !important;
        font-weight: 600 !important;
    }}
    .stSidebar {{
        background-color: #f0f5ff !important;
        border-right: 1px solid #003366;
    }}
    </style>
"""

logo_code = f'st.sidebar.image("data:image/png;base64,{id_b64}", use_container_width=True)'

# Replacement logic to inject at the right place (after imports)
if 'st.markdown(\'\'\' <style>' in content:
    # Remove old style to avoid duplication
    content = re.sub(r"st\.markdown\(''' <style>.*?</style> ''', unsafe_allow_html=True\)", "", content, flags=re.DOTALL)

injection = f"st.markdown('{css_content}', unsafe_allow_html=True)\n{logo_code}\n"
content = content.replace('st.title("🛡️ Validador de Pagos Mensuales")', injection + 'st.title("🛡️ Validador de Pagos Mensuales")')

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Branding Applied successfully to app.py")
