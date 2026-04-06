# 🛡️ Validador de Pagos - Centro de Prototipado UNAL

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://validador-pagos-unal.streamlit.app/)

Esta aplicación ha sido diseñada para automatizar y agilizar el proceso de auditoría de pagos para contratistas del **Centro de Prototipado de la Universidad Nacional de Colombia**. Utiliza inteligencia artificial avanzada (LLM) para realizar un "Triple Cruce" de información entre contratos, formatos 4013 y constancias de cumplimiento.

---

## 🚀 Características

-   **Auditoría Inteligente**: Extracción automática de datos de PDFs y documentos Word.
-   **Triple Cruce**: Validación de coherencia entre el Contrato, el Formato 4013 y la Constancia de Cumplimiento.
-   **Seguridad**: Procesamiento local de archivos (no se guardan en el servidor).
-   **Interfaz Institucional**: Diseño alineado con la identidad visual del Centro de Prototipado.

---

## 📖 Instrucciones de Preparación (4013)

Para garantizar una validación exitosa, el archivo del **Formato 4013** debe prepararse de la siguiente manera:

1.  **Unión de Documentos**: Debe ser un único PDF que contenga:
    -   Excel de Certificación de Rentas de Trabajo (V.6.1_VF) diligenciado.
    -   Comprobantes de pago de Seguridad Social (Salud, Pensión, ARL).
    -   Certificado de ARL vigente.
2.  **Nombre del Archivo**: El PDF resultante debe llamarse:  
    `4013AnexosOSE[NÚMERO_DE_CONTRATO].pdf`  
    *Ejemplo: 4013AnexosOSE401788.pdf*

---

## 🛠️ Instalación y Uso Local

### Requisitos Previos
-   Python 3.8+
-   Una API Key de [Groq](https://console.groq.com/) (Gratuita o de pago).

### Pasos
1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/tu-usuario/validador-pagos-app.git
    cd validador-pagos-app
    ```

2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ejecutar la aplicación**:
    ```bash
    streamlit run app.py
    ```

4.  **Configuración**:
    -   Ingresa tu **Groq API Key** en la barra lateral.
    -   Sube los documentos solicitados siguiendo las instrucciones en pantalla.

---

## 🛡️ Privacidad y Seguridad
Los documentos se procesan en memoria y no se almacenan de forma persistente. La API Key de Groq se maneja únicamente durante la sesión activa del usuario.

## 🏛️ Créditos
Desarrollado para el **Centro de Prototipado**, UNAL Sede Manizales.
