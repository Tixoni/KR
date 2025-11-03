FROM nginx:1.25-alpine

# Копируем конфигурацию gateway
COPY nginx.conf /etc/nginx/nginx.conf

# Создаем директории для логов
RUN mkdir -p /var/log/nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]

