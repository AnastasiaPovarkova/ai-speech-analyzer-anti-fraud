import os
from pydub import AudioSegment
from pydub.silence import split_on_silence

def prepare_audio(input_path, output_path="data/samples/processed.wav"):
    """
    Конвертирует аудио в формат, понятный для Whisper:
    WAV, 16kHz, Mono, 16bit.
    """
    try:
        print(f"📦 Обработка файла: {input_path}")
        
        # 1. Загрузка аудио (pydub сам поймет формат, если установлен ffmpeg)
        audio = AudioSegment.from_file(input_path)
        
        # 2. Приведение к нужным параметрам
        # set_frame_rate(16000) - частота
        # set_channels(1) - моно
        # set_sample_width(2) - 16-bit (2 байта)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        # 3. Экспорт
        audio.export(output_path, format="wav")
        print(f"✅ Файл готов и сохранен в: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Ошибка при обработке аудио: {str(e)}")
        return None

def remove_silence(audio_path):
    """
    (Опционально) Удаляет длинные паузы, чтобы Whisper не тратил время на тишину.
    """
    audio = AudioSegment.from_wav(audio_path)
    
    # Разрезаем по тишине и склеиваем обратно
    # min_silence_len - длина тишины (мс), которую считаем паузой
    # silence_thresh - порог громкости (дБ), ниже которого - тишина
    chunks = split_on_silence(audio, min_silence_len=1000, silence_thresh=audio.dBFS-16)
    
    if chunks:
        combined = sum(chunks)
        combined.export(audio_path, format="wav")
        print("✂️ Длинные паузы удалены")

if __name__ == "__main__":
    # Укажи имя своего файла
    test_input = "data/samples/test1.m4a" 
    
    # 1. Сначала подготавливаем формат
    processed_path = prepare_audio(test_input)
    
    # 2. Убираем тишину
    if processed_path:
        remove_silence(processed_path)