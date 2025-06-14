#!/usr/bin/env python3
# ====================================
# ФАЙЛ: backend/emergency_install.py
# ЭКСТРЕННАЯ УСТАНОВКА - ТОЛЬКО РАБОЧИЕ ПАКЕТЫ
# ====================================

"""
Экстренная установка только тех пакетов, которые ГАРАНТИРОВАННО работают
"""

import subprocess
import sys
import os

def install_package(package, version=None):
    """Устанавливает пакет с обработкой ошибок"""
    package_spec = f"{package}=={version}" if version else package
    
    try:
        print(f"📦 Установка {package_spec}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_spec, "--only-binary=all"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {package} установлен")
            return True
        else:
            print(f"❌ Ошибка установки {package}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Таймаут установки {package}")
        return False
    except Exception as e:
        print(f"❌ Исключение при установке {package}: {e}")
        return False

def try_install_alternatives(alternatives):
    """Пробует установить альтернативные версии пакета"""
    for package, versions in alternatives.items():
        print(f"\n🔄 Пробуем установить {package}...")
        
        for version in versions:
            if install_package(package, version):
                return True
        
        # Пробуем без версии
        if install_package(package):
            return True
    
    return False

def main():
    print("🚨 ЭКСТРЕННАЯ УСТАНОВКА Legal Assistant API")
    print("Устанавливаем только проверенные пакеты")
    print("=" * 60)
    
    # Список пакетов с альтернативными версиями
    core_packages = {
        "fastapi": ["0.100.1", "0.95.2", "0.90.1"],
        "uvicorn": ["0.22.0", "0.20.0", "0.18.3"],
        "pydantic": ["1.10.12", "1.10.7", "1.9.2"],  # Возвращаемся к v1
        "python-multipart": ["0.0.5", "0.0.6"],
        "python-dotenv": ["1.0.0", "0.21.0"]
    }
    
    optional_packages = {
        "requests": ["2.31.0", "2.28.2"],
        "beautifulsoup4": ["4.12.2", "4.11.1"],
        "httpx": ["0.24.1", "0.23.3"]
    }
    
    # Обновляем pip
    print("📦 Обновление pip...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("✅ pip обновлен")
    except:
        print("⚠️ Не удалось обновить pip, продолжаем...")
    
    # Устанавливаем основные пакеты
    print("\n" + "="*40)
    print("УСТАНОВКА ОСНОВНЫХ ПАКЕТОВ")
    print("="*40)
    
    core_success = 0
    for package, versions in core_packages.items():
        print(f"\n🔧 Устанавливаем {package}...")
        success = False
        
        for version in versions:
            if install_package(package, version):
                success = True
                break
        
        if not success:
            # Пробуем без версии
            if install_package(package):
                success = True
        
        if success:
            core_success += 1
        else:
            print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: Не удалось установить {package}")
    
    # Проверяем критические пакеты
    if core_success < 3:  # Минимум fastapi, uvicorn, pydantic
        print("\n❌ КРИТИЧЕСКИЕ ПАКЕТЫ НЕ УСТАНОВЛЕНЫ!")
        print("Попробуйте:")
        print("1. pip install fastapi uvicorn pydantic --no-deps")
        print("2. pip install fastapi==0.95.2 uvicorn==0.20.0 pydantic==1.10.12")
        return False
    
    # Устанавливаем опциональные пакеты
    print("\n" + "="*40)
    print("УСТАНОВКА ОПЦИОНАЛЬНЫХ ПАКЕТОВ")
    print("="*40)
    
    for package, versions in optional_packages.items():
        print(f"\n🔧 Пробуем установить {package}...")
        success = False
        
        for version in versions:
            if install_package(package, version):
                success = True
                break
        
        if not success:
            print(f"⚠️ Не удалось установить {package}, пропускаем...")
    
    # Создаем директории
    print("\n📁 Создание директорий...")
    directories = ["logs", "simple_db", "uploads", "temp"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ {directory}")
    
    # Финальная проверка
    print("\n" + "="*40)
    print("ПРОВЕРКА УСТАНОВКИ")
    print("="*40)
    
    critical_imports = ["fastapi", "uvicorn", "pydantic"]
    working_imports = []
    
    for module in critical_imports:
        try:
            __import__(module)
            print(f"✅ {module}")
            working_imports.append(module)
        except ImportError:
            print(f"❌ {module}")
    
    # Результат
    print("\n" + "="*60)
    if len(working_imports) >= 3:
        print("🎉 ЭКСТРЕННАЯ УСТАНОВКА УСПЕШНА!")
        print("\n🚀 Попробуйте запустить:")
        print("   python main.py")
        print("\n📚 Если работает, откройте:")
        print("   http://localhost:8000")
        print("   http://localhost:8000/docs")
        
        # Создаем минимальный тестовый файл
        create_test_script()
        
        return True
    else:
        print("❌ ЭКСТРЕННАЯ УСТАНОВКА НЕ УДАЛАСЬ")
        print("\nПоследняя попытка - установите вручную:")
        print("pip install fastapi uvicorn")
        return False

def create_test_script():
    """Создает минимальный тестовый скрипт"""
    test_script = """#!/usr/bin/env python3
# Минимальный тест API
from fastapi import FastAPI

app = FastAPI(title="Emergency Legal Assistant API", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "Emergency API works!", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy", "mode": "emergency"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting emergency server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
    
    try:
        with open("emergency_test.py", "w", encoding="utf-8") as f:
            f.write(test_script)
        print("\n📝 Создан emergency_test.py для тестирования")
        print("   Запустите: python emergency_test.py")
    except Exception as e:
        print(f"⚠️ Не удалось создать тестовый файл: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔ Установка прервана пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        print("Попробуйте установить вручную: pip install fastapi uvicorn")