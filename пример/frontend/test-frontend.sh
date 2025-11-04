#!/bin/bash
# Простой тест фронтенда без Node.js зависимостей
echo "=== Frontend Tests ==="



# Проверяем что JS файлы существуют
echo "Checking JavaScript files..."
if [ -f "frontend/scripts/script.js" ]; then
    echo "script.js exists"
else
    echo "script.js missing"
    exit 1
fi

if [ -f "frontend/scripts/upload.js" ]; then
    echo "upload.js exists"
else
    echo "upload.js missing"
    exit 1
fi
# Проверяем синтаксис JS файлов
echo "Checking JavaScript syntax..."
for file in frontend/scripts/*.js; do
    if [ -f "$file" ]; then
        echo "Checking $file..."
        # Простая проверка синтаксиса
        if node -c "$file"; then
            echo "$file syntax OK"
        else
            echo "$file syntax error"
            exit 1
        fi
    fi
done

# Проверяем что HTML файлы существуют
echo "Checking HTML files..."
if [ -f "frontend/index.html" ]; then
    echo "index.html exists"
else
    echo "index.html missing"
    exit 1
fi

if [ -f "frontend/upload.html" ]; then
    echo "upload.html exists"
else
    echo "upload.html missing"
    exit 1
fi

# Проверяем что CSS файлы существуют
echo "Checking CSS files..."
if [ -f "frontend/styles/style.css" ]; then
    echo "style.css exists"
else
    echo "style.css missing"
    exit 1
fi

if [ -f "frontend/styles/uploadstyle.css" ]; then
    echo "uploadstyle.css exists"
else
    echo "uploadstyle.css missing"
    exit 1
fi

echo "All frontend tests passed!"
