-- Создаем базы данных
CREATE DATABASE auth_db;
CREATE DATABASE tours_db;
CREATE DATABASE booking_db;

-- auth_db (аутентификация + профили пользователей)
\c auth_db;
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- tours_db (туры)
\c tours_db;
CREATE TABLE IF NOT EXISTS tours (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    available BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- booking_db (бронирования)
\c booking_db;
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    tour_id INTEGER NOT NULL,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'confirmed'
);