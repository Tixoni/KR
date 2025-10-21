# Tourism Platform

Микросервисная платформа для управления туристическими турами и бронированиями.

## Архитектура

Проект состоит из следующих компонентов:

- **Frontend** - веб-интерфейс на HTML/CSS/JavaScript с Nginx
- **Auth Service** - сервис аутентификации и управления пользователями
- **Tours Service** - сервис управления турами
- **Booking Service** - сервис бронирований
- **PostgreSQL** - база данных

## Безопасность

### ⚠️ ВАЖНО: Настройка секретов

Перед запуском в продакшене ОБЯЗАТЕЛЬНО:

1. Скопируйте `env.example` в `.env`
2. Измените `SECRET_KEY` на сложный случайный ключ
3. Измените пароли базы данных
4. Никогда не коммитьте `.env` файл в репозиторий

```bash
cp env.example .env
# Отредактируйте .env файл с вашими секретами
```

### Переменные окружения

```bash
# Обязательные для продакшена
SECRET_KEY=your-super-secret-key-change-me-in-production
POSTGRES_PASSWORD=your-secure-password

# Опциональные
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Запуск

### Разработка

```bash
# Запуск всех сервисов
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up -d --build
```

### Продакшен

```bash
# 1. Настройте переменные окружения
export SECRET_KEY="your-production-secret-key"
export POSTGRES_PASSWORD="your-secure-password"

# 2. Запустите сервисы
docker-compose up -d --build
```

## Доступ к сервисам

- **Frontend**: http://localhost:8080
- **Auth Service**: http://localhost:8000
- **Tours Service**: http://localhost:8001
- **Booking Service**: http://localhost:8002
- **PostgreSQL**: localhost:5432

## API Документация

После запуска сервисов документация доступна по адресам:

- Auth Service: http://localhost:8000/docs
- Tours Service: http://localhost:8001/docs
- Booking Service: http://localhost:8002/docs

## Функциональность

### Для пользователей:
- Регистрация и авторизация
- Просмотр туров с фильтрацией
- Бронирование туров
- Управление бронированиями

### Для администраторов:
- Создание и редактирование туров
- Удаление туров
- Просмотр всех пользователей
- Управление бронированиями

## Улучшения безопасности

В проекте реализованы следующие меры безопасности:

1. **Переменные окружения** для секретов
2. **JWT токены** для аутентификации
3. **Валидация данных** на клиенте и сервере
4. **Обработка ошибок** с понятными сообщениями
5. **Таймауты** для API запросов
6. **Хеширование паролей** с bcrypt

## Мониторинг

Для мониторинга состояния сервисов используйте health check endpoints:

- Auth Service: http://localhost:8000/health
- Tours Service: http://localhost:8001/health
- Booking Service: http://localhost:8002/health

## Разработка

### Структура проекта

```
tourism-platform/
├── auth-service/          # Сервис аутентификации
├── tours-service/         # Сервис туров
├── booking-service/       # Сервис бронирований
├── frontend/             # Веб-интерфейс
├── infrastructure/       # SQL скрипты
├── docker-compose.yml    # Конфигурация Docker
└── env.example          # Пример переменных окружения
```

### Добавление новых функций

1. Создайте новую ветку
2. Внесите изменения
3. Протестируйте локально
4. Создайте Pull Request

## Устранение неполадок

### Проблемы с подключением к БД

```bash
# Проверьте статус контейнеров
docker-compose ps

# Просмотрите логи
docker-compose logs postgres
docker-compose logs auth-service
```

### Проблемы с CORS

Убедитесь, что Nginx правильно настроен в `frontend/nginx.conf`

### Проблемы с токенами

Проверьте, что `SECRET_KEY` одинаковый во всех сервисах.

## Лицензия

MIT License
