import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import glob
import cv2
import numpy as np
import pytesseract
from gtts import gTTS
from googletrans import Translator

# ==================== INTERFAZ PRINCIPAL ====================
st.title("TRADUCTOR.")
st.subheader("Escucho lo que quieres traducir.")

image = Image.open('OIG7.jpg')
st.image(image, width=300)

with st.sidebar:
    st.subheader("Traductor.")
    st.write("Presiona el botón y habla lo que quieres traducir. Luego, selecciona el idioma.")

# ==================== RECONOCIMIENTO DE VOZ ====================
st.write("Toca el Botón y habla lo que quieres traducir")

stt_button = Button(label="Escuchar 🎤", width=300, height=50)
stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
"""))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

if result and "GET_TEXT" in result:
    st.write(result.get("GET_TEXT"))
    text = result.get("GET_TEXT")

    # ==================== TRADUCCIÓN Y SÍNTESIS DE VOZ ====================
    translator = Translator()
    os.makedirs("temp", exist_ok=True)

    input_language = st.selectbox("Idioma de Entrada", ["Inglés", "Español", "Bengali", "Coreano", "Mandarín", "Japonés"])
    output_language = st.selectbox("Idioma de Salida", ["Inglés", "Español", "Bengali", "Coreano", "Mandarín", "Japonés"])
    accent = st.selectbox("Selecciona el acento", ["Defecto", "Español", "Reino Unido", "Estados Unidos", "Canadá", "Australia", "Irlanda", "Sudáfrica"])

    lang_codes = {"Inglés": "en", "Español": "es", "Bengali": "bn", "Coreano": "ko", "Mandarín": "zh-cn", "Japonés": "ja"}
    accent_codes = {"Defecto": "com", "Español": "com.mx", "Reino Unido": "co.uk", "Estados Unidos": "com", "Canadá": "ca", "Australia": "com.au", "Irlanda": "ie", "Sudáfrica": "co.za"}

    input_code = lang_codes[input_language]
    output_code = lang_codes[output_language]
    tld = accent_codes[accent]

    def text_to_speech(input_lang, output_lang, text, tld):
        translation = translator.translate(text, src=input_lang, dest=output_lang)
        tts = gTTS(translation.text, lang=output_lang, tld=tld, slow=False)
        file_name = "audio.mp3"
        tts.save(f"temp/{file_name}")
        return file_name, translation.text

    if st.button("Convertir"):
        file_name, translated_text = text_to_speech(input_code, output_code, text, tld)
        st.audio(f"temp/{file_name}", format="audio/mp3")
        st.write("Texto Traducido:", translated_text)

# ==================== RECONOCIMIENTO ÓPTICO DE CARACTERES (OCR) ====================
st.title("Reconocimiento Óptico de Caracteres")
st.subheader("Elige la fuente de la imagen")

use_camera = st.checkbox("Usar Cámara")
uploaded_image = st.file_uploader("Cargar Imagen", type=["png", "jpg"])

if use_camera:
    img_file_buffer = st.camera_input("Captura una imagen")
else:
    img_file_buffer = None

# ==================== PROCESAMIENTO DE IMAGEN ====================
if img_file_buffer or uploaded_image:
    if img_file_buffer:
        bytes_data = img_file_buffer.getvalue()
    else:
        bytes_data = uploaded_image.read()

    img_np = np.frombuffer(bytes_data, np.uint8)
    img_cv = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    text_detected = pytesseract.image_to_string(img_rgb)

    st.write("Texto Detectado:")
    st.write(text_detected)

# ==================== LIMPIEZA AUTOMÁTICA ====================
def remove_old_files(days=7):
    mp3_files = glob.glob("temp/*.mp3")
    now = time.time()
    cutoff = now - (days * 86400)
    
    for f in mp3_files:
        if os.stat(f).st_mtime < cutoff:
            os.remove(f)
            print("Deleted:", f)

remove_old_files()



