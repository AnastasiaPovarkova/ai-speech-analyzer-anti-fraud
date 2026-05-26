from src.transcriber import clean_whisper_output

def test_clean_whisper_output_removes_warnings_and_empty_lines():
    # 1. Данные на вход (фиктивный грязный лог от Whisper)
    dirty_input = (
        "WARNING: The binary 'main' is deprecated.\n"
        "  \n"
        "Алло, это служба безопасности банка.\n"
        "Please use 'whisper-cli' instead.\n"
        "Переведите ваши деньги на безопасный счет."
    )
    
    # 2. Ожидаемый результат
    expected_output = (
        "Алло, это служба безопасности банка.\n"
        "Переведите ваши деньги на безопасный счет."
    )
    
    # 3. Вызов тестируемой функции
    result = clean_whisper_output(dirty_input)
    
    # 4. Проверка утверждения (Assertion)
    assert result == expected_output

def test_clean_whisper_output_with_empty_text():
    assert clean_whisper_output("") == ""
    assert clean_whisper_output("   \n\n   ") == ""