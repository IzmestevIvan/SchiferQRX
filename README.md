# SchiferQRX

SchiferQRX — это Django-проект для создания и извлечения секретных QR-кодов.  
Проект включает систему аутентификации пользователей, интерфейс для работы с QR-кодами и базовую структуру для дальнейшего расширения функционала.

## Возможности

- регистрация и авторизация пользователей
- генерация QR-кодов
- извлечение данных из QR-кодов
- хранение и обработка данных через Django
- разделение логики по приложениям
- подготовленная структура для сервисного слоя

## Стек технологий

- Python
- Django 3.2.16
- SQLite3 (на проде будет postgres)
- HTML
- CSS
- JS
- Django Templates

## Структура проекта

```bash
qr_secret/
│
├── env/
├── qr_secret/
│   ├── qr_secret/  - настройки проекта
│   ├── qrapp/  - там вся логика по генерации qr кодов
│   ├── static/  - здесь весь css/js
│   ├── templates/ - здесь весь html
│   ├── users/ - здесь вся работа с юзерами, создание моделей, админка
│   ├── db.sqlite3
│   └── manage.py
│
├── .gitignore
└── requirements.txt
```

---

## 🚀 Установка и запуск

> ⚠️ Все команды с `manage.py` выполняются внутри папки `qr_secret`

### 1. 📦 Клонирование репозитория

```bash
git clone <ссылка-на-репозиторий>
cd qr_secret
```

### 2. 🧪 Создание виртуального окружения

```bash
python3 -m venv env
```

#### macOS / Linux
```bash
source env/bin/activate
```

#### Windows
```bash
env\Scripts\activate
```

### 3. 📥 Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. 📁 Переход в папку проекта

```bash
cd qr_secret
```

### 5. 🗄 Применение миграций

```bash
python manage.py migrate
```

### 7. ▶️ Запуск сервера

```bash
python manage.py runserver
```

### 🌐 Открыть в браузере

```
http://127.0.0.1:8000/
```

---

## 💡 Полезные команды

```bash
python manage.py shell  -- если хочешь покопаться в проекте через терминал
python manage.py makemigrations  -- если меняешь что-то в бд, то делай миграции
python manage.py collectstatic  -- собрать всю статику (css, js) в отдельное место
```
