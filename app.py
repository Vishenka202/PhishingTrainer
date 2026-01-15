from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import sqlite3
import json
from contextlib import contextmanager

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# SQLite database configuration
DATABASE = 'phishing_trainer.db'

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                role VARCHAR(20) NOT NULL DEFAULT 'test_subject',
                created_by INTEGER,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                security_level VARCHAR(20) DEFAULT 'beginner',
                training_progress INTEGER DEFAULT 0,
                phishing_tests_completed INTEGER DEFAULT 0,
                organization VARCHAR(100),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Create tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                difficulty VARCHAR(20) DEFAULT 'beginner',
                time_limit INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Create questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type VARCHAR(20) DEFAULT 'single_choice',
                options TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                points INTEGER DEFAULT 1,
                FOREIGN KEY (test_id) REFERENCES tests (id) ON DELETE CASCADE
            )
        ''')
        
        # Create test results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                test_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                max_score INTEGER NOT NULL,
                time_spent INTEGER NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                answers TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (test_id) REFERENCES tests (id)
            )
        ''')
        
        # Create user progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                test_id INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'not_started',
                score INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                attempts INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (test_id) REFERENCES tests (id),
                UNIQUE(user_id, test_id)
            )
        ''')
        
        # Create admin user if not exists
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role, security_level, organization) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('admin', 'admin@phishing-trainer.com', generate_password_hash('admin123'), 'System Administrator', 'admin', 'expert', 'Система'))
        except sqlite3.IntegrityError:
            pass  # Admin user already exists
        
        # Create sample test if not exists
        cursor.execute('SELECT COUNT(*) FROM tests')
        if cursor.fetchone()[0] == 0:
            # Create sample test
            cursor.execute('''
                INSERT INTO tests (title, description, difficulty, created_by)
                VALUES (?, ?, ?, ?)
            ''', ('Основы распознавания фишинга', 'Базовый тест для проверки знаний о фишинговых атаках', 'beginner', 1))
            
            test_id = cursor.lastrowid
            
            # Create sample questions
            sample_questions = [
                {
                    'question_text': 'Какие из перечисленных признаков могут указывать на фишинговое письмо?',
                    'question_type': 'multiple_choice',
                    'options': ['Ошибки в написании доменного имени отправителя', 'Срочные требования немедленных действий', 'Запрос конфиденциальной информации', 'Официальный логотип компании'],
                    'correct_answer': [0, 1, 2],
                    'explanation': 'Фишинговые письма часто содержат ошибки в доменных именах, создают ощущение срочности и запрашивают конфиденциальные данные.',
                    'points': 2
                },
                {
                    'question_text': 'Вам пришло письмо от банка с ссылкой на сайт my-bank-security.com. Как следует поступить?',
                    'question_type': 'single_choice',
                    'options': ['Перейти по ссылке и ввести данные', 'Позвонить в банк по официальному номеру', 'Проигнорировать письмо', 'Переслать письмо другу'],
                    'correct_answer': [1],
                    'explanation': 'Всегда звоните в банк по официальному номеру для подтверждения. Домены с дополнительными словами часто являются фишинговыми.',
                    'points': 1
                },
                {
                    'question_text': 'Письмо от "службы поддержки" содержит вложение с названием "Обновление_безопасности.exe". Что делать?',
                    'question_type': 'single_choice',
                    'options': ['Открыть вложение - это важно для безопасности', 'Удалить письмо не открывая вложение', 'Переслать в IT-отдел', 'Сохранить вложение на компьютер'],
                    'correct_answer': [1],
                    'explanation': 'Исполняемые файлы (.exe) в письмах от неизвестных отправителей - классический признак фишинга с вредоносным ПО.',
                    'points': 1
                }
            ]
            
            for question in sample_questions:
                cursor.execute('''
                    INSERT INTO questions (test_id, question_text, question_type, options, correct_answer, explanation, points)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (test_id, question['question_text'], question['question_type'], 
                      json.dumps(question['options']), json.dumps(question['correct_answer']), 
                      question['explanation'], question['points']))
        
        conn.commit()

# Initialize database on startup
init_db()

def format_date(date_string):
    """Format date string to readable format"""
    if not date_string:
        return 'Не указана'
    try:
        if isinstance(date_string, str):
            date_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            return date_obj.strftime('%d.%m.%Y %H:%M')
        elif isinstance(date_string, datetime):
            return date_string.strftime('%d.%m.%Y %H:%M')
        else:
            return str(date_string)
    except:
        return str(date_string)

def format_short_date(date_string):
    """Format date string to short readable format"""
    if not date_string:
        return 'Не указана'
    try:
        if isinstance(date_string, str):
            date_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            return date_obj.strftime('%d.%m.%Y')
        elif isinstance(date_string, datetime):
            return date_string.strftime('%d.%m.%Y')
        else:
            return str(date_string)
    except:
        return str(date_string)

def get_user_by_username(username):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,))
        user = cursor.fetchone()
        if user:
            user_dict = dict(user)
            user_dict['registration_date'] = format_date(user_dict['registration_date'])
            user_dict['last_login'] = format_date(user_dict['last_login'])
            return user_dict
        return None

def get_user_by_id(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ? AND is_active = 1', (user_id,))
        user = cursor.fetchone()
        if user:
            user_dict = dict(user)
            user_dict['registration_date'] = format_date(user_dict['registration_date'])
            user_dict['last_login'] = format_date(user_dict['last_login'])
            return user_dict
        return None

def create_user(username, email, password, full_name, role, created_by, organization=None):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role, created_by, organization) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, generate_password_hash(password), full_name, role, created_by, organization))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def get_all_users(current_user_id, current_user_role):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if current_user_role == 'admin':
            cursor.execute('''
                SELECT u.*, creator.username as created_by_name 
                FROM users u 
                LEFT JOIN users creator ON u.created_by = creator.id 
                WHERE u.id != ? AND u.is_active = 1
                ORDER BY u.role, u.username
            ''', (current_user_id,))
        else:
            cursor.execute('''
                SELECT u.*, creator.username as created_by_name 
                FROM users u 
                LEFT JOIN users creator ON u.created_by = creator.id 
                WHERE u.created_by = ? AND u.is_active = 1 AND u.role = 'test_subject'
                ORDER BY u.username
            ''', (current_user_id,))
            
        users = cursor.fetchall()
        result = []
        for user in users:
            user_dict = dict(user)
            user_dict['registration_date'] = format_short_date(user_dict['registration_date'])
            result.append(user_dict)
        return result

def get_organization_users(organization):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, creator.username as created_by_name 
            FROM users u 
            LEFT JOIN users creator ON u.created_by = creator.id 
            WHERE u.organization = ? AND u.is_active = 1 AND u.role = 'test_subject'
            ORDER BY u.username
        ''', (organization,))
        
        users = cursor.fetchall()
        result = []
        for user in users:
            user_dict = dict(user)
            user_dict['registration_date'] = format_short_date(user_dict['registration_date'])
            result.append(user_dict)
        return result

def get_organizations():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT organization 
            FROM users 
            WHERE organization IS NOT NULL AND organization != '' AND is_active = 1
            ORDER BY organization
        ''')
        return [row[0] for row in cursor.fetchall()]

def update_user_profile(user_id, full_name, email, security_level):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET full_name = ?, email = ?, security_level = ? 
                WHERE id = ?
            ''', (full_name, email, security_level, user_id))
            conn.commit()
            return True
    except:
        return False

def change_user_password(user_id, new_password):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET password_hash = ? 
                WHERE id = ?
            ''', (generate_password_hash(new_password), user_id))
            conn.commit()
            return True
    except:
        return False

def delete_user(user_id, current_user_id, current_user_role):
    if user_id == current_user_id:
        return False, "Нельзя удалить собственный аккаунт"
    
    if current_user_role == 'user':
        user_to_delete = get_user_by_id(user_id)
        if not user_to_delete or user_to_delete['created_by'] != current_user_id or user_to_delete['role'] != 'test_subject':
            return False, "Недостаточно прав для удаления этого пользователя"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            return True, "Пользователь удален"
    except:
        return False, "Ошибка при удалении пользователя"

def update_last_login(username):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = ? WHERE username = ?', (datetime.now(), username))
        conn.commit()

def create_test(title, description, difficulty, time_limit, created_by):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tests (title, description, difficulty, time_limit, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, description, difficulty, time_limit, created_by))
            test_id = cursor.lastrowid
            conn.commit()
            return test_id
    except:
        return None

def update_test(test_id, title, description, difficulty, time_limit):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tests 
                SET title = ?, description = ?, difficulty = ?, time_limit = ?
                WHERE id = ?
            ''', (title, description, difficulty, time_limit, test_id))
            conn.commit()
            return True
    except:
        return False

def delete_test(test_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tests WHERE id = ?', (test_id,))
            conn.commit()
            return True
    except:
        return False

def add_question(test_id, question_text, question_type, options, correct_answer, explanation, points):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO questions (test_id, question_text, question_type, options, correct_answer, explanation, points)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (test_id, question_text, question_type, json.dumps(options), 
                  json.dumps(correct_answer), explanation, points))
            conn.commit()
            return True
    except:
        return False

def get_all_tests(user_id=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute('''
                SELECT t.*, up.status, up.score, up.attempts,
                       (SELECT COUNT(*) FROM questions q WHERE q.test_id = t.id) as question_count
                FROM tests t
                LEFT JOIN user_progress up ON t.id = up.test_id AND up.user_id = ?
                WHERE t.is_active = 1
                ORDER BY t.created_at DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT t.*, 
                       (SELECT COUNT(*) FROM questions q WHERE q.test_id = t.id) as question_count
                FROM tests t
                WHERE t.is_active = 1
                ORDER BY t.created_at DESC
            ''')
        tests = cursor.fetchall()
        return [dict(test) for test in tests]

def get_test_with_questions(test_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tests WHERE id = ?', (test_id,))
        test = cursor.fetchone()
        if not test:
            return None
        
        test_dict = dict(test)
        
        cursor.execute('SELECT * FROM questions WHERE test_id = ? ORDER BY id', (test_id,))
        questions = cursor.fetchall()
        
        test_dict['questions'] = []
        for question in questions:
            question_dict = dict(question)
            question_dict['options'] = json.loads(question_dict['options'])
            question_dict['correct_answer'] = json.loads(question_dict['correct_answer'])
            test_dict['questions'].append(question_dict)
        
        return test_dict

def save_test_result(user_id, test_id, score, max_score, time_spent, answers):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO test_results (user_id, test_id, score, max_score, time_spent, answers)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, test_id, score, max_score, time_spent, json.dumps(answers)))
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_progress (user_id, test_id, status, score, completed_at, attempts)
                VALUES (?, ?, ?, ?, ?, COALESCE((SELECT attempts FROM user_progress WHERE user_id = ? AND test_id = ?), 0) + 1)
            ''', (user_id, test_id, 'completed', score, datetime.now(), user_id, test_id))
            
            cursor.execute('''
                UPDATE users 
                SET phishing_tests_completed = phishing_tests_completed + 1,
                    training_progress = (
                        SELECT COUNT(*) * 100 / (SELECT COUNT(*) FROM tests WHERE is_active = 1) 
                        FROM user_progress 
                        WHERE user_id = ? AND status = 'completed'
                    )
                WHERE id = ?
            ''', (user_id, user_id))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Error saving test result: {e}")
        return False

def get_user_test_history(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tr.*, t.title, t.difficulty
            FROM test_results tr
            JOIN tests t ON tr.test_id = t.id
            WHERE tr.user_id = ?
            ORDER BY tr.completed_at DESC
        ''', (user_id,))
        results = cursor.fetchall()
        return [dict(result) for result in results]

def get_test_statistics(test_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_attempts,
                AVG(score) as avg_score,
                MAX(score) as max_score,
                MIN(score) as min_score
            FROM test_results 
            WHERE test_id = ?
        ''', (test_id,))
        stats = dict(cursor.fetchone())
        
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as completed_users
            FROM user_progress 
            WHERE test_id = ? AND status = 'completed'
        ''', (test_id,))
        
        cursor.execute('SELECT COUNT(*) as total_users FROM users WHERE is_active = 1 AND role != "admin"')
        total_users = cursor.fetchone()[0]
        
        stats['completion_rate'] = (stats['completed_users'] / total_users * 100) if total_users > 0 else 0
        
        return stats

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/comparison')
def comparison():
    return render_template('comparison.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['organization'] = user.get('organization', '')
            update_last_login(username)
            return jsonify({'success': True, 'message': 'Вход выполнен успешно!'})
        else:
            return jsonify({'success': False, 'message': 'Неверные учетные данные!'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    test_history = get_user_test_history(session['user_id'])[:5]
    return render_template('dashboard.html', user=user, test_history=test_history)

@app.route('/tests')
def tests_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    tests = get_all_tests(session['user_id'])
    return render_template('tests.html', tests=tests)

@app.route('/test/<int:test_id>')
def take_test(test_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    test = get_test_with_questions(test_id)
    if not test:
        return "Тест не найден", 404
    
    return render_template('take_test.html', test=test)

@app.route('/test/<int:test_id>/submit', methods=['POST'])
def submit_test(test_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Требуется авторизация'})
    
    data = request.get_json()
    answers = data.get('answers', {})
    time_spent = data.get('time_spent', 0)
    
    test = get_test_with_questions(test_id)
    if not test:
        return jsonify({'success': False, 'message': 'Тест не найден'})
    
    score = 0
    max_score = 0
    detailed_answers = {}
    
    for question in test['questions']:
        max_score += question['points']
        user_answer = answers.get(str(question['id']))
        
        if user_answer is not None:
            if question['question_type'] == 'single_choice':
                correct = str(user_answer) in map(str, question['correct_answer'])
            else:
                user_answers = set(map(str, user_answer))
                correct_answers = set(map(str, question['correct_answer']))
                correct = user_answers == correct_answers
            
            if correct:
                score += question['points']
            
            detailed_answers[str(question['id'])] = {
                'user_answer': user_answer,
                'correct': correct,
                'correct_answer': question['correct_answer'],
                'explanation': question.get('explanation', '')
            }
    
    if save_test_result(session['user_id'], test_id, score, max_score, time_spent, detailed_answers):
        return jsonify({
            'success': True,
            'score': score,
            'max_score': max_score,
            'percentage': int((score / max_score) * 100) if max_score > 0 else 0
        })
    else:
        return jsonify({'success': False, 'message': 'Ошибка при сохранении результата'})

@app.route('/test_results')
def test_results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    test_history = get_user_test_history(session['user_id'])
    return render_template('test_results.html', test_history=test_history)

@app.route('/user_management')
def user_management():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['role'] not in ['admin', 'user']:
        return redirect(url_for('dashboard'))
    
    if session['role'] == 'admin':
        organizations = get_organizations()
        users = get_all_users(session['user_id'], session['role'])
        return render_template('user_management.html', 
                             users=users, 
                             organizations=organizations,
                             selected_organization=None)
    else:
        users = get_all_users(session['user_id'], session['role'])
        return render_template('user_management.html', users=users)

@app.route('/organization_users/<organization>')
def organization_users(organization):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Недостаточно прав'})
    
    users = get_organization_users(organization)
    return jsonify({
        'success': True, 
        'users': users,
        'organization': organization
    })

@app.route('/create_user', methods=['POST'])
def create_user_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Требуется авторизация'})
    
    if session['role'] not in ['admin', 'user']:
        return jsonify({'success': False, 'message': 'Недостаточно прав'})
    
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role', 'test_subject')
    organization = data.get('organization', '')
    
    if session['role'] == 'user' and role == 'test_subject':
        organization = session.get('organization', '')
    
    if session['role'] == 'user' and role != 'test_subject':
        return jsonify({'success': False, 'message': 'Вы можете создавать только испытуемых'})
    
    if create_user(username, email, password, full_name, role, session['user_id'], organization):
        return jsonify({'success': True, 'message': 'Пользователь создан успешно!'})
    else:
        return jsonify({'success': False, 'message': 'Ошибка при создании пользователя'})

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Требуется авторизация'})
    
    data = request.get_json()
    full_name = data.get('full_name')
    email = data.get('email')
    security_level = data.get('security_level')
    
    if update_user_profile(session['user_id'], full_name, email, security_level):
        return jsonify({'success': True, 'message': 'Профиль обновлен успешно!'})
    else:
        return jsonify({'success': False, 'message': 'Ошибка при обновлении профиля'})

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Требуется авторизация'})
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    user = get_user_by_username(session['username'])
    if not check_password_hash(user['password_hash'], current_password):
        return jsonify({'success': False, 'message': 'Текущий пароль неверен'})
    
    if change_user_password(session['user_id'], new_password):
        return jsonify({'success': True, 'message': 'Пароль изменен успешно!'})
    else:
        return jsonify({'success': False, 'message': 'Ошибка при изменении пароля'})

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user_route(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Требуется авторизация'})
    
    if session['role'] not in ['admin', 'user']:
        return jsonify({'success': False, 'message': 'Недостаточно прав'})
    
    success, message = delete_user(user_id, session['user_id'], session['role'])
    return jsonify({'success': success, 'message': message})

@app.route('/get_user_stats')
def get_user_stats():
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    user = get_user_by_id(session['user_id'])
    stats = {
        'training_progress': user['training_progress'],
        'tests_completed': user['phishing_tests_completed'],
        'success_rate': 85,
        'rank': 'Эксперт' if user['training_progress'] > 70 else 'Продвинутый'
    }
    
    return jsonify({'success': True, 'stats': stats})

@app.route('/test_management')
def test_management():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('dashboard'))
    
    tests = get_all_tests()
    return render_template('test_management.html', tests=tests)

@app.route('/create_test', methods=['GET', 'POST'])
def create_test_route():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        difficulty = data.get('difficulty', 'beginner')
        time_limit = data.get('time_limit', 0)
        questions = data.get('questions', [])
        
        test_id = create_test(title, description, difficulty, time_limit, session['user_id'])
        if test_id:
            for question_data in questions:
                add_question(
                    test_id,
                    question_data['question_text'],
                    question_data['question_type'],
                    question_data['options'],
                    question_data['correct_answer'],
                    question_data.get('explanation', ''),
                    question_data.get('points', 1)
                )
            
            return jsonify({'success': True, 'message': 'Тест создан успешно!', 'test_id': test_id})
        else:
            return jsonify({'success': False, 'message': 'Ошибка при создании теста'})
    
    return render_template('create_test.html')

@app.route('/delete_test/<int:test_id>', methods=['POST'])
def delete_test_route(test_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Недостаточно прав'})
    
    if delete_test(test_id):
        return jsonify({'success': True, 'message': 'Тест удален успешно!'})
    else:
        return jsonify({'success': False, 'message': 'Ошибка при удалении теста'})

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True)