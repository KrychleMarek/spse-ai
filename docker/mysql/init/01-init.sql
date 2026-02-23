-- Vytvoření databáze, pokud neexistuje
CREATE DATABASE IF NOT EXISTS example_db;
USE example_db;

-- Tabulka pro galerii
CREATE TABLE IF NOT EXISTS photos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    url VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabulka pro kalendář událostí
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    time TIME,
    description TEXT,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Vložení ukázkových dat do galerie
INSERT INTO photos (title, url, description) VALUES
('První fotka', 'https://placehold.co/600x400/1e88e5/ffffff?text=Photo+1', 'Popis první fotky v galerii.'),
('Druhá fotka', 'https://placehold.co/600x400/43a047/ffffff?text=Photo+2', 'Toto je popis druhé fotky v galerii.'),
('Třetí fotka', 'https://placehold.co/600x400/e53935/ffffff?text=Photo+3', 'Popis třetí fotky v naší galerii.');

-- Vložení ukázkových dat do kalendáře událostí
INSERT INTO events (title, date, time, description, location) VALUES
('Koncert v klubu', '2025-06-15', '19:30:00', 'Živé vystoupení v místním klubu.', 'Klub Modrá Vopice, Praha'),
('Festival Rock na Kopci', '2025-07-20', '14:00:00', 'Venkovní festival s několika kapelami.', 'Letenská pláň, Praha'),
('Natáčení nového videoklipu', '2025-08-05', '09:00:00', 'Celodenní natáčení nového videoklipu k singlu.', 'Studio XYZ, Brno');
