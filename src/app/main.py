import os
import webview

def load_addresses():
    addresses = []
    try:
        # Путь к файлу addresses.txt
        addresses_path = os.path.join('src', 'resources', 'addresses.txt')
        with open(addresses_path, 'r', encoding='utf-8') as file:
            for line in file:
                addresses.append(line.strip())
    except Exception as e:
        print(f"Ошибка при загрузке адресов из файла: {e}")
    return addresses

if __name__ == "__main__":
    # Загрузка адресов
    addresses = load_addresses()

    # Инициализация WebView
    map_path = os.path.abspath(os.path.join('src', 'resources', 'map.html'))
    webview.create_window('Доставка за 10 минут', f'file:///{map_path}', width=800, height=600)
    webview.start()