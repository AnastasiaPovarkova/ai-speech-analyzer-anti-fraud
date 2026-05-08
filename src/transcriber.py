import subprocess
import os
import sys
from audio_processor import prepare_audio, remove_silence
from ai_analyzer import analyze_speech

def transcribe_audio(audio_path, language="ru"):
    """
    Полный цикл: подготовка аудио -> распознавание (Whisper) -> анализ (Gemini).
    """
    # Путь для временного файла, который будет гарантированно подходить для Whisper
    processed_path = "data/samples/temp_ready_for_whisper.wav"
    
    print(f"🔄 Подготовка аудио: приведение к стандарту 16kHz Mono...")
    # Всегда прогоняем через конвертер для страховки параметров частоты и каналов
    ready_file = prepare_audio(audio_path, processed_path)

    if not ready_file:
        return "❌ Ошибка при подготовке аудио файла."

    # Применяем удаление тишины к временному файлу для повышения точности и скорости
    remove_silence(ready_file)

    # Настройка параметров и запуск Whisper
    model_path = "models/ggml-base.bin"
    whisper_bin = "whisper-cli"

    # 3. Распознавание текста
    # # -m: модель, -f: файл, --no-timestamps: убираем [00:00.000], чтобы был только текст
    print(f"📦 Распознавание речи через Whisper (язык: {language})...")
    command = [
        whisper_bin,
        "-m", model_path,
        "-f", ready_file,
        "--no-timestamps",
        "-l", language
    ]

    try:
        # capture_output=True сохраняет то, что программа вывела в консоль
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        text = result.stdout.strip()
        
        # Очистка технического мусора Whisper (иногда выводит пустые строки)
        clean_text = "\n".join([line for line in text.split('\n') if line.strip()])
        
        print("\n--- РАСШИФРОВАННЫЙ ТЕКСТ ---")
        print(clean_text)
        print("----------------------------\n")

        # 4. ИИ-Анализ 
        if clean_text:
            print("🧠 Отправляю текст на анализ в Gemini 3.1 Flash Lite Preview...")
            analysis = analyze_speech(clean_text)
            display_analysis_results(analysis)
        else:
            print("⚠️ Текст не распознан, анализ невозможен.")

        # Очистка временного файла
        if os.path.exists(ready_file):
            os.remove(ready_file)
    
        if result.returncode == 0:
            return clean_text
        else:
            # Если whisper-cli выдал ошибку (например, не нашел модель)
            return f"❌ Ошибка Whisper: {result.stderr}"

    except Exception as e:
        # Если сломался сам Python (например, не нашел команду whisper-cli)
        return f"❌ Ошибка выполнения: {str(e)}"
    
def display_analysis_results(result):
    """
    Красиво выводит JSON-ответ от анализатора в консоль.
    """
    if "error" in result:
        print(f"❌ Ошибка анализа: {result['error']}")
        return

    # Цветовая индикация вердикта (эмуляция)
    verdict = result.get("verdict", "НЕИЗВЕСТНО")
    icon = "🚨" if verdict == "ОПАСНО" else "⚠️" if verdict == "ПОДОЗРИТЕЛЬНО" else "✅"
    
    print("="*50)
    print(f"{icon} ВЕРДИКТ: {verdict} ({result.get('confidence_score', 0)}%)")
    print("-" * 50)
    print(f"📝 АНАЛИЗ: {result.get('analysis')}")
    print(f"🎯 ТРИГГЕРЫ: {', '.join(result.get('triggers', []))}")
    print(f"💡 СОВЕТ: {result.get('recommendation')}")
    print("="*50)

if __name__ == "__main__":
    # Теперь просто указываем путь к исходному файлу из диктофона
    input_audio = "data/samples/test1.m4a"
    
    if os.path.exists(input_audio):
        transcribe_audio(input_audio)
    else:
        print(f"❌ Файл не найден: {input_audio}")