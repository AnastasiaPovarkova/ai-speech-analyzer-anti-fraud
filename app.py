import streamlit as st
import os
import hashlib
from datetime import datetime
from src.transcriber import transcribe_audio
from src.ai_analyzer import analyze_speech
from src.database import init_db, save_result, get_history, delete_record

# Инициализация базы данных
init_db()

st.set_page_config(page_title="Anti-Fraud AI Analyzer", page_icon="🛡️", layout="wide")

# Стили для компактности кнопок и метрик
st.markdown("""
    <style>
    .stDownloadButton button { width: 100%; }
    .stButton button { width: 100%; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Anti-Fraud Speech Analyzer")

with st.sidebar:
    st.header("⚙️ Настройки")
    # Уникальный ключ для выбора языка
    language = st.selectbox("Язык разговора", ["auto", "ru", "en"], key="sb_language")
    
    # Получаем историю для расчета актуальной статистики
    history_data = get_history()
    st.divider()
    
    # Статистика с учетом категорий классификации
    st.metric("Всего проверок", len(history_data))
    st.metric("Критических угроз (Мошенничество)", len([h for h in history_data if h[4] == "МОШЕННИЧЕСТВО"]))
    st.metric("Выявлено спама", len([h for h in history_data if h[4] == "СПАМ"]))
    
    st.info("💡 **Технологии:**\n- Whisper.cpp (Local)\n- Gemini 3.1 Flash Lite\n- SQLite Database")

# Создаем вкладки
tab1, tab2, tab3 = st.tabs(["📁 Загрузить файл", "🎙️ Диктофон", "📜 История проверок"])

def render_results_ui(text, analysis, key):
    """Отрисовывает результаты анализа в раздельные колонки с уникальным ключом для виджетов"""
    st.success("Анализ успешно завершен!")
    col_text, col_res = st.columns([1, 1.2])
    
    with col_text:
        st.subheader("📝 Распознанный текст")
        st.text_area("Результат расшифровки:", value=text, height=400, key=f"text_area_{key}")
    
    with col_res:
        st.subheader("🧠 Вердикт системы")
        if "error" in analysis:
            st.error(f"Ошибка ИИ-анализатора: {analysis['error']}")
        else:
            verdict = analysis.get("verdict", "НЕИЗВЕСТНО")
            score = analysis.get("confidence_score", 0)
        
            m1, m2 = st.columns(2)
            m1.metric("Категория звонка", verdict)
            m2.metric("Уверенность ИИ", f"{score}%")
        
            # Цветовая индикация в зависимости от вердикта
            if verdict == "МОШЕННИЧЕСТВО":
                st.error(f"🚨 **Внимание! Опасность мошенничества:** {analysis.get('analysis')}")
            elif verdict == "СПАМ":
                st.warning(f"☎️ **Спам или реклама:** {analysis.get('analysis')}")
            elif verdict == "ЛИЧНЫЙ ЗВОНОК":
                st.success(f"🤝 **Безопасный звонок:** {analysis.get('analysis')}")
            else:
                st.info(f"🤔 **Анализ:** {analysis.get('analysis')}")
        
            st.markdown("### 🎯 Ключевые триггеры")
            for t in analysis.get("triggers", []):
                st.markdown(f"- `{t}`")
        
            st.info(f"💡 **Рекомендация:** {analysis.get('recommendation')}")

            # Формирование детального отчета для скачивания
            report_txt = (
                f"ОТЧЕТ АНАЛИЗА ЗВОНКА\n"
                f"====================\n"
                f"ВЕРДИКТ: {verdict} ({score}%)\n"
                f"АНАЛИЗ: {analysis.get('analysis')}\n"
                f"РЕКОМЕНДАЦИЯ: {analysis.get('recommendation')}\n\n"
                f"ПОЛНЫЙ ТЕКСТ:\n{text}"
            )
            st.download_button("📥 Скачать этот отчет (TXT)", report_txt, "call_analysis_report.txt", key=f"dl_btn_{key}")

def run_analysis_ui(audio_path, key):
    """Отображает кнопку запуска анализа и обрабатывает процесс транскрибации"""
    if st.button("🚀 Запустить анализ", use_container_width=True, key=f"btn_analyze_{key}"):
        with st.spinner("🕵️‍♂️ Идет расшифровка и поиск признаков мошенничества..."):
            text_result = transcribe_audio(audio_path, language=language)
            
            if text_result:
                analysis = analyze_speech(text_result)
                
                # Сохраняем результаты в базу данных
                save_result(os.path.basename(audio_path), text_result, analysis)
                
                # Запоминаем результаты глобально в сессии
                st.session_state["last_text"] = text_result
                st.session_state["last_analysis"] = analysis
                st.session_state["last_path"] = audio_path
                st.session_state["active_key"] = key
                
                st.rerun() # Перезапускаем страницу для обновления истории
            else:
                st.error("Не удалось распознать речь в аудиофайле.")

# Вкладка 1: Загрузка файлов
with tab1:
    uploaded = st.file_uploader("Выберите аудиофайл", type=['wav', 'mp3', 'm4a'], key="uploader_file")
    if uploaded:
        path = f"data/samples/{uploaded.name}"
        # Записываем файл только если он новый, чтобы не перезатирать диск на каждый rerun
        if not os.path.exists(path):
            os.makedirs("data/samples", exist_ok=True)
            with open(path, "wb") as f: 
                f.write(uploaded.getbuffer())
        
        # Если в этой вкладке уже есть выполненный анализ, показываем его
        if st.session_state.get("last_path") == path and st.session_state.get("active_key") == "upload":
            render_results_ui(st.session_state["last_text"], st.session_state["last_analysis"], "upload")
        else:
            run_analysis_ui(path, key="upload")

# Вкладка 2: Встроенный диктофон
with tab2:
    audio_val = st.audio_input("Записать разговор через микрофон", key="recorder_input")
    if audio_val:
        # Считываем аудио-буфер
        audio_bytes = audio_val.read()
        
        # Получаем SHA256 хэш данных, чтобы безошибочно идентифицировать эту конкретную запись
        current_audio_hash = hashlib.sha256(audio_bytes).hexdigest()
        
        # Если хэш изменился — это действительно новая запись
        if st.session_state.get("last_recorded_hash") != current_audio_hash:
            os.makedirs("data/samples", exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            stable_path = f"data/samples/rec_{ts}.wav"
            
            with open(stable_path, "wb") as f: 
                f.write(audio_bytes)
                
            st.session_state["recorded_path"] = stable_path
            st.session_state["last_recorded_hash"] = current_audio_hash
            
            # При новой записи сбрасываем старый кэш анализа
            if "last_path" in st.session_state:
                del st.session_state["last_path"]
        
        # Отображаем результаты анализа, если они сохранены для ТЕКУЩЕЙ записи микрофона
        if st.session_state.get("last_path") == st.session_state.get("recorded_path") and st.session_state.get("active_key") == "record":
            render_results_ui(st.session_state["last_text"], st.session_state["last_analysis"], "record")
        else:
            # Иначе показываем кнопку для запуска нового анализа
            run_analysis_ui(st.session_state["recorded_path"], key="record")
    else:
        # Если запись удалена пользователем из виджета, чистим стейт
        if "recorded_path" in st.session_state:
            del st.session_state["recorded_path"]
        if "last_recorded_hash" in st.session_state:
            del st.session_state["last_recorded_hash"]

# Вкладка 3: Интерактивная история
with tab3:    
    if history_data:
        full_report = "ПОЛНЫЙ СВОДНЫЙ ОТЧЕТ ПО ВСЕМ ПРОВЕРЕННЫМ ЗВОНКАМ\n" + "="*50 + "\n\n"
        for h in history_data:
            full_report += (
                f"[{h[1]}] Файл: {h[2]}\n"
                f"ВЕРДИКТ: {h[4]} ({h[5]}%)\n"
                f"АНАЛИЗ: {h[6]}\n"
                f"РЕКОМЕНДАЦИЯ: {h[7]}\n"
                f"ТЕКСТ РАЗГОВОРА:\n{h[3]}\n"
                + "-"*40 + "\n"
            )
        
        st.download_button("📥 Скачать всю историю звонков (TXT)", full_report, "all_history_report.txt", key="dl_btn_all_history")
        st.divider()

        search = st.text_input("🔍 Поиск по истории (имя файла или вердикт)", "", key="input_search_history").lower().strip()
        
        for item in history_data:
            item_verdict = item[4].lower() if item[4] else ""
            item_filename = item[2].lower() if item[2] else ""
            
            if search in ["мошенничество", "спам", "личный звонок"]:
                match = (item_verdict == search)
            else:
                match = search in item_filename or search in item_verdict
            
            if match:
                with st.expander(f"🕒 {item[1]} | {item[2]} — {item[4]}"):
                    st.write(f"**Анализ ИИ:** {item[6]}")
                    st.write(f"**Рекомендация:** {item[7]}")
                    st.divider()
                    st.write("**Полная текстовая расшифровка:**")
                    st.caption(item[3])
                    
                    col1, col2 = st.columns(2)
                    
                    report = (
                        f"ОТЧЕТ АНАЛИЗА ЗВОНКА\n"
                        f"Дата: {item[1]}\n"
                        f"Файл: {item[2]}\n\n"
                        f"ВЕРДИКТ: {item[4]} ({item[5]}%)\n"
                        f"АНАЛИЗ:\n{item[6]}\n"
                        f"РЕКОМЕНДАЦИЯ:\n{item[7]}\n\n"
                        f"ПОЛНЫЙ ТЕКСТ РАЗГОВОРА:\n{item[3]}"
                    )
                    
                    col1.download_button("📥 Отчет (TXT)", report, f"report_{item[2]}.txt", key=f"dl_{item[0]}")
                    
                    if col2.button("🗑️ Удалить запись", key=f"del_{item[0]}"):
                        delete_record(item[0])
                        st.rerun()
    else:
        st.info("История проверок пока пуста. Проведите свой первый анализ в одной из вкладок выше!")