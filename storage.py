"""Загрузка и сохранение данных проекта в JSON-файлах."""
import json
import os


def read_json(filename: str) -> list:
    """Прочитать список записей из JSON-файла.

    Отсутствующий файл считается пустым списком. При поврежденном
    файле выводится предупреждение и также возвращается пустой список.
    """
    try:
        with open(filename, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        print(f"Файл {filename} поврежден ({error}), данные не загружены")
        return []
    if not isinstance(data, list):
        print(f"Файл {filename} должен содержать список записей")
        return []
    return data


def write_json(filename: str, data: list) -> None:
    """Записать список записей в JSON-файл."""
    folder = os.path.dirname(filename)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_domains(filename: str) -> dict[int, dict]:
    """Загрузить домены из JSON-файла в словарь по идентификаторам."""
    return {domain["id"]: domain for domain in read_json(filename)}


def save_domains(filename: str, domains: dict[int, dict]) -> None:
    """Сохранить домены в JSON-файл."""
    write_json(filename, list(domains.values()))


def load_certificates(filename: str) -> list[dict]:
    """Загрузить сертификаты из JSON-файла."""
    return read_json(filename)


def save_certificates(filename: str, certificates: list[dict]) -> None:
    """Сохранить сертификаты в JSON-файл."""
    write_json(filename, certificates)
