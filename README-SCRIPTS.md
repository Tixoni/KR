# Tourism Platform - Docker Swarm Management Scripts

Этот набор скриптов обеспечивает максимально простое управление Tourism Platform в Docker Swarm.


## 🚀 Быстрый старт

```bash
# Запустить платформу
./manage-swarm.sh start

# Проверить статус
./manage-swarm.sh status

# Остановить платформу
./manage-swarm.sh stop
```

## 📋 Доступные скрипты

### Основные скрипты

| Скрипт            | Описание |                 Использование |
|-------------------|----------|--------------------------------|
| `manage-swarm.sh` | Главный скрипт управления | `./manage-swarm.sh [command]` |
| `start-swarm.sh` | Быстрый запуск | `./start-swarm.sh` |
| `stop-swarm.sh` | Быстрая остановка | `./stop-swarm.sh` |
| `restart-swarm.sh` | Перезапуск | `./restart-swarm.sh` |
| `deploy-swarm.sh` | Полное развертывание | `./deploy-swarm.sh` |
| `cleanup-swarm.sh` | Очистка | `./cleanup-swarm.sh [--force]` |
| `check-status.sh` | Проверка статуса | `./check-status.sh [options]` |
| `logs-swarm.sh` | Просмотр логов | `./logs-swarm.sh [service] [lines]` |

## 🎛️ Управление через главный скрипт

### Основные команды

```bash
# Запуск платформы
./manage-swarm.sh start

# Остановка платформы
./manage-swarm.sh stop

# Перезапуск платформы
./manage-swarm.sh restart

# Полное развертывание (с пересборкой)
./manage-swarm.sh deploy

# Проверка статуса
./manage-swarm.sh status

# Просмотр логов
./manage-swarm.sh logs [service] [lines]

# Очистка
./manage-swarm.sh cleanup

# Масштабирование сервисов
./manage-swarm.sh scale [service] [replicas]

# Проверка здоровья
./manage-swarm.sh health

# Справка
./manage-swarm.sh help
```

### Примеры использования

```bash
# Запустить платформу
./manage-swarm.sh start

# Проверить статус
./manage-swarm.sh status

# Посмотреть логи auth-service (50 строк)
./manage-swarm.sh logs auth 50

# Масштабировать auth-service до 5 реплик
./manage-swarm.sh scale auth-service 5

# Проверить здоровье сервисов
./manage-swarm.sh health

# Остановить платформу
./manage-swarm.sh stop
```

## 📊 Просмотр логов

### Просмотр логов через главный скрипт

```bash
# Все логи (20 строк каждого сервиса)
./manage-swarm.sh logs

# Логи конкретного сервиса
./manage-swarm.sh logs auth 100
./manage-swarm.sh logs tours 50
./manage-swarm.sh logs booking 30
./manage-swarm.sh logs frontend 20
./manage-swarm.sh logs postgres 100

# Только ошибки
./manage-swarm.sh logs errors 200

# Следить за логами в реальном времени
./manage-swarm.sh logs follow auth
```

### Прямое использование logs-swarm.sh

```bash
# Все логи
./logs-swarm.sh

# Логи конкретного сервиса
./logs-swarm.sh auth 100
./logs-swarm.sh tours 50

# Следить за логами
./logs-swarm.sh follow auth

# Только ошибки
./logs-swarm.sh errors 200
```

## 🔍 Проверка статуса

### Основная проверка

```bash
# Полный статус
./manage-swarm.sh status

# Детальная проверка
./check-status.sh

# Только ресурсы
./check-status.sh --resources

# Логи конкретного сервиса
./check-status.sh --logs auth-service 20

# Проверка здоровья
./check-status.sh --health auth-service http://localhost:8000/health
```

## 🧹 Очистка

### Обычная очистка

```bash
# Остановить и очистить
./manage-swarm.sh cleanup

# Принудительная очистка
./cleanup-swarm.sh --force
```

### Полная очистка

```bash
# Остановить платформу
./manage-swarm.sh stop

# Полная очистка
./cleanup-swarm.sh --force

# Удалить неиспользуемые ресурсы
docker system prune -a
```

## 🔧 Масштабирование

### Масштабирование сервисов

```bash
# Масштабировать auth-service до 5 реплик
./manage-swarm.sh scale auth-service 5

# Масштабировать frontend до 3 реплик
./manage-swarm.sh scale frontend 3

# Масштабировать tours-service до 2 реплик
./manage-swarm.sh scale tours-service 2
```

### Доступные сервисы для масштабирования

- `postgres` - База данных
- `auth-service` - Сервис аутентификации
- `tours-service` - Сервис туров
- `booking-service` - Сервис бронирования
- `frontend` - Фронтенд

## 🌐 Доступ к сервисам

После запуска платформы доступны следующие URL:

- **Frontend**: http://localhost:8080
- **Auth API**: http://localhost:8000
- **Tours API**: http://localhost:8001
- **Booking API**: http://localhost:8002

## 📋 Полезные команды

### Docker команды

```bash
# Просмотр всех сервисов
docker service ls

# Просмотр логов сервиса
docker service logs tourism-platform_auth-service

# Масштабирование сервиса
docker service scale tourism-platform_auth-service=3

# Обновление сервиса
docker service update --force tourism-platform_auth-service

# Просмотр деталей сервиса
docker service ps tourism-platform_auth-service
```

### Мониторинг

```bash
# Статистика ресурсов
docker stats

# Использование диска
docker system df

# Информация о системе
docker system info
```

## 🚨 Устранение неполадок

### Проблемы с запуском

```bash
# Проверить статус Docker Swarm
docker node ls

# Проверить логи
./manage-swarm.sh logs

# Проверить здоровье
./manage-swarm.sh health

# Перезапустить
./manage-swarm.sh restart
```

### Проблемы с сетью

```bash
# Проверить сеть
docker network ls

# Создать сеть заново
docker network create --driver overlay tourism_network
```

### Проблемы с данными

```bash
# Проверить тома
docker volume ls

# Очистить тома
docker volume prune
```

## 📝 Логирование

Все скрипты создают логи:

- `deployment.log` - Логи развертывания
- `cleanup.log` - Логи очистки

Просмотр логов:

```bash
# Логи развертывания
tail -f deployment.log

# Логи очистки
tail -f cleanup.log
```

## 🔒 Безопасность

- Все скрипты используют безопасные команды
- Автоматическая очистка при ошибках
- Проверка существования ресурсов перед удалением
- Логирование всех операций

## 📞 Поддержка

При возникновении проблем:

1. Проверьте статус: `./manage-swarm.sh status`
2. Посмотрите логи: `./manage-swarm.sh logs`
3. Проверьте здоровье: `./manage-swarm.sh health`
4. Перезапустите: `./manage-swarm.sh restart`

Для полной очистки и перезапуска:

```bash
./manage-swarm.sh stop
./cleanup-swarm.sh --force
./manage-swarm.sh deploy
```
