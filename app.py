import streamlit as st
import os
import json
from src.transcriber import transcribe_audio
from src.ai_analyzer import analyze_speech

# Настройка страницы
st.set_page_config(page_title="Anti-Fraud AI Analyzer", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: rgba(28, 131, 225, 0.1); padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Anti-Fraud Speech Analyzer")

# --- Боковая панель ---
with st.sidebar:
    st.header("Настройки")
    language = st.selectbox("Язык разговора", ["auto", "ru", "en"], index=0)
    st.divider()
    st.info("💡 **Технологии:**\n- Whisper.cpp (Local)\n- Gemini 3.1 Flash Lite")
    
    # Кнопка сброса интерфейса
    if st.button("🔄 Очистить кэш", use_container_width=True):
        # Очищаем кэш данных (результаты работы функций)
        st.cache_data.clear()
        # Перезагружаем страницу, чтобы очистить все input-виджеты и переменные
        st.rerun()

# --- Основной интерфейс: Выбор метода ввода ---
tab1, tab2 = st.tabs(["📁 Загрузить файл", "🎙️ Записать с микрофона"])

audio_to_process = None

with tab1:
    uploaded_file = st.file_uploader("Выберите аудиофайл", type=['m4a', 'mp3', 'wav'])
    if uploaded_file:
        os.makedirs("data/samples", exist_ok=True)
        audio_to_process = os.path.join("data/samples", uploaded_file.name)
        with open(audio_to_process, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.audio(uploaded_file)

with tab2:
    st.write("Используйте встроенный микрофон для записи:")
    audio_value = st.audio_input("Записать разговор")
    
    if audio_value:
        os.makedirs("data/samples", exist_ok=True)
        # Записываем в файл, но теперь кнопка сброса его не удалит
        audio_to_process = os.path.join("data/samples", "recorded_audio.wav")
        with open(audio_to_process, "wb") as f:
            f.write(audio_value.getbuffer())
        st.success("Голос успешно записан!")

# --- Логика анализа ---
if audio_to_process:
    if st.button("🚀 Запустить глубокий анализ", use_container_width=True):
        with st.spinner("🕵️‍♂️ Идет расшифровка и поиск признаков мошенничества..."):
            text_result = transcribe_audio(audio_to_process, language=language)
            
            if text_result:
                analysis = analyze_speech(text_result)
                st.success("Анализ завершен!")
                
                col_text, col_res = st.columns([1, 1.2])
                with col_text:
                    st.subheader("📝 Распознанный текст")
                    st.text_area("Результат расшифровки:", value=text_result, height=400)
                
                with col_res:
                    st.subheader("🧠 Вердикт системы")
                    if "error" in analysis:
                        st.error(f"Ошибка ИИ: {analysis['error']}")
                    else:
                        verdict = analysis.get("verdict", "НЕИЗВЕСТНО")
                        score = analysis.get("confidence_score", 0)
                        
                        m1, m2 = st.columns(2)
                        m1.metric("Вердикт", verdict)
                        m2.metric("Уверенность ИИ", f"{score}%")
                        
                        if verdict == "ОПАСНО":
                            st.error(f"**Анализ:** {analysis.get('analysis')}")
                        elif verdict == "ПОДОЗРИТЕЛЬНО":
                            st.warning(f"**Анализ:** {analysis.get('analysis')}")
                        else:
                            st.success(f"**Анализ:** {analysis.get('analysis')}")
                        
                        st.markdown("### 🎯 Ключевые триггеры")
                        for t in analysis.get("triggers", []):
                            st.markdown(f"- `{t}`")
                        
                        st.info(f"💡 **Рекомендация:** {analysis.get('recommendation')}")
            else:
                st.error("Не удалось получить текст.")

st.divider()
st.caption("AI Speech Analyzer v1.3 | Кнопка быстрого сброса UI")