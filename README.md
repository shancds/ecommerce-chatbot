# E-Shop Customer Support Chatbot

A full-stack AI-powered customer support chatbot for e-commerce, featuring a Python/Flask backend with PostgreSQL and a React frontend.

## Prerequisites

- Python 3.7+
- Node.js 18+
- PostgreSQL database

## Quick Start

### 1. Backend Setup

```bash
cd Backend

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# Edit .env with your PostgreSQL credentials
```

Configure your `.env` file:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=eshop_chatbot
DB_USER=postgres
DB_PASSWORD=your_password_here
```

Set up the database:
```bash
# Connect to PostgreSQL and create database
psql -U postgres
CREATE DATABASE eshop_chatbot;
\q

# Run schema and seed data
psql -U postgres -d eshop_chatbot -f sql/schema.sql
psql -U postgres -d eshop_chatbot -f sql/seed_data.sql
```

Start the backend server:
```bash
python main.py
```

The API will be available at `http://localhost:5000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Project Structure

```
├── Backend/
│   ├── main.py              # Flask API entry point
│   ├── src/
│   │   ├── agent.py         # AI agent implementation
│   │   ├── api.py           # REST API routes
│   │   ├── database.py      # PostgreSQL connection
│   │   ├── inference_engine.py
│   │   ├── knowledge_base.py
│   │   └── nlp_processor.py
│   ├── sql/
│   │   ├── schema.sql       # Database schema
│   │   └── seed_data.sql    # Sample data
│   └── data/                # JSON data files
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   │   ├── ChatWidget.jsx
    │   │   ├── ChatPanel.jsx
    │   │   ├── ChatBubble.jsx
    │   │   └── AuthForm.jsx
    │   └── contexts/
    │       └── AuthContext.jsx
    └── package.json
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | User login |
| POST | `/api/chat` | Send message to chatbot |
| GET | `/api/chat/history` | Get chat history |

## Development

Run both servers simultaneously in separate terminals:

Terminal 1 (Backend):
```bash
cd Backend
python main.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

## Features

- User authentication (register/login)
- Real-time chat interface
- Order tracking
- Product recommendations
- Return policy information
- Shipping details
- AI-powered responses using rule-based inference
