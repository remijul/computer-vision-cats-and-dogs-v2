-- Création de l'utilisateur
CREATE USER catsdogs WITH PASSWORD '?C@TS&D0GS!';

-- Création de la base de données
CREATE DATABASE cats_dogs_db OWNER catsdogs;

-- Attribution de tous les privilèges sur la base de données
GRANT ALL PRIVILEGES ON DATABASE cats_dogs_db TO catsdogs;

-- Se connecter à la nouvelle base de données pour les privilèges sur le schéma
\c cats_dogs_db;

-- Attribution des privilèges sur le schéma public
GRANT ALL PRIVILEGES ON SCHEMA public TO catsdogs;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO catsdogs;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO catsdogs;

-- Privilèges par défaut pour les futurs objets
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO catsdogs;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO catsdogs;