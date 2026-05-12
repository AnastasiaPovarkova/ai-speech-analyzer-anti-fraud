import streamlit as st
import os
import json
from src.transcriber import transcribe_audio
from src.ai_analyzer import analyze_speech

# Настройка страницы
st.set_page_config(page_title="Anti-Fraud AI Analyzer", page_icon="🛡️", layout="wide")

# Кастомные стили для карточек
st.markdown("""
    <style>
    .report-card {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .stMetric {
        background-color: rgba(28, 131, 225, 0.1);
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Anti-Fraud Speech Analyzer")
st.markdown("""
Интеллектуальная система защиты от телефонного мошенничества.
""")

# --- Боковая панель (Sidebar) ---
with st.sidebar:
    st.header("Настройки")
    language = st.selectbox("Язык разговора", ["auto", "ru", "en"], index=0)
    st.divider()
    st.info("💡 **Технологии:**\n- Whisper.cpp (Local)\n- Gemini 3.1 Flash Lite")
    if st.button("Очистить кэш"):
        st.cache_data.clear()

# --- Основной интерфейс ---
uploaded_file = st.file_uploader("Загрузите аудиофайл для проверки", type=['m4a', 'mp3', 'wav'])

if uploaded_file is not None:
    os.makedirs("data/samples", exist_ok=True)
    temp_path = os.path.join("data/samples", uploaded_file.name)
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.audio(uploaded_file, format='audio/wav')

    if st.button("🚀 Запустить глубокий анализ", use_container_width=True):
        with st.spinner("🕵️‍♂️ Идет расшифровка и поиск признаков мошенничества..."):
            # 1. Получаем текст через Whisper
            text_result = transcribe_audio(temp_path, language=language)
            
            if text_result:
                # 2. Получаем анализ через Gemini
                analysis = analyze_speech(text_result)
                
                st.success("Анализ завершен!")
                
                # Отображение результатов
                col_text, col_res = st.columns([1, 1.2])
                
                with col_text:
                    st.subheader("📝 Распознанный текст")
                    st.text_area("Whisper Transcript:", value=text_result, height=400)
                
                with col_res:
                    st.subheader("🧠 Вердикт системы")
                    
                    if "error" in analysis:
                        st.error(f"Ошибка ИИ: {analysis['error']}")
                    else:
                        # Динамический выбор цвета в зависимости от вердикта
                        verdict = analysis.get("verdict", "НЕИЗВЕСТНО")
                        score = analysis.get("confidence_score", 0)
                        
                        v_color = "red" if verdict == "ОПАСНО" else "orange" if verdict == "ПОДОЗРИТЕЛЬНО" else "green"
                        
                        # Метрики
                        m1, m2 = st.columns(2)
                        m1.metric("Вердикт", verdict, delta=None)
                        m2.metric("Уверенность ИI", f"{score}%")
                        
                        # Блок анализа
                        if verdict == "ОПАСНО":
                            st.error(f"**Анализ:** {analysis.get('analysis')}")
                        elif verdict == "ПОДОЗРИТЕЛЬНО":
                            st.warning(f"**Анализ:** {analysis.get('analysis')}")
                        else:
                            st.success(f"**Анализ:** {analysis.get('analysis')}")
                        
                        # Триггеры
                        st.markdown("### 🎯 Ключевые триггеры")
                        for t in analysis.get("triggers", []):
                            st.markdown(f"- `{t}`")
                        
                        # Рекомендация
                        st.info(f"💡 **Рекомендация:** {analysis.get('recommendation')}")
            else:
                st.error("Не удалось получить текст из аудиофайла.")

st.divider()
st.caption("AI Speech Analyzer v1.0 | Разработано для защиты пользователей от социальной инженерии.")