import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Инициализируем новый клиент Google Gen AI
# Ключ берется из .env (GEMINI_API_KEY)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_speech(text):
    """
    Анализирует расшифрованный текст на наличие признаков мошенничества.
    Использует новый SDK (google-genai) и модель Gemini 3.1 Flash Lite.
    """
    if not text or len(text.strip()) < 5:
        return {"error": "Текст слишком короткий для анализа"}

    # Техническое имя модели для API 3.1 Flash Lite
    model_id = 'gemini-3.1-flash-lite-preview'
    
    # Системные инструкции (Промпт)
    system_instruction = """
    Ты — ведущий эксперт по противодействию социальной инженерии и телефонному мошенничеству.
    Твоя задача: провести глубокий лингвистический и психологический анализ текста звонка.

    ИНСТРУКЦИИ:
    1. Ищи маркеры мошенничества:
       - Сбор данных (паспорт, СНИЛС, карты, коды из СМС).
       - Психологическое давление (срочность, угроза блокировки, "родственник в беде").
       - Подозрительные инструкции (установить AnyDesk, установить приложение, перевести на "безопасный счет").
    2. Оценивай контекст: если это обычный бытовой разговор, не ставь высокий риск.
    3. Выделяй прямые цитаты.

    ОТВЕТЬ ТОЛЬКО В ФОРМАТЕ JSON:
    {
      "verdict": "ОПАСНО" | "ПОДОЗРИТЕЛЬНО" | "БЕЗОПАСНО",
      "confidence_score": 0-100,
      "triggers": ["цитата 1", "цитата 2"],
      "analysis": "краткое пояснение логики на русском",
      "recommendation": "совет пользователю на русском"
    }
    """
    # Настройка конфигурации генерации
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type='application/json',
        temperature=0.1
    )

    try:
        # Прямой запрос к модели 3.1 Preview
        response = client.models.generate_content(
            model=model_id,
            contents=f"Проанализируй следующий текст разговора:\n\n{text}",
            config=config
        )
        
        if not response.text:
            return {"error": f"Модель {model_id} вернула пустой ответ"}
            
        return json.loads(response.text)
            
    except Exception as e:
        return {"error": f"Ошибка API при вызове {model_id}: {str(e)}"}

if __name__ == "__main__":
    # Тест на примере с "Доставкой"
    test_text = "Здравствуйте! Это звонит из доставки зон. Доставка зон у вас назначена. Можете, пожалуйста, продиктовать паспортные данные."
    
    print("🧠 Анализ текста...")
    result = analyze_speech(test_text)
    
    if "error" in result:
        print(f"❌ {result['error']}")
    else:
        print("\n" + "="*40)
        print(f"ВЕРДИКТ: {result.get('verdict')} ({result.get('confidence_score')}%)")
        print(f"АНАЛИЗ: {result.get('analysis')}")
        print(f"ТРИГГЕРЫ: {', '.join(result.get('triggers', []))}")
        print(f"СОВЕТ: {result.get('recommendation')}")
        print("="*40)