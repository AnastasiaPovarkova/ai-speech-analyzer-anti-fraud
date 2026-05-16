import streamlit as st
import os
from datetime import datetime
from src.transcriber import transcribe_audio
from src.ai_analyzer import analyze_speech
from src.database import init_db, save_result, get_history, delete_record

# Инициализация
init_db()

st.set_page_config(page_title="Anti-Fraud AI Analyzer", page_icon="🛡️", layout="wide")

# Стили для компактности
st.markdown("""
    <style>
    .stDownloadButton button { width: 100%; }
    .stButton button { width: 100%; }
    [data-testid="stMetricValue"] { font-size: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Anti-Fraud Speech Analyzer")

with st.sidebar:
    st.header("⚙️ Настройки")
    language = st.selectbox("Язык разговора", ["auto", "ru", "en"])
    
    # Статистика
    history_data = get_history()
    st.divider()
    st.metric("Всего проверок", len(history_data))
    st.metric("Угроз выявлено", len([h for h in history_data if h[4] == "ОПАСНО"]))
    
    if st.button("🔄 Сбросить интерфейс"):
        # Очищаем состояние при сбросе
        for key in ["last_text", "last_analysis", "last_path"]:
            if key in st.session_state: del st.session_state[key]
        st.cache_data.clear()
        st.rerun()

    st.info("💡 **Технологии:**\n- Whisper.cpp (Local)\n- Gemini 3.1 Flash Lite")

tab1, tab2, tab3 = st.tabs(["📁 Загрузить", "🎙️ Диктофон", "📜 История"])

def run_analysis_ui(audio_path):
    if not audio_path:
        return

    # Проверяем, есть ли результат в памяти, чтобы он не пропадал
    if st.session_state.get("last_path") == audio_path:
        render_results_ui(st.session_state["last_text"], st.session_state["last_analysis"])

    if st.button("🚀 Запустить анализ", use_container_width=True):
        with st.spinner("🕵️‍♂️ Идет расшифровка и поиск признаков мошенничества..."):
            text_result = transcribe_audio(audio_path, language=language)
            
            if text_result:
                analysis = analyze_speech(text_result)
                
                # Сохраняем в базу 
                save_result(os.path.basename(audio_path), text_result, analysis)
                
                # Сохраняем в состояние сессии
                st.session_state["last_text"] = text_result
                st.session_state["last_analysis"] = analysis
                st.session_state["last_path"] = audio_path
                
                st.rerun() # Обновляем для синхронизации с историей
            else:
                st.error("Не удалось получить текст.")

def render_results_ui(text, analysis):
    """Отдельная функция для отрисовки результатов (исправляет верстку)"""
    st.success("Анализ завершен!")
    col_text, col_res = st.columns([1, 1.2])
    
    with col_text:
        st.subheader("📝 Распознанный текст")
        st.text_area("Результат:", value=text, height=400)
    
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

            # Кнопка скачивания отчета (ТЕПЕРЬ ВНУТРИ КОЛОНКИ И БЕЗ ОШИБОК)
            report_txt = f"ОТЧЕТ АНАЛИЗА\nВЕРДИКТ: {verdict}\n\nАНАЛИЗ:\n{analysis.get('analysis')}\n\nТЕКСТ:\n{text}"
            st.download_button("📥 Скачать отчет (TXT)", report_txt, "report.txt")

# Вкладки загрузки и записи
with tab1:
    uploaded = st.file_uploader("Файл", type=['wav', 'mp3', 'm4a'])
    if uploaded:
        os.makedirs("data/samples", exist_ok=True)
        path = f"data/samples/{uploaded.name}"
        with open(path, "wb") as f: f.write(uploaded.getbuffer())
        run_analysis_ui(path)

with tab2:
    audio_val = st.audio_input("Микрофон")
    if audio_val:
        os.makedirs("data/samples", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"data/samples/rec_{ts}.wav"
        with open(path, "wb") as f: f.write(audio_val.getbuffer())
        run_analysis_ui(path)

# --- ИСТОРИЯ ---
with tab3:    
    if history_data:
        # 1. СКАЧАТЬ ВСЮ ИСТОРИЮ
        full_report = "ПОЛНЫЙ ОТЧЕТ ПО ВСЕМ ПРОВЕРКАМ\n" + "="*30 + "\n\n"
        for h in history_data:
            full_report += f"[{h[1]}] Файл: {h[2]}\nВЕРДИКТ: {h[4]} ({h[5]}%)\nАНАЛИЗ: {h[6]}\nТЕКСТ: {h[3][:100]}...\n" + "-"*20 + "\n"
        
        st.download_button("📥 Скачать всю историю (TXT)", full_report, "full_history_report.txt")

        # 2. СПИСОК ЗАПИСЕЙ
        search = st.text_input("🔍 Поиск", "").lower()
        
        for item in history_data:
            # Логика поиска 
            if search == "опасно": match = (item[4].lower() == "опасно")
            else: match = search in item[2].lower() or search in item[4].lower()
            
            if match:
                with st.expander(f"🕒 {item[1]} | {item[2]} — {item[4]}"):
                    st.write(f"**Анализ:** {item[6]}")
                    st.write(f"**Текст:** {item[3]}")
                    
                    col1, col2 = st.columns(2)
                    
                    # Индивидуальный отчет
                    report = f"ОТЧЕТ АНАЛИЗА\nДата: {item[1]}\nФайл: {item[2]}\n\nВЕРДИКТ: {item[4]} ({item[5]}%)\n\nАНАЛИЗ:\n{item[6]}\n\nРЕКОМЕНДАЦИЯ:\n{item[7]}\n\nПОЛНЫЙ ТЕКСТ:\n{item[3]}"
                    
                    col1.download_button("📥 Отчет", report, f"report_{item[2]}.txt", key=f"dl_{item[0]}")
                    
                    if col2.button("🗑️ Удалить", key=f"del_{item[0]}"):
                        delete_record(item[0])
                        st.rerun()
    else:
        st.info("История пуста.")