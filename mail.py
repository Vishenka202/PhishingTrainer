"""
Проверка регистраций email на различных сайтах с использованием Holehe
Установка: pip install holehe
"""

import holehe
import json
from typing import Dict, List
from datetime import datetime
import sys

def check_email_registrations(email: str) -> Dict:
    """
    Проверяет регистрации email на различных сайтах с помощью Holehe
    
    Args:
        email: Email для проверки
        
    Returns:
        Словарь с результатами проверки
    """
    print(f"🔍 Проверка регистраций для email: {email}")
    print("Это может занять несколько минут...")
    
    try:
        # Запускаем Holehe для проверки email
        results = holehe.find(email)
        
        # Собираем все сайты, где найден email
        found_sites = {}
        
        for result in results:
            if result.get("exists"):
                site_info = {
                    "site": result.get("domain", "Неизвестно"),
                    "exists": result.get("exists", False),
                    "emailrecovery": result.get("emailrecovery"),
                    "phoneNumber": result.get("phoneNumber"),
                    "others": result.get("others", {})
                }
                found_sites[result.get("domain", "unknown")] = site_info
        
        return {
            "email": email,
            "total_found": len(found_sites),
            "sites": found_sites,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        return {
            "email": email,
            "error": str(e),
            "total_found": 0,
            "sites": {},
            "timestamp": datetime.now().isoformat(),
            "status": "error"
        }

def display_results(results: Dict):
    """
    Выводит результаты проверки в удобном формате
    
    Args:
        results: Результаты проверки
    """
    print("\n" + "="*80)
    print("РЕЗУЛЬТАТЫ ПРОВЕРКИ EMAIL РЕГИСТРАЦИЙ")
    print("="*80)
    
    if results.get("status") == "error":
        print(f"❌ Ошибка при проверке: {results.get('error')}")
        return
    
    email = results.get("email", "Неизвестно")
    total = results.get("total_found", 0)
    
    print(f"📧 Email: {email}")
    print(f"📊 Всего найдено регистраций: {total}")
    print(f"⏰ Время проверки: {datetime.fromisoformat(results['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
    
    if total == 0:
        print("\n🎉 Email не найден на проверяемых сайтах")
        return
    
    print("\n" + "-"*80)
    print("НАЙДЕННЫЕ РЕГИСТРАЦИИ:")
    print("-"*80)
    
    # Группируем сайты по категориям для удобства
    site_categories = {
        "Социальные сети": ["facebook", "twitter", "instagram", "linkedin", "vk", "tiktok"],
        "Технические/Разработка": ["github", "gitlab", "stackoverflow", "git"],
        "Профессиональные": ["xing", "behance", "dribbble", "researchgate"],
        "Покупки": ["amazon", "ebay", "aliexpress", "etsy"],
        "Развлечения": ["youtube", "twitch", "spotify", "netflix"],
        "Путешествия": ["booking", "airbnb", "expedia", "tripadvisor"],
        "Образование": ["coursera", "udemy", "edx", "khanacademy"],
        "Финансы": ["paypal", "venmo", "revolut", "coinbase"],
        "Игры": ["steam", "epicgames", "origin", "xbox"]
    }
    
    categorized_sites = {category: [] for category in site_categories.keys()}
    categorized_sites["Другие"] = []
    
    for site_name, site_data in results["sites"].items():
        site_lower = site_name.lower()
        categorized = False
        
        for category, patterns in site_categories.items():
            if any(pattern in site_lower for pattern in patterns):
                categorized_sites[category].append((site_name, site_data))
                categorized = True
                break
        
        if not categorized:
            categorized_sites["Другие"].append((site_name, site_data))
    
    # Выводим результаты по категориям
    for category, sites in categorized_sites.items():
        if sites:
            print(f"\n{category}:")
            print("-" * 40)
            
            for site_name, site_data in sorted(sites, key=lambda x: x[0]):
                additional_info = []
                
                if site_data.get("emailrecovery"):
                    additional_info.append(f"Восстановление: {site_data['emailrecovery']}")
                if site_data.get("phoneNumber"):
                    additional_info.append(f"Телефон: {site_data['phoneNumber']}")
                
                info_str = f"  • {site_name}"
                if additional_info:
                    info_str += f" ({'; '.join(additional_info)})"
                
                print(info_str)
    
    # Выводим статистику по категориям
    print("\n" + "-"*80)
    print("СТАТИСТИКА ПО КАТЕГОРИЯМ:")
    print("-"*80)
    
    for category, sites in categorized_sites.items():
        if sites:
            print(f"{category}: {len(sites)}")
    
    print("\n" + "="*80)

def save_results_to_file(results: Dict, filename: str = None):
    """
    Сохраняет результаты в файл
    
    Args:
        results: Результаты проверки
        filename: Имя файла для сохранения (опционально)
    """
    if results.get("status") == "error":
        return
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        email_part = results["email"].replace("@", "_at_")
        filename = f"email_check_results_{email_part}_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Результаты сохранены в файл: {filename}")
    except Exception as e:
        print(f"\n⚠️  Не удалось сохранить результаты: {e}")

def main():
    """
    Основная функция
    """
    print("\n" + "="*80)
    print("ПРОВЕРКА РЕГИСТРАЦИЙ EMAIL НА САЙТАХ")
    print("Использует Holehe (https://github.com/megadose/holehe)")
    print("="*80)
    
    # Проверяем, установлен ли holehe
    try:
        import holehe
    except ImportError:
        print("\n❌ Модуль holehe не установлен!")
        print("Установите его с помощью команды:")
        print("pip install holehe")
        print("\nЗавершение работы.")
        sys.exit(1)
    
    while True:
        print("\n" + "-"*80)
        email = input("\nВведите email для проверки (или 'exit' для выхода): ").strip()
        
        if email.lower() == 'exit':
            print("\nЗавершение работы.")
            break
        
        # Простая валидация email
        if "@" not in email or "." not in email:
            print("❌ Неверный формат email")
            continue
        
        # Проверяем email
        results = check_email_registrations(email)
        
        # Выводим результаты
        display_results(results)
        
        # Предлагаем сохранить результаты
        if results.get("status") == "success" and results.get("total_found", 0) > 0:
            save_choice = input("\nСохранить результаты в файл? (y/n): ").lower()
            if save_choice in ['y', 'yes', 'да']:
                save_results_to_file(results)
        
        # Предлагаем продолжить
        continue_check = input("\nПроверить другой email? (y/n): ").lower()
        if continue_check not in ['y', 'yes', 'да']:
            print("\nЗавершение работы.")
            break

def batch_check_emails(emails: List[str]):
    """
    Пакетная проверка нескольких email
    
    Args:
        emails: Список email для проверки
    """
    print(f"\n🧺 Пакетная проверка {len(emails)} email...")
    
    all_results = []
    
    for i, email in enumerate(emails, 1):
        print(f"\n[{i}/{len(emails)}] Проверка: {email}")
        results = check_email_registrations(email)
        all_results.append(results)
        
        if results.get("status") == "success":
            print(f"   Найдено регистраций: {results.get('total_found', 0)}")
        else:
            print(f"   ❌ Ошибка: {results.get('error', 'Неизвестно')}")
    
    # Сохраняем все результаты
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_filename = f"batch_email_check_{timestamp}.json"
    
    try:
        with open(batch_filename, 'w', encoding='utf-8') as f:
            json.dump({
                "batch_check": True,
                "total_emails": len(emails),
                "check_timestamp": datetime.now().isoformat(),
                "results": all_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Все результаты сохранены в файл: {batch_filename}")
        
        # Сводная статистика
        successful = sum(1 for r in all_results if r.get("status") == "success")
        total_found = sum(r.get("total_found", 0) for r in all_results if r.get("status") == "success")
        
        print(f"\n📊 Сводная статистика:")
        print(f"   • Проверено email: {len(emails)}")
        print(f"   • Успешных проверок: {successful}")
        print(f"   • Всего найдено регистраций: {total_found}")
        
    except Exception as e:
        print(f"\n⚠️  Не удалось сохранить результаты пакетной проверки: {e}")

if __name__ == "__main__":
    try:
        # Если переданы аргументы командной строки
        if len(sys.argv) > 1:
            if sys.argv[1] == "--batch":
                # Режим пакетной проверки
                emails = sys.argv[2:]
                if emails:
                    batch_check_emails(emails)
                else:
                    print("❌ Не указаны email для пакетной проверки")
                    print("Использование: python script.py --batch email1@example.com email2@example.com")
            else:
                # Проверка одного email из аргументов
                email = sys.argv[1]
                results = check_email_registrations(email)
                display_results(results)
                
                if results.get("status") == "success" and results.get("total_found", 0) > 0:
                    save_results_to_file(results)
        else:
            # Интерактивный режим
            main()
    
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем.")
    
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("Проверьте подключение к интернету и установку holehe.")