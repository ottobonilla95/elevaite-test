-- Elevaite Platform - Database Initialization Script
-- This script runs automatically on first PostgreSQL startup
-- It creates all required databases for the platform

-- Create databases for each service
CREATE DATABASE auth;
CREATE DATABASE workflow_engine;
CREATE DATABASE elevaite_ingestion;

-- Grant privileges to elevaite user
GRANT ALL PRIVILEGES ON DATABASE auth TO elevaite;
GRANT ALL PRIVILEGES ON DATABASE workflow_engine TO elevaite;
GRANT ALL PRIVILEGES ON DATABASE elevaite_ingestion TO elevaite;

-- Enable UUID extension on all databases (required for uuid_generate_v4())
\c auth
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c workflow_engine
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c elevaite_ingestion
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
