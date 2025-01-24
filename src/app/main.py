import os
import webview

# Определяем путь к директории, где находится сам скрипт
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_addresses():
    addresses = []
    try:
        # Путь к файлу addresses.txt
        addresses_path = os.path.join(BASE_DIR, 'addresses.txt')
        with open(addresses_path, 'r', encoding='utf-8') as file:
            for line in file:
                addresses.append(line.strip())
    except Exception as e:
        print(f"Ошибка при загрузке адресов из файла: {e}")
    return addresses


if __name__ == "__main__":
    # Загрузка адресов
    addresses = load_addresses()

    # Путь к файлу map.html
    map_path = os.path.join(BASE_DIR, 'map.html')

    # Инициализация WebView
    webview.create_window('Доставка за 10 минут', f'file:///{map_path}', width=800, height=600)
    webview.start()
