import os
import webview
import threading
import asyncio
import time
import tempfile
import pygame
import speech_recognition as sr
import edge_tts

# Папка проекта (src/app)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# HTML файл карты
MAP_HTML = os.path.join(BASE_DIR, 'webscript', 'map.html')

window = None
assistant_thread = None
assistant_running = False
assistant_stop_event = threading.Event()


class Api:
    def start_voice_assistant(self):
        global assistant_thread, assistant_running, assistant_stop_event
        if assistant_running:
            print("Ассистент уже запущен")
            return

        print("Запускаем голосового помощника")
        assistant_stop_event.clear()
        assistant_thread = threading.Thread(target=assistant_loop, daemon=True)
        assistant_thread.start()
        assistant_running = True

    def stop_voice_assistant(self):
        global assistant_running, assistant_stop_event
        if not assistant_running:
            print("Ассистент уже остановлен")
            return

        print("Останавливаем голосового помощника")
        assistant_stop_event.set()
        assistant_running = False


async def speak_async(text):
    temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    tts = edge_tts.Communicate(text, voice="ru-RU-DmitryNeural", rate="+40%")
    await tts.save(temp_path)

    pygame.mixer.init()
    pygame.mixer.music.load(temp_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(20)
    pygame.mixer.quit()
    os.remove(temp_path)


def speak(text):
    try:
        asyncio.run(speak_async(text))
    except Exception as e:
        print("TTS error:", e)


def listen_once(timeout=5, phrase_time_limit=7):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎧 Ожидание команды...")
        r.pause_threshold = 1.0
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        # блок обработки ошибки ожидания речи
        except sr.WaitTimeoutError:
            return ""
    try:
        query = r.recognize_google(audio, language='ru-RU')
        print(f"🗣 Вы сказали: {query}")
        return query.lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        speak("Ошибка подключения к сервису распознавания.")
        return ""


def js_escape(s: str) -> str:
    if s is None:
        return ''
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")


def call_js(js_code: str):
    global window
    try:
        if window:
            window.evaluate_js(js_code)
        else:
            print("Webview window не готов")
    except Exception as e:
        print("Ошибка вызова JS:", e)


def send_voice_command_to_map(command: str):
    safe = js_escape(command)
    js = f"window.handleVoiceCommand('{safe}');"
    call_js(js)


def process_map_command(command: str):
    command = command.lower()

    # Включение зон
    if any(phrase in command for phrase in ["покажи зоны", "показать зоны", "отобрази зоны", "включи зоны",
                                            "покажи зона"]):
        send_voice_command_to_map('{"action": "zones", "state": "show"}')
        speak("Включаю отображение зон доставки")
        return True

    # Скрытие зон
    if any(phrase in command for phrase in ["скрой зоны", "убери зоны", "выключи зоны", "спрячь зоны"]):
        send_voice_command_to_map('{"action": "zones", "state": "hide"}')
        speak("Выключаю отображение зон доставки")
        return True

    # Построение маршрута
    if any(phrase in command for phrase in ["построй маршрут", "построи маршрут", "постройте маршрут"]):
        addr = command

        routing_mode = "auto"
        if "пешком" in addr or "на ногах" in addr:
            routing_mode = "pedestrian"
        elif "на машине" in addr or "на авто" in addr or "авто" in addr:
            routing_mode = "auto"

        # Чистим адрес
        addr = (addr
                .replace("построй маршрут", "")
                .replace("построи маршрут", "")
                .replace("постройте маршрут", "")
                .replace("до", "")
                .replace("пешком", "")
                .replace("на ногах", "")
                .replace("на машине", "")
                .replace("на авто", "")
                .replace("авто", "")
                .strip())

        if not addr:
            speak("Не расслышал адрес для маршрута. Повторите, пожалуйста.")
            return True

        # Отправляем JSON в JS
        js_command = {
            "action": "route",
            "address": addr,
            "mode": routing_mode
        }
        send_voice_command_to_map(str(js_command).replace("'", '"'))

        # "Построить маршрут"
        js_code = f"""
            let input = document.querySelector('input[type="text"], input');
            if(input) input.value = '{addr}';
            let btn = Array.from(document.querySelectorAll('button')).find(b => 
                /постро/i.test(b.innerText) || /маршрут/i.test(b.innerText)
            );
            if(btn) btn.click();
        """
        webview.windows[0].evaluate_js(js_code)

        speak(f"Строю маршрут до {addr} {'пешком' if routing_mode == 'pedestrian' else 'на машине'}")
        return True

    # Очистка маршрута
    if any(phrase in command for phrase in ["очисти маршрут", "убери маршрут", "сбрось маршрут"]):
        send_voice_command_to_map('{"action": "clearRoute"}')
        speak("Маршрут очищен")
        return True

    return False


def assistant_loop():
    hour = time.localtime().tm_hour
    if 5 <= hour < 12:
        greeting = "Доброе утро"
    elif 12 <= hour < 18:
        greeting = "Добрый день"
    else:
        greeting = "Добрый вечер"
    speak(f"{greeting}. Голосовой помощник активен.")

    while not assistant_stop_event.is_set():
        phrase = listen_once(timeout=8, phrase_time_limit=6)
        if assistant_stop_event.is_set():
            break
        if not phrase:
            continue

        print("Обработаю команду:", phrase)
        handled = process_map_command(phrase)
        if handled:
            continue

        if "привет" in phrase:
            speak("Приветствую. Чем могу помочь?")
        elif "время" in phrase:
            now = time.strftime("%H:%M")
            speak(f"Сейчас {now}")
        elif "выход" in phrase or "завершаем" in phrase:
            speak("До свидания")
            assistant_stop_event.set()
            break
        else:
            speak("Команда не распознана. Повторите, пожалуйста.")

    speak("Голосовой помощник отключен.")


def start_app():
    global window
    api = Api()
    url = f'file:///{MAP_HTML.replace(os.path.sep, "/")}'
    window = webview.create_window('Доставка за 10 минут', url, js_api=api, width=1100, height=700)
    webview.start()


if __name__ == "__main__":
    start_app()
