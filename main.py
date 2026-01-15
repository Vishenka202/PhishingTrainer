import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import pandas as pd
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, pipeline
import json
import os
from datetime import datetime
import random
import re
import threading


class EmployeeLetterGenerator:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.generator = None
        self.employee_data = []
        self.companies_db = self.load_companies_database()
        self.model_loaded = False
        self.model_loading = False

    def load_companies_database(self):
        """База данных компаний по интересам, возрастам и городам"""
        return {
            "технологии": [
                {"name": "Яндекс", "url": "https://yandex.ru/jobs", "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург", "Екатеринбург", "Новосибирск", "Казань", "Южно-Сахалинск"]},
                {"name": "Сбер", "url": "https://sber.ru/career", "age_groups": ["26-35", "36-45", "46-55"],
                 "cities": ["Москва", "Санкт-Петербург", "Нижний Новгород", "Ростов-на-Дону", "Самара",
                            "Южно-Сахалинск"]},
                {"name": "VK", "url": "https://vk.com/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург", "Южно-Сахалинск"]},
            ],
            "программирование": [
                {"name": "Яндекс", "url": "https://yandex.ru/jobs", "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург", "Екатеринбург", "Новосибирск", "Казань"]},
                {"name": "Kaspersky", "url": "https://careers.kaspersky.com", "age_groups": ["26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург"]},
                {"name": "JetBrains", "url": "https://jetbrains.com/careers", "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург", "Новосибирск"]},
            ],
            "спорт": [
                {"name": "Adidas Россия", "url": "https://adidas.ru/careers", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург", "Краснодар", "Сочи", "Южно-Сахалинск"]},
                {"name": "Nike Россия", "url": "https://nike.com/careers", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург", "Казань", "Южно-Сахалинск"]},
                {"name": "Спортмастер", "url": "https://sportmaster.ru/career",
                 "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Краснодар", "Южно-Сахалинск"]}
            ],
            "рыбалка": [
                {"name": "Fisher Club", "url": "https://fisherclub.ru/career",
                 "age_groups": ["26-35", "36-45", "46-55"],
                 "cities": ["Москва", "Санкт-Петербург", "Владивосток", "Южно-Сахалинск", "Хабаровск"]},
                {"name": "Рыболов", "url": "https://rybolov.ru/jobs", "age_groups": ["26-35", "36-45", "46-55"],
                 "cities": ["Москва", "Санкт-Петербург", "Калининград", "Южно-Сахалинск"]},
                {"name": "Сахалин Рыбак", "url": "https://sakhalin-rybak.ru/career",
                 "age_groups": ["18-25", "26-35", "36-45"], "cities": ["Южно-Сахалинск", "Владивосток", "Хабаровск"]}
            ],
            "охота": [
                {"name": "Охотник", "url": "https://ohotnik.ru/jobs", "age_groups": ["26-35", "36-45", "46-55"],
                 "cities": ["Москва", "Санкт-Петербург", "Красноярск", "Иркутск", "Южно-Сахалинск"]},
                {"name": "Hunter Pro", "url": "https://hunterpro.ru/career", "age_groups": ["26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург", "Новосибирск", "Южно-Сахалинск"]}
            ],
            "искусство": [
                {"name": "Яндекс.Музыка", "url": "https://music.yandex.ru/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург"]},
                {"name": "Кинопоиск", "url": "https://kinopoisk.ru/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва"]},
                {"name": "Артхив", "url": "https://artchive.ru/jobs", "age_groups": ["26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург"]}
            ],
            "путешествия": [
                {"name": "Tutu.ru", "url": "https://tutu.ru/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург"]},
                {"name": "Ostrovok.ru", "url": "https://ostrovok.ru/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва"]},
                {"name": "Спутник", "url": "https://sputnik8.com/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург"]},
            ],
            "образование": [
                {"name": "Skyeng", "url": "https://skyeng.ru/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург", "Новосибирск"]},
                {"name": "Нетология", "url": "https://netology.ru/jobs", "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург"]},
                {"name": "Учи.ру", "url": "https://uchi.ru/jobs", "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург"]}
            ],
            "здоровье": [
                {"name": "Фитнес-дом", "url": "https://fitnessdom.ru/career", "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург", "Казань", "Краснодар"]},
                {"name": "World Class", "url": "https://worldclass.ru/career",
                 "age_groups": ["18-25", "26-35", "36-45"], "cities": ["Москва", "Санкт-Петербург", "Сочи"]},
                {"name": "Спортлайф", "url": "https://sportlife.ru/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург", "Екатеринбург"]},
            ],
            "кулинария": [
                {"name": "Delivery Club", "url": "https://deliveryclub.ru/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург", "Казань", "Нижний Новгород"]},
                {"name": "Яндекс.Еда", "url": "https://eda.yandex.ru/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург", "Екатеринбург", "Новосибирск"]},
                {"name": "ВкусВилл", "url": "https://vkusvill.ru/jobs", "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург", "Казань", "Краснодар"]},
            ],
            "чтение": [
                {"name": "Литрес", "url": "https://litres.ru/jobs", "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва"]},
                {"name": "MyBook", "url": "https://mybook.ru/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва"]},
                {"name": "Читай-город", "url": "https://chitai-gorod.ru/jobs",
                 "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург", "Екатеринбург", "Новосибирск"]}
            ],
            "музыка": [
                {"name": "Яндекс.Музыка", "url": "https://music.yandex.ru/jobs", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург"]},
                {"name": "VK Музыка", "url": "https://vk.com/music", "age_groups": ["18-25", "26-35"],
                 "cities": ["Москва", "Санкт-Петербург"]},
            ],
            "фотография": [
                {"name": "Canon Россия", "url": "https://canon.ru/jobs", "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва", "Санкт-Петербург"]},
                {"name": "Nikon Россия", "url": "https://nikon.ru/jobs", "age_groups": ["18-25", "26-35", "36-45"],
                 "cities": ["Москва"]},
            ]
        }

    def get_age_group(self, age):
        """Определение возрастной группы"""
        if 18 <= age <= 25:
            return "18-25"
        elif 26 <= age <= 35:
            return "26-35"
        elif 36 <= age <= 45:
            return "36-45"
        elif 46 <= age <= 55:
            return "46-55"
        else:
            return "26-35"

    def select_company(self, interests, age_group, city):
        """Выбор компании на основе интересов, возрастной группы и города"""
        suitable_companies = []

        for interest in interests:
            interest_lower = interest.lower().strip()
            if interest_lower in self.companies_db:
                for company in self.companies_db[interest_lower]:
                    if age_group in company["age_groups"]:
                        if city in company["cities"]:
                            suitable_companies.append((company, 3))  # высший приоритет
                        else:
                            suitable_companies.append((company, 1))  # низший приоритет

        if suitable_companies:
            suitable_companies.sort(key=lambda x: x[1], reverse=True)
            max_priority = suitable_companies[0][1]
            top_companies = [comp for comp, priority in suitable_companies if priority == max_priority]
            return random.choice(top_companies)
        else:
            return {"name": "Сбер", "url": "https://sber.ru/career", "age_groups": ["26-35", "36-45", "46-55"],
                    "cities": ["Москва", "Санкт-Петербург", "Нижний Новгород", "Ростов-на-Дону", "Самара"]}

    def load_model(self, progress_callback=None):
        """Загрузка модели с обработкой ошибок"""
        if self.model_loading:
            return False
            
        self.model_loading = True
        
        try:
            if progress_callback:
                progress_callback("Инициализация загрузки модели...")
            
            # Используем оригинальную модель, которая точно работает
            model_name = 'sberbank-ai/rugpt3small_based_on_gpt2'
            
            if progress_callback:
                progress_callback("Загрузка токенизатора...")
                
            self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
            if progress_callback:
                progress_callback("Загрузка модели... Это может занять несколько минут...")
                
            self.model = GPT2LMHeadModel.from_pretrained(model_name)

            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            if progress_callback:
                progress_callback(f"Перенос модели на {self.device}...")
                
            self.model = self.model.to(self.device)
            self.model.eval()

            if progress_callback:
                progress_callback("Создание пайплайна генерации...")
                
            self.generator = pipeline(
                'text-generation',
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1,
                max_length=400,
                temperature=0.7,
                repetition_penalty=1.3
            )
            
            self.model_loaded = True
            self.model_loading = False
            
            if progress_callback:
                progress_callback("Модель успешно загружена!")
                
            return True
            
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            self.model_loading = False
            
            # Пробуем альтернативный подход - минимальная модель
            try:
                if progress_callback:
                    progress_callback("Попытка загрузки упрощенной модели...")
                
                # Используем маленькую модель для тестирования
                from transformers import AutoTokenizer, AutoModelForCausalLM
                
                model_name = "gpt2"  # Самая базовая модель для теста
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.tokenizer.pad_token = self.tokenizer.eos_token
                self.model = AutoModelForCausalLM.from_pretrained(model_name)
                
                self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                self.model = self.model.to(self.device)
                self.model.eval()
                
                self.generator = pipeline(
                    'text-generation',
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=0 if torch.cuda.is_available() else -1
                )
                
                self.model_loaded = True
                self.model_loading = False
                
                if progress_callback:
                    progress_callback("Упрощенная модель загружена (английский язык)")
                    
                return True
            except Exception as e2:
                print(f"Ошибка загрузки упрощенной модели: {e2}")
                if progress_callback:
                    progress_callback("Не удалось загрузить модель. Будут использоваться шаблонные письма.")
                return False

    def load_employees_from_csv(self, file_path):
        """Загрузка данных сотрудников из CSV"""
        try:
            df = pd.read_csv(file_path)
            if 'interests' in df.columns:
                df['interests'] = df['interests'].apply(
                    lambda x: x.split(',') if isinstance(x, str) else x
                )
            self.employee_data = df.to_dict('records')
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {e}")
            return False

    def load_employees_from_json(self, file_path):
        """Загрузка данных сотрудников из JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.employee_data = json.load(f)
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {e}")
            return False

    def clean_generated_text(self, text, prompt):
        """Очистка сгенерированного текста от повторения промпта"""
        if text.startswith(prompt):
            text = text[len(prompt):].strip()

        patterns_to_remove = [
            r'Напиши.*?письмо.*?:',
            r'Убедись.*?персонализировано.*?',
            r'В конце письма добавь ссылку.*?',
            r'Учти его интересы.*?',
            r'Сделай акцент.*?',
            r'Свяжи мотивацию.*?',
            r'Покажи как его увлечения.*?',
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()

        return text

    def generate_letter(self, employee, letter_type="общее", additional_context=""):
        """Генерация письма для сотрудника с учетом интересов, возраста и города"""
        if not self.model_loaded:
            # Используем шаблонные письма если модель не загружена
            return self.generate_template_only(employee, letter_type)

        try:
            interests = employee['interests']
            if isinstance(interests, str):
                interests = [interest.strip() for interest in interests.split(',')]

            age = employee.get('age', 30)
            age_group = self.get_age_group(age)
            city = employee.get('city', 'Москва')

            company = self.select_company(interests, age_group, city)
            interests_str = ', '.join(interests)

            # Более структурированные промпты для лучшей генерации
            prompts = {
                "общее": f"Уважаемый {employee['name']}!\n\nКомпания {company['name']} обращается к вам, зная о ваших увлечениях {interests_str}.",
                "благодарность": f"Уважаемый {employee['name']}!\n\nКомпания {company['name']} выражает благодарность за вашу работу. Ваши увлечения {interests_str} помогают развивать ценные качества.",
                "приглашение": f"Уважаемый {employee['name']}!\n\nКомпания {company['name']} приглашает вас принять участие в специальном мероприятии. Мы знаем о ваших интересах {interests_str}.",
                "мотивация": f"Уважаемый {employee['name']}!\n\nКомпания {company['name']} хочет поддержать ваше развитие. Ваши увлечения {interests_str} показывают вашу целеустремленность.",
                "карьера": f"Уважаемый {employee['name']}!\n\nКомпания {company['name']} видит потенциал в вашем профессиональном росте. Ваши интересы {interests_str} могут стать основой для карьерного развития."
            }

            base_prompt = prompts.get(letter_type, prompts["общее"])

            # Добавляем персонализацию
            personalization = f"\n\nОсобенно ценно, что вы из {city}. "
            city_comments = {
                "Южно-Сахалинск": "города с уникальной природой и возможностями для активного отдыха.",
                "Москва": "столицы с безграничными возможностями для развития.",
                "Санкт-Петербург": "культурной столицы России, вдохновляющей на творчество.",
                "Екатеринбург": "уральской столицы с богатыми традициями.",
                "Новосибирск": "научного центра Сибири, где рождаются инновации."
            }
            personalization += city_comments.get(city, "города с большими перспективами.")

            # Формируем финальный промпт
            prompt = base_prompt + personalization + additional_context + "\n\n"

            # Генерация текста
            result = self.generator(
                prompt,
                max_length=300,
                num_return_sequences=1,
                temperature=0.7,
                repetition_penalty=1.3,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                no_repeat_ngram_size=2,
                early_stopping=True
            )

            generated_text = result[0]['generated_text']

            # Очищаем текст
            cleaned_text = self.clean_generated_text(generated_text, prompt)

            # Добавляем стандартное завершение
            if not cleaned_text.strip().endswith(company['name']):
                cleaned_text += f"\n\nС уважением,\nКоманда {company['name']}\n\nСсылка для получения подробной информации: {company['url']}"

            return {
                'text': cleaned_text,
                'company': company['name'],
                'url': company['url'],
                'age_group': age_group,
                'city': city
            }

        except Exception as e:
            print(f"Ошибка генерации: {e}")
            return self.generate_template_only(employee, letter_type)

    def generate_template_only(self, employee, letter_type="общее"):
        """Генерация письма только по шаблону (без модели)"""
        interests = employee['interests']
        if isinstance(interests, str):
            interests = [interest.strip() for interest in interests.split(',')]
            
        age = employee.get('age', 30)
        age_group = self.get_age_group(age)
        city = employee.get('city', 'Москва')
        company = self.select_company(interests, age_group, city)
        interests_str = ', '.join(interests)

        return {
            'text': self.generate_template_letter(employee, company, letter_type, interests_str, city),
            'company': company['name'],
            'url': company['url'],
            'age_group': age_group,
            'city': city
        }

    def generate_template_letter(self, employee, company, letter_type, interests, city):
        """Генерация качественного шаблонного письма"""
        templates = {
            "общее": f"""Уважаемый {employee['name']}!

Компания {company['name']} рада обратиться к вам. Мы знаем о ваших увлечениях ({interests}) и хотим поддержать ваши интересы.

Живя в прекрасном городе {city}, вы имеете уникальные возможности для развития своих хобби. Мы уверены, что ваша активность и увлечения помогают вам в профессиональном развитии.

Мы подготовили специальное предложение, которое идеально подойдет человеку с вашими интересами. Наши возможности позволят вам развивать свои увлечения и получать от этого дополнительную пользу.

Не упустите шанс узнать больше! Перейдите по ссылке для получения подробной информации: {company['url']}

Мы будем рады видеть вас среди наших партнеров!

С уважением,
Команда {company['name']}""",

            "благодарность": f"""Уважаемый {employee['name']}!

Компания {company['name']} выражает искреннюю благодарность за вашу отличную работу. Ваши увлечения {interests} развивают в вас ценные качества, которые помогают в профессиональной деятельности.

Особенно ценно, что вы из {city} - города с богатыми традициями. Мы видим ваш потенциал и хотим предложить дополнительные возможности для роста.

Узнайте больше о наших программах поддержки на сайте: {company['url']}

Желаем дальнейших успехов и развития ваших увлечений!

С наилучшими пожеланиями,
{company['name']}""",

            "приглашение": f"""Уважаемый {employee['name']}!

Компания {company['name']} приглашает вас на уникальное мероприятие, которое идеально подойдет для человека с вашими увлечениями ({interests}).

Мы знаем, что вы из {city}, и подготовили программу, учитывающую региональные особенности. Это прекрасная возможность познакомиться с единомышленниками и узнать что-то новое.

Не пропустите это событие! Подробности и регистрация доступны по ссылке: {company['url']}

Ждем вас на нашем мероприятии!

С уважением,
Организаторы от {company['name']}""",

            "мотивация": f"""Уважаемый {employee['name']}!

Компания {company['name']} хочет поддержать ваше стремление к развитию. Ваши увлечения {interests} показывают вашу разносторонность и целеустремленность.

Город {city}, в котором вы живете, предоставляет много возможностей для роста, и мы верим в ваш успех. Ваши хобби могут стать отличным фундаментом для профессионального развития.

Откройте для себя новые горизонты! Посетите наш сайт для получения дополнительной информации: {company['url']}

Пусть ваши увлечения вдохновляют вас на новые достижения!

С наилучшими пожеланиями,
{company['name']}""",

            "карьера": f"""Уважаемый {employee['name']}!

Компания {company['name']} видит большой потенциал в вашем профессиональном развитии. Ваши интересы ({interests}) могут стать отличным фундаментом для построения успешной карьеры.

Мы знаем, что вы из {city}, и готовы предложить вам возможности для роста в нашем филиале или удаленно. Ваши увлечения могут открыть новые карьерные перспективы.

Не упустите шанс изменить свою карьеру к лучшему! Узнайте о вакансиях и возможностях на нашем сайте: {company['url']}

Мы уверены, что вместе мы сможем достичь больших высот!

С уважением,
HR-отдел {company['name']}"""
        }

        return templates.get(letter_type, templates["общее"])

    def generate_all_letters(self, letter_type="общее", additional_context=""):
        """Генерация писем для всех сотрудников"""
        results = []
        for employee in self.employee_data:
            letter_data = self.generate_letter(employee, letter_type, additional_context)
            results.append({
                'employee': employee['name'],
                'age': employee.get('age', 'Не указан'),
                'city': employee.get('city', 'Не указан'),
                'interests': employee['interests'],
                'letter': letter_data['text'],
                'company': letter_data['company'],
                'url': letter_data['url'],
                'age_group': letter_data['age_group'],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return results

    def save_letters_to_file(self, letters, filename):
        """Сохранение писем в файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for item in letters:
                    f.write(f"=== Письмо для {item['employee']} ===\n")
                    f.write(f"Возраст: {item['age']}\n")
                    f.write(f"Город: {item['city']}\n")
                    f.write(
                        f"Интересы: {', '.join(item['interests']) if isinstance(item['interests'], list) else item['interests']}\n")
                    f.write(f"Компания: {item['company']}\n")
                    f.write(f"Ссылка: {item['url']}\n")
                    f.write(f"Возрастная группа: {item['age_group']}\n")
                    f.write(f"Время генерации: {item['timestamp']}\n")
                    f.write("\n" + item['letter'])
                    f.write("\n\n" + "=" * 50 + "\n\n")
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")
            return False


class LetterGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор персонализированных писем для сотрудников")
        self.root.geometry("1000x750")

        self.generator = EmployeeLetterGenerator()
        self.setup_ui()
        self.start_model_loading()

    def setup_ui(self):
        """Настройка графического интерфейса"""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Заголовок
        title_label = ttk.Label(main_frame, text="Генератор персонализированных писем для сотрудников",
                                font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Статус модели
        self.model_status = ttk.Label(main_frame, text="Модель загружается...", foreground="blue")
        self.model_status.grid(row=1, column=0, columnspan=3, pady=(0, 10))

        # Секция загрузки данных
        data_frame = ttk.LabelFrame(main_frame, text="Загрузка данных сотрудников", padding="10")
        data_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(data_frame, text="Загрузить из CSV",
                   command=self.load_csv).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(data_frame, text="Загрузить из JSON",
                   command=self.load_json).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(data_frame, text="Добавить вручную",
                   command=self.add_manual).grid(row=0, column=2)

        self.data_status = ttk.Label(data_frame, text="Данные не загружены", foreground="red")
        self.data_status.grid(row=1, column=0, columnspan=3, pady=(10, 0))

        # Секция настроек генерации
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки письма", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(settings_frame, text="Тип письма:").grid(row=0, column=0, sticky=tk.W)
        self.letter_type = ttk.Combobox(settings_frame,
                                        values=["общее", "благодарность", "приглашение", "мотивация", "карьера"])
        self.letter_type.set("общее")
        self.letter_type.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

        ttk.Label(settings_frame, text="Дополнительный контекст:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.additional_context = ttk.Entry(settings_frame, width=50)
        self.additional_context.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 0))

        # Кнопки генерации
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="Сгенерировать все письма",
                   command=self.generate_all).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Сгенерировать выборочно",
                   command=self.generate_selected).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Сохранить все письма",
                   command=self.save_letters).pack(side=tk.LEFT)

        # Секция отображения сотрудников
        employees_frame = ttk.LabelFrame(main_frame, text="Сотрудники", padding="10")
        employees_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Treeview для сотрудников
        self.employees_tree = ttk.Treeview(employees_frame, columns=("Возраст", "Город", "Интересы"), show="headings",
                                           height=8)
        self.employees_tree.heading("#0", text="Имя")
        self.employees_tree.heading("Возраст", text="Возраст")
        self.employees_tree.heading("Город", text="Город")
        self.employees_tree.heading("Интересы", text="Интересы")

        self.employees_tree.column("#0", width=150)
        self.employees_tree.column("Возраст", width=80)
        self.employees_tree.column("Город", width=120)
        self.employees_tree.column("Интересы", width=200)

        self.employees_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbar для treeview
        scrollbar = ttk.Scrollbar(employees_frame, orient="vertical", command=self.employees_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.employees_tree.configure(yscrollcommand=scrollbar.set)

        # Секция результатов
        results_frame = ttk.LabelFrame(main_frame, text="Результаты", padding="10")
        results_frame.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10), padx=(10, 0))

        self.results_text = scrolledtext.ScrolledText(results_frame, width=60, height=20)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Настройка весов для растягивания
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        employees_frame.columnconfigure(0, weight=1)
        employees_frame.rowconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def update_model_status(self, message):
        """Обновление статуса загрузки модели"""
        self.model_status.config(text=message)
        self.root.update()

    def start_model_loading(self):
        """Запуск загрузки модели в отдельном потоке"""
        def load_model_thread():
            success = self.generator.load_model(progress_callback=self.update_model_status)
            if success:
                self.update_model_status("Модель готова к работе!")
            else:
                self.update_model_status("Модель не загружена. Будут использоваться шаблонные письма.")

        thread = threading.Thread(target=load_model_thread, daemon=True)
        thread.start()

    def load_csv(self):
        """Загрузка данных из CSV файла"""
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            if self.generator.load_employees_from_csv(file_path):
                self.update_employees_list()
                self.data_status.config(text=f"Загружено {len(self.generator.employee_data)} сотрудников",
                                        foreground="green")

    def load_json(self):
        """Загрузка данных из JSON файла"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            if self.generator.load_employees_from_json(file_path):
                self.update_employees_list()
                self.data_status.config(text=f"Загружено {len(self.generator.employee_data)} сотрудников",
                                        foreground="green")

    def add_manual(self):
        """Окно для ручного добавления сотрудника"""
        manual_window = tk.Toplevel(self.root)
        manual_window.title("Добавить сотрудника")
        manual_window.geometry("400x300")

        ttk.Label(manual_window, text="Имя:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(manual_window, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(manual_window, text="Возраст:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        age_entry = ttk.Entry(manual_window, width=30)
        age_entry.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(manual_window, text="Город:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        city_entry = ttk.Entry(manual_window, width=30)
        city_entry.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(manual_window, text="Интересы (через запятую):").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        interests_entry = ttk.Entry(manual_window, width=30)
        interests_entry.grid(row=3, column=1, padx=10, pady=10)

        def save_employee():
            name = name_entry.get().strip()
            age_text = age_entry.get().strip()
            city = city_entry.get().strip()
            interests = [interest.strip() for interest in interests_entry.get().split(",") if interest.strip()]

            if not name:
                messagebox.showwarning("Предупреждение", "Введите имя сотрудника")
                return

            if not age_text.isdigit():
                messagebox.showwarning("Предупреждение", "Введите корректный возраст (число)")
                return

            age = int(age_text)

            if age < 18 or age > 65:
                messagebox.showwarning("Предупреждение", "Введите возраст от 18 до 65 лет")
                return

            if not city:
                messagebox.showwarning("Предупреждение", "Введите город")
                return

            if not interests:
                messagebox.showwarning("Предупреждение", "Введите хотя бы один интерес")
                return

            self.generator.employee_data.append({
                'name': name,
                'age': age,
                'city': city,
                'interests': interests
            })
            self.update_employees_list()
            self.data_status.config(text=f"Загружено {len(self.generator.employee_data)} сотрудников",
                                    foreground="green")
            manual_window.destroy()

        ttk.Button(manual_window, text="Сохранить", command=save_employee).grid(row=4, column=0, columnspan=2, pady=20)

    def update_employees_list(self):
        """Обновление списка сотрудников"""
        for item in self.employees_tree.get_children():
            self.employees_tree.delete(item)

        for employee in self.generator.employee_data:
            interests = ', '.join(employee['interests']) if isinstance(employee['interests'], list) else employee[
                'interests']
            age = employee.get('age', 'Не указан')
            city = employee.get('city', 'Не указан')
            self.employees_tree.insert("", "end", text=employee['name'], values=(age, city, interests))

    def generate_all(self):
        """Генерация писем для всех сотрудников"""
        if not self.generator.employee_data:
            messagebox.showwarning("Предупреждение", "Сначала загрузите данные сотрудников")
            return

        letter_type = self.letter_type.get()
        additional_context = self.additional_context.get()

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Генерация писем...\n\n")
        self.root.update()

        try:
            letters = self.generator.generate_all_letters(letter_type, additional_context)
            self.display_letters(letters)
            self.generated_letters = letters
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка генерации: {e}")

    def generate_selected(self):
        """Генерация письма для выбранного сотрудника"""
        selection = self.employees_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите сотрудника из списка")
            return

        letter_type = self.letter_type.get()
        additional_context = self.additional_context.get()

        self.results_text.delete(1.0, tk.END)

        for item in selection:
            employee_name = self.employees_tree.item(item, "text")
            employee = next((emp for emp in self.generator.employee_data if emp['name'] == employee_name), None)

            if employee:
                self.results_text.insert(tk.END, f"Генерация письма для {employee_name}...\n")
                self.root.update()

                try:
                    letter_data = self.generator.generate_letter(employee, letter_type, additional_context)
                    self.results_text.insert(tk.END, f"\n=== Письмо для {employee_name} ===\n")
                    self.results_text.insert(tk.END, f"Возраст: {employee.get('age', 'Не указан')}\n")
                    self.results_text.insert(tk.END, f"Город: {employee.get('city', 'Не указан')}\n")
                    self.results_text.insert(tk.END, f"Компания: {letter_data['company']}\n")
                    self.results_text.insert(tk.END, f"Ссылка: {letter_data['url']}\n")
                    self.results_text.insert(tk.END, f"Возрастная группа: {letter_data['age_group']}\n\n")
                    self.results_text.insert(tk.END, letter_data['text'])
                    self.results_text.insert(tk.END, "\n" + "=" * 50 + "\n\n")
                except Exception as e:
                    self.results_text.insert(tk.END, f"Ошибка: {e}\n\n")

    def display_letters(self, letters):
        """Отображение сгенерированных писем"""
        self.results_text.delete(1.0, tk.END)

        for item in letters:
            self.results_text.insert(tk.END, f"=== Письмо для {item['employee']} ===\n")
            self.results_text.insert(tk.END, f"Возраст: {item['age']}\n")
            self.results_text.insert(tk.END, f"Город: {item['city']}\n")
            self.results_text.insert(tk.END,
                                     f"Интересы: {', '.join(item['interests']) if isinstance(item['interests'], list) else item['interests']}\n")
            self.results_text.insert(tk.END, f"Компания: {item['company']}\n")
            self.results_text.insert(tk.END, f"Ссылка: {item['url']}\n")
            self.results_text.insert(tk.END, f"Возрастная группа: {item['age_group']}\n")
            self.results_text.insert(tk.END, f"Время: {item['timestamp']}\n\n")
            self.results_text.insert(tk.END, item['letter'])
            self.results_text.insert(tk.END, "\n" + "=" * 50 + "\n\n")

    def save_letters(self):
        """Сохранение писем в файл"""
        if not hasattr(self, 'generated_letters') or not self.generated_letters:
            messagebox.showwarning("Предупреждение", "Сначала сгенерируйте письма")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            if self.generator.save_letters_to_file(self.generated_letters, file_path):
                messagebox.showinfo("Успех", f"Письма сохранены в файл: {file_path}")


def create_sample_files():
    """Создание примеров файлов с данными"""
    # Пример CSV файла
    csv_data = [
        "name,age,city,interests",
        'Иван Петров,28,Москва,"технологии, программирование, спорт"',
        'Мария Сидорова,32,Санкт-Петербург,"образование, искусство, чтение"',
        'Алексей Козлов,45,Екатеринбург,"путешествия, фотография, музыка"',
        'Ольга Новикова,23,Казань,"кулинария, танцы, здоровье"',
        'Дмитрий Иванов,38,Новосибирск,"технологии, бизнес, карьера"',
        'Анна Смирнова,29,Краснодар,"спорт, здоровье, путешествия"',
        'Иванов Иван Иванович,25,Южно-Сахалинск,"спорт, рыбалка, охота"'
    ]

    with open('example_employees.csv', 'w', encoding='utf-8') as f:
        for line in csv_data:
            f.write(line + '\n')

    # Пример JSON файла
    json_data = [
        {"name": "Иван Петров", "age": 28, "city": "Москва", "interests": ["технологии", "программирование", "спорт"]},
        {"name": "Мария Сидорова", "age": 32, "city": "Санкт-Петербург",
         "interests": ["образование", "искусство", "чтение"]},
        {"name": "Алексей Козлов", "age": 45, "city": "Екатеринбург",
         "interests": ["путешествия", "фотография", "музыка"]},
        {"name": "Ольга Новикова", "age": 23, "city": "Казань", "interests": ["кулинария", "танцы", "здоровье"]},
        {"name": "Иванов Иван Иванович", "age": 25, "city": "Южно-Сахалинск",
         "interests": ["спорт", "рыбалка", "охота"]}
    ]

    with open('example_employees.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print("Созданы примеры файлов: example_employees.csv и example_employees.json")


if __name__ == "__main__":
    # Создаем примеры файлов в фоновом режиме
    import threading
    
    def create_files():
        create_sample_files()
    
    thread = threading.Thread(target=create_files, daemon=True)
    thread.start()

    # Запускаем приложение
    root = tk.Tk()
    app = LetterGeneratorApp(root)
    root.mainloop()