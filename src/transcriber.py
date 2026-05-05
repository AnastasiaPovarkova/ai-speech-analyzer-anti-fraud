import subprocess
import os

def transcribe_audio(audio_path):
    """
    Функция-обертка: вызывает системный whisper-cli и забирает текст в Python.
    """
    # Путь к скачанной модели
    model_path = "models/ggml-base.bin"
    
    # Имя команды для запуска (можно найти через ls /usr/local/bin)
    whisper_bin = "whisper-cli"

    if not os.path.exists(audio_path):
        return f"❌ Файл не найден: {audio_path}"

    # Формируем команду, как если бы мы писали её в терминале
    # -m: модель, -f: файл, --no-timestamps: убираем [00:00.000], чтобы был только текст
    command = [
        whisper_bin,
        "-m", model_path,
        "-f", audio_path,
        "--no-timestamps",
        "-l", "en" # Указываем язык явно
    ]

    try:
        # Запускаем процесс и ждем завершения
        # capture_output=True сохраняет то, что программа вывела в консоль
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')

        if result.returncode == 0:
            # Если всё прошло успешно, возвращаем чистый текст
            return result.stdout.strip()
        else:
            # Если whisper-cli выдал ошибку (например, не нашел модель)
            return f"❌ Ошибка движка whisper-cli: {result.stderr}"

    except Exception as e:
        # Если сломался сам Python (например, не нашел команду whisper-cli)
        return f"❌ Системная ошибка: {str(e)}"

if __name__ == "__main__":
    # Указываем путь к скачанному файлу
    path_to_test = "data/samples/test.wav"
    
    print("⏳ Начинаю расшифровку... Это может занять несколько секунд.")
    final_text = transcribe_audio(path_to_test)
    
    print("\n--- РЕЗУЛЬТАТ ---")
    print(final_text)
    print("-----------------")