# 🛡️ Validador de Pagos UNAL - Súper Auditor Administrativo

Esta aplicación automatiza la auditoría y validación de documentos para la radicación de pagos mensuales de contratistas en el Centro de Prototipado de la Universidad Nacional de Colombia. Utiliza inteligencia artificial de alta potencia (**Groq GPT-OSS 120B**) para realizar un triple cruce de datos entre contratos, formatos 4013 y constancias de cumplimiento.

## 🚀 Características Principales

- **Triple Cruce Administrativo**: Compara automáticamente el Número de Orden, Nombre del Contratista y Empresa Quipu en los tres documentos obligatorios.
- **Auditoría de Seguridad Social**: Valida el número de planilla PILA, la fecha real de pago (ignorando la fecha límite) y el periodo de aporte.
- **Semáforo de Cumplimiento**: Tabla visual que resalta en rojo cualquier discrepancia entre los documentos para evitar devoluciones del pago.
- **Cálculo de Consecutivo**: Determina automáticamente el número de pago parcial basado en la fecha de inicio del contrato y el mes actual.
- **Validación de Nomenclatura**: Verifica que los archivos PDF sigan el formato de nombre oficial exigido por la universidad (ej. `4013AnexosOSE14.pdf`).

## 🛠️ Requisitos Técnicos

- **Python 3.9+**
- **Streamlit**
- **Groq API Key** (Configurada para el modelo `openai/gpt-oss-120b`)
- Librerías: `pypdf`, `python-docx`, `pandas`, `groq`

## 📦 Instalación y Uso

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/validador-pagos-unal.git
   cd validador-pagos-unal
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecutar la aplicación:
   ```bash
   streamlit run app.py
   ```

## 📋 Estructura de Captura

La IA ha sido entrenada para reconocer las particularidades de los documentos de la UNAL, incluyendo:
- Lectura de tablas complejas en Word y PDF.
- Distinción entre fecha de "Límite" y "Pago" en el formato 4013.
- Normalización de nombres de contratistas y montos monetarios.

---
**Desarrollado para el Centro de Prototipado - Universidad Nacional de Colombia.**
