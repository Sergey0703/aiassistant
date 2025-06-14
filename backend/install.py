#!/usr/bin/env python3
# ====================================
# ФАЙЛ: backend/install.py
# Скрипт установки зависимостей
# ====================================

"""
Скрипт установки зависимостей для Legal Assistant API
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"\n🔧 {description}...")
    print(f"Команда: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✅ {description} - успешно")
        if result.stdout:
            print(f"Вывод: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False

def check_python_version():
    """Проверяет версию Python"""
    version = sys.version_info
    print(f"🐍 Python версия: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Требуется Python 3.8 или выше")
        return False
    
    print("✅ Версия Python подходит")
    return True

def install_minimal():
    """Устанавливает минимальные зависимости"""
    print("\n📦 Установка МИНИМАЛЬНЫХ зависимостей...")
    
    requirements_file = "requirements-minimal.txt"
    if not os.path.exists(requirements_file):
        print(f"❌ Файл {requirements_file} не найден")
        return False
    
    return run_command(
        f"{sys.executable} -m pip install -r {requirements_file}",
        "Установка минимальных зависимостей"
    )

def install_windows():
    """Устанавливает Windows-совместимые зависимости"""
    print("\n📦 Установка WINDOWS-совместимых зависимостей...")
    
    requirements_file = "requirements-windows.txt"
    if not os.path.exists(requirements_file):
        print(f"❌ Файл {requirements_file} не найден")
        return False
    
    return run_command(
        f"{sys.executable} -m pip install -r {requirements_file}",
        "Установка Windows-совместимых зависимостей"
    )

def install_full():
    """Устанавливает полные зависимости"""
    print("\n📦 Установка ПОЛНЫХ зависимостей...")
    print("⚠️ Внимание: некоторые пакеты могут требовать компиляторы!")
    
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print(f"❌ Файл {requirements_file} не найден")
        return False
    
    return run_command(
        f"{sys.executable} -m pip install -r {requirements_file}",
        "Установка полных зависимостей"
    )

def upgrade_pip():
    """Обновляет pip"""
    return run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Обновление pip"
    )

def create_directories():
    """Создает необходимые директории"""
    print("\n📁 Создание директорий...")
    
    directories = [
        "logs",
        "simple_db", 
        "chromadb_data",
        "uploads",
        "temp",
        "backups"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Создана директория: {directory}")
        except Exception as e:
            print(f"❌ Ошибка создания {directory}: {e}")

def test_installation():
    """Тестирует установку"""
    print("\n🧪 Тестирование установки...")
    
    test_imports = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation")
    ]
    
    all_good = True
    
    for module, description in test_imports:
        try:
            __import__(module)
            print(f"✅ {module}: {description}")
        except ImportError:
            print(f"❌ {module}: {description} - НЕ УСТАНОВЛЕНО")
            all_good = False
    
    return all_good

def main():
    """Главная функция установки"""
    print("=" * 60)
    print("🏛️  Legal Assistant API - Установка зависимостей")
    print("=" * 60)
    
    # Проверяем версию Python
    if not check_python_version():
        sys.exit(1)
    
    # Создаем директории
    create_directories()
    
    # Обновляем pip
    print("\n" + "="*40)
    print("ЭТАП 1: Обновление pip")
    print("="*40)
    upgrade_pip()
    
    # Спрашиваем пользователя о типе установки
    print("\n" + "="*40)
    print("ЭТАП 2: Выбор типа установки")
    print("="*40)
    print("Выберите тип установки:")
    print("1. Минимальная (только FastAPI + uvicorn)")
    print("2. Windows-совместимая (рекомендуется для Windows)")
    print("3. Полная (включая ChromaDB, может требовать компиляторы)")
    print("4. Пропустить установку")
    
    choice = input("\nВведите номер (1-4): ").strip()
    
    if choice == "1":
        success = install_minimal()
    elif choice == "2":
        success = install_windows()
    elif choice == "3":
        print("⚠️ ВНИМАНИЕ: Полная установка может потребовать:")
        print("   - Microsoft Visual C++ Build Tools")
        print("   - Rust компилятор")
        print("   - Может занять много времени")
        confirm = input("\nПродолжить? (y/N): ").strip().lower()
        if confirm == 'y':
            success = install_full()
        else:
            print("Установка отменена, используем Windows-совместимую версию")
            success = install_windows()
    elif choice == "4":
        print("⏩ Установка пропущена")
        success = True
    else:
        print("❌ Неверный выбор, устанавливаем Windows-совместимую версию")
        success = install_windows()
    
    if not success:
        print("\n❌ Установка завершилась с ошибками")
        sys.exit(1)
    
    # Тестируем установку
    print("\n" + "="*40)
    print("ЭТАП 3: Тестирование")
    print("="*40)
    
    if test_installation():
        print("\n✅ Установка завершена успешно!")
        print("\n🚀 Для запуска сервера используйте:")
        print("   python main.py")
        print("\n📚 Документация API будет доступна по адресу:")
        print("   http://localhost:8000/docs")
    else:
        print("\n❌ Некоторые модули не установлены")
        print("Попробуйте запустить установку еще раз или установите вручную:")
        print("   pip install fastapi uvicorn pydantic")

if __name__ == "__main__":
    main()