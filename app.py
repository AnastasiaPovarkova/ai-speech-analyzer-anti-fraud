import streamlit as st
import os
from datetime import datetime
from src.transcriber import transcribe_audio
from src.ai_analyzer import analyze_speech
from src.database import init_db, save_result, get_history

# Инициализация БД
init_db()

st.set_page_config(page_title="Anti-Fraud AI Analyzer", page_icon="🛡️", layout="wide")

# Кастомный CSS для красоты
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

# Создаем вкладки
tab1, tab2, tab3 = st.tabs(["📁 Загрузить файл", "🎙️ Записать с микрофона", "📜 История проверок"])

# Функция для отображения логики анализа (чтобы не дублировать код)
def run_analysis_ui(audio_path):
    if audio_path:
        st.divider()
        if st.button("🚀 Запустить глубокий анализ", use_container_width=True):
            with st.spinner("🕵️‍♂️ Идет расшифровка и поиск признаков мошенничества..."):
                text_result = transcribe_audio(audio_path, language=language)
                
                if text_result:
                    analysis = analyze_speech(text_result)
                    
                    # Сохраняем в базу (теперь с уникальным именем файла)
                    save_result(os.path.basename(audio_path), text_result, analysis)
                    
                    st.success("Анализ завершен!")
                    
                    col_text, col_res = st.columns([1, 1.2])
                    with col_text:
                        st.subheader("📝 Распознанный текст")
                        st.text_area("Результат:", value=text_result, height=300)
                    
                    with col_res:
                        st.subheader("🧠 Вердикт системы")
                        verdict = analysis.get("verdict", "НЕИЗВЕСТНО")
                        st.metric("Вердикт", verdict, delta=f"{analysis.get('confidence_score')}%")
                        st.info(f"💡 {analysis.get('recommendation')}")
                        
                        with st.expander("Посмотреть детали анализа"):
                            st.write(analysis.get("analysis"))
                            st.write("**Триггеры:**", ", ".join(analysis.get("triggers", [])))

# --- Вкладка 1: Загрузка ---
with tab1:
    uploaded_file = st.file_uploader("Выберите аудиофайл", type=['m4a', 'mp3', 'wav'])
    if uploaded_file:
        os.makedirs("data/samples", exist_ok=True)
        path = os.path.join("data/samples", uploaded_file.name)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.audio(path)
        run_analysis_ui(path) # Кнопка анализа появится только здесь

# --- Вкладка 2: Диктофон ---
with tab2:
    st.write("Запишите подозрительный разговор:")
    audio_value = st.audio_input("Микрофон")
    
    if audio_value:
        os.makedirs("data/samples", exist_ok=True)
        # Генерируем уникальное имя файла с таймстампом
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rec_path = os.path.join("data/samples", f"rec_{timestamp}.wav")
        
        with open(rec_path, "wb") as f:
            f.write(audio_value.getbuffer())
        
        st.success(f"Запись сохранена как {os.path.basename(rec_path)}")
        run_analysis_ui(rec_path) # Кнопка анализа появится только здесь

# --- Вкладка 3: История ---
with tab3:
    st.subheader("📜 Журнал прошлых проверок")
    history = get_history()
    if history:
        for item in history:
            # item[1] - время, item[2] - файл, item[4] - вердикт
            with st.expander(f"🕒 {item[1]} | {item[2]} — {item[4]}"):
                st.write(f"**Текст:** {item[3]}")
                st.write(f"**Рекомендация:** {item[6]}")
    else:
        st.info("История пуста.")

st.divider()
st.caption("AI Speech Analyzer v1.4 | SQLite Storage Enabled")