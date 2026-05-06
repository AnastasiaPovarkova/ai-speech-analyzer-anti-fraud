import subprocess
import os
from audio_processor import prepare_audio, remove_silence

def transcribe_audio(audio_path, language="ru"):
    """
    Полный цикл: гарантированная подготовка аудио (16kHz, Mono) + распознавание текста.
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

    # -m: модель, -f: файл, --no-timestamps: убираем [00:00.000], чтобы был только текст
    command = [
        whisper_bin,
        "-m", model_path,
        "-f", ready_file,
        "--no-timestamps",
        "-l", language
    ]

    try:
        # Запускаем распознавание через подпроцесс
        # capture_output=True сохраняет то, что программа вывела в консоль
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        
        # Всегда удаляем временный файл, чтобы не засорять папку с образцами
        if os.path.exists(ready_file):
            os.remove(ready_file)

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            # Если whisper-cli выдал ошибку (например, не нашел модель)
            return f"❌ Ошибка Whisper: {result.stderr}"

    except Exception as e:
        # Если сломался сам Python (например, не нашел команду whisper-cli)
        return f"❌ Ошибка выполнения: {str(e)}"

if __name__ == "__main__":
    my_record = "data/samples/test1.m4a" 
    
    print(f"⏳ Начинаю расшифровку... Это может занять несколько секунд.")
    result_text = transcribe_audio(my_record, language="ru")
    
    print("\n--- ИТОГОВЫЙ ТЕКСТ ---")
    print(result_text)
    print("-----------------")