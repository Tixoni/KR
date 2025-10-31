FROM nginx:1.25-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html /usr/share/nginx/html/index.html
COPY styles.css /usr/share/nginx/html/styles.css
COPY script.js /usr/share/nginx/html/script.js
COPY sounds/ /usr/share/nginx/html/sounds/

# Alpine Linux использует apk вместо apt-get
RUN apk update && apk add --no-cache curl

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]