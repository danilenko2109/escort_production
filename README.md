# L'Aura - Премиальный каталог профилей

> Production-ready премиум платформа с роскошным черно-золотым дизайном

[![Status](https://img.shields.io/badge/status-production--ready-green)]()
[![License](https://img.shields.io/badge/license-proprietary-blue)]()

## 🚀 Quick Start (3 шага)

```bash
# 1. Клонируйте проект
git clone <your-repo>
cd laura

# 2. Запустите setup
make setup

# 3. Запустите dev servers (в 2 терминалах)
make backend    # Terminal 1
make frontend   # Terminal 2
```

**Готово!** 🎉
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- Admin: http://localhost:3000/admin/login

---

## 📋 Содержание

- [Требования](#требования)
- [Установка](#установка)
- [Запуск](#запуск)
- [Production Build](#production-build)
- [Архитектура](#архитектура)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

---

## ✅ Требования

| Компонент | Версия | Проверка |
|-----------|--------|----------|
| Node.js | 18+ | `node --version` |
| Python | 3.11+ | `python3 --version` |
| SQLite | built-in | `python3 -c "import sqlite3"` |
| Yarn | 1.22+ | `yarn --version` |

**Проверить все зависимости:**
```bash
python3 scripts/check-deps.py
```

---

## 📦 Установка

### Автоматическая установка (рекомендуется)

```bash
make setup
```

Эта команда:
1. ✅ Проверит зависимости
2. ✅ Установит пакеты backend (Python)
3. ✅ Установит пакеты frontend (Node.js)
4. ✅ Создаст .env файлы из примеров
5. ✅ Заполнит базу данных тестовыми данными

### Ручная установка

#### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python seed.py
```

#### Frontend
```bash
cd frontend
yarn install
cp .env.example .env
```

---

## 🏃 Запуск

### Development (локально)

**Вариант 1: Makefile (рекомендуется)**
```bash
# В двух отдельных терминалах:
make backend    # Terminal 1 - запустит backend на :8001
make frontend   # Terminal 2 - запустит frontend на :3000
```

**Вариант 2: Прямой запуск**
```bash
# Terminal 1: Backend
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Frontend  
cd frontend
yarn start
```

### Production

```bash
# Build frontend for production
make build

# Run backend in production mode
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
```

---

## 🏗️ Архитектура

```
/app/
├── backend/              # FastAPI backend
│   ├── server.py         # Главный сервер
│   ├── models.py         # Pydantic модели
│   ├── auth.py           # JWT аутентификация
│   ├── utils.py          # Утилиты
│   ├── seed.py           # Seed данные
│   ├── requirements.txt  # Python зависимости
│   └── .env             # Переменные окружения
├── frontend/            # React фронтенд
│   ├── src/
│   │   ├── components/  # Компоненты
│   │   ├── pages/       # Страницы
│   │   ├── utils/       # API и утилиты
│   │   └── App.js       # Главный компонент
│   ├── package.json     # Node зависимости
│   └── .env            # Переменные окружения
├── scripts/             # Скрипты автоматизации
├── Makefile            # Make команды
└── README.md           # Эта документация
```

### Технологии

**Frontend:**
- React 19
- Framer Motion (анимации)
- Tailwind CSS
- Shadcn/UI
- Axios

**Backend:**
- FastAPI
- SQLite (sqlite3)
- JWT аутентификация
- Cloudinary (изображения)
- Telegram Bot (уведомления)

**Database:**
- SQLite (`backend/app.db`)

---

## 🔌 Интеграции

### Cloudinary (изображения)

1. Зарегистрируйтесь на https://cloudinary.com
2. В Dashboard скопируйте credentials
3. Добавьте в `backend/.env`:
```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### Telegram (уведомления)

1. Создайте бота через @BotFather
2. Получите токен бота
3. Узнайте свой chat_id
4. Добавьте в `backend/.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 📡 API Documentation

### Публичные endpoints

```
GET  /api/profiles              # Список профилей
GET  /api/profiles/{id}         # Детали профиля
POST /api/contact               # Отправить сообщение
GET  /api/health                # Health check
```

### Admin endpoints (требуется JWT)

```
POST /api/admin/login           # Вход
GET  /api/admin/stats           # Статистика
POST /api/profiles              # Создать профиль
PUT  /api/profiles/{id}         # Обновить профиль
DELETE /api/profiles/{id}       # Удалить профиль
GET  /api/cloudinary/signature  # Подпись для загрузки
```

### Health Check

```bash
curl http://localhost:8001/api/health
```

Response:
```json
{
  "status": "ok",
  "database": "healthy",
  "timestamp": "2026-01-30T12:00:00Z"
}
```

---

## 🔑 Учетные данные

### Admin панель
- **URL:** /admin/login
- **Username:** `admin`
- **Password:** `admin123`

⚠️ **ВАЖНО:** Измените пароль в продакшене!

### Тестовые города
- Москва
- Санкт-Петербург
- Екатеринбург
- Новосибирск

---

## 🧪 Тестирование

### Smoke Tests

```bash
make test
```

### Ручное тестирование

```bash
# Backend health
curl http://localhost:8001/api/health

# Get profiles
curl http://localhost:8001/api/profiles?city=Москва

# Admin login
curl -X POST http://localhost:8001/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

---

## 🐛 Troubleshooting

### Frontend не компилируется

**Проблема:** `assignWith is not defined`

**Решение:**
```bash
cd frontend
rm -rf node_modules yarn.lock
yarn install
```

### Backend не запускается

**Проблема:** MongoDB connection error

**Проверка:**
```bash
# Проверить что MongoDB запущен
sudo systemctl status mongodb
# или
mongod --version
```

### Порт уже занят

```bash
# Найти процесс на порту 3000 или 8001
lsof -i :3000
lsof -i :8001

# Убить процесс
kill -9 <PID>
```

### .env файлы отсутствуют

```bash
# Создать из примеров
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

---

## 📚 Дополнительные команды

```bash
make help              # Показать все доступные команды
make check             # Проверить зависимости
make install           # Установить зависимости
make seed              # Заполнить БД данными
make build             # Production build
make clean             # Очистить артефакты
make logs              # Показать логи
make restart           # Перезапустить сервисы
```

---

## 🚀 Production Deployment

См. [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)

**Ключевые шаги:**
1. Измените `JWT_SECRET` на случайный strong string
2. Установите `CORS_ORIGINS` на реальные домены
3. Настройте HTTPS
4. Включите rate limiting
5. Настройте мониторинг
6. Создайте backup стратегию

---

## 🎯 Основные фичи

- ✅ Премиум черно-золотой дизайн
- ✅ Плавные анимации (Framer Motion)
- ✅ Поиск профилей по городу
- ✅ Фильтрация и сортировка
- ✅ Responsive дизайн
- ✅ Admin панель
- ✅ JWT аутентификация
- ✅ Загрузка изображений (Cloudinary)
- ✅ Telegram уведомления
- ✅ Русский язык UI

---

## 📄 Лицензия

Proprietary - All rights reserved

---

## 👥 Поддержка

**Email:** info@laura.ru

**Issues:** Создайте issue в репозитории

---

**Made with ❤️ and ✨**
