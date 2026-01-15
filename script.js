// Обновляем статистику при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    updateUserStats();
    
    const profileForm = document.getElementById('profileForm');
    const passwordForm = document.getElementById('passwordForm');
    
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }
    
    if (passwordForm) {
        passwordForm.addEventListener('submit', handlePasswordChange);
    }
});

// Обновление статистики пользователя
async function updateUserStats() {
    try {
        const response = await fetch('/get_user_stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            document.getElementById('progress-value').textContent = stats.training_progress + '%';
            document.getElementById('tests-value').textContent = stats.tests_completed;
            document.getElementById('success-value').textContent = stats.success_rate + '%';
            document.getElementById('rank-value').textContent = stats.rank;
            
            // Обновляем прогресс-бар
            const progressFill = document.querySelector('.progress-fill');
            if (progressFill) {
                progressFill.style.width = stats.training_progress + '%';
            }
        }
    } catch (error) {
        console.error('Ошибка при загрузке статистики:', error);
    }
}

// Обработка обновления профиля
async function handleProfileUpdate(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = {
        full_name: form.full_name.value,
        email: form.email.value,
        security_level: form.security_level.value
    };
    
    const messageDiv = document.getElementById('profileMessage');
    
    try {
        const response = await fetch('/update_profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            messageDiv.textContent = data.message;
            messageDiv.className = 'message success';
            // Обновляем имя в заголовке
            const headerElement = document.querySelector('.dashboard-header p');
            if (headerElement) {
                headerElement.textContent = `Добро пожаловать, ${formData.full_name || form.username.value}!`;
            }
        } else {
            messageDiv.textContent = data.message;
            messageDiv.className = 'message error';
        }
    } catch (error) {
        messageDiv.textContent = 'Ошибка соединения';
        messageDiv.className = 'message error';
    }
}

// Обработка смены пароля
async function handlePasswordChange(e) {
    e.preventDefault();
    
    const form = e.target;
    const newPassword = form.new_password.value;
    const confirmPassword = form.confirm_password.value;
    
    // Проверка совпадения паролей
    if (newPassword !== confirmPassword) {
        const messageDiv = document.getElementById('passwordMessage');
        messageDiv.textContent = 'Пароли не совпадают';
        messageDiv.className = 'message error';
        return;
    }
    
    const formData = {
        current_password: form.current_password.value,
        new_password: newPassword
    };
    
    const messageDiv = document.getElementById('passwordMessage');
    
    try {
        const response = await fetch('/change_password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            messageDiv.textContent = data.message;
            messageDiv.className = 'message success';
            form.reset(); // Очищаем форму
        } else {
            messageDiv.textContent = data.message;
            messageDiv.className = 'message error';
        }
    } catch (error) {
        messageDiv.textContent = 'Ошибка соединения';
        messageDiv.className = 'message error';
    }
}