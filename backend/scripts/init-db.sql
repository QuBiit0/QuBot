-- Qubot Database Initialization Script
-- Creates initial schema and default data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS public;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO qubot;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO qubot;
