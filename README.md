# SmartAgri ML — AI-Powered Smart Agriculture & Crop Disease Detection System

A complete, production-quality full-stack application combining AI/ML, modern web technologies, and real database persistence to help farmers detect crop diseases, get crop recommendations, predict yields, and access weather forecasts.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Framer Motion, Recharts, Lucide Icons |
| Backend | Python 3.11+, FastAPI, Pydantic v2, JWT Auth, Passlib (bcrypt) |
| AI / ML | TensorFlow/Keras, scikit-learn, NumPy, Pandas, OpenCV, Pillow |
| Database | MongoDB Atlas (via Motor async driver) |
| Weather | Open-Meteo API (free, no API key required) |

## Features

- AI Crop Disease Detection (8 crops, 20+ diseases) with image upload
- AI Crop Recommendation based on soil N/P/K, temperature, humidity, pH, rainfall
- AI Yield Prediction using Random Forest regression
- Real-time Weather Forecast with 7-day outlook and farming advice
- User Dashboard with interactive charts and activity tracking
- Admin Dashboard with user management and system statistics
- History management with search, pagination, and PDF report downloads
- JWT authentication with forgot/reset password (token-based, time-limited)
- Dark/Light mode toggle
- Responsive design (mobile, tablet, desktop)

## Project Structure

```
SmartAgri-ML/
├── frontend/          # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── types/
│   │   └── utils.ts
│   ├── package.json
│   └── vite.config.ts
├── backend/           # FastAPI + Python backend
│   ├── app/
│   │   ├── api/        # Route handlers
│   │   ├── core/       # Config, database, security
│   │   ├── ml/         # ML models (disease, crop, yield)
│   │   ├── models/
│   │   ├── schemas/    # Pydantic schemas
│   │   ├── services/   # Business logic
│   │   └── main.py     # FastAPI entry point
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- MongoDB (local or Atlas cluster)

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Edit .env with your MongoDB Atlas connection string and JWT secret
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 3. Environment Variables

Create `backend/.env` with:

```env
# MongoDB (local or Atlas)
MONGODB_URL=mongodb://localhost:27017
# Or Atlas: mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=smart_agriculture_db

# JWT secret (generate: python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET=your_secret_here

# CORS
BACKEND_CORS_ORIGINS=http://localhost:5173

# Admin bootstrap
ADMIN_EMAIL=admin@smartagri.com
ADMIN_PASSWORD=admin123456
```

### 4. Running the Application

Start the backend:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Start the frontend (new terminal):

```bash
cd frontend
npm run dev
```

## URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

## API Endpoints

### Authentication
- `POST /api/auth/register` — Register new user
- `POST /api/auth/login` — Login
- `POST /api/auth/forgot-password` — Request password reset
- `POST /api/auth/reset-password` — Reset password with token
- `GET /api/auth/me` — Get current user

### Disease Detection
- `POST /api/disease/predict` — Upload leaf image for prediction
- `GET /api/disease/history` — Get disease prediction history
- `GET /api/disease/report/{id}` — Download PDF report
- `GET /api/disease/crops` — List supported crops

### Crop Recommendation
- `POST /api/crop/recommend` — Get AI crop recommendation
- `GET /api/crop/history` — Get recommendation history

### Yield Prediction
- `POST /api/yield/predict` — Predict crop yield
- `GET /api/yield/history` — Get yield prediction history
- `GET /api/yield/options` — Get form options

### Weather
- `GET /api/weather/forecast` — Get 7-day forecast
- `GET /api/weather/current` — Get current weather
- `GET /api/weather/geocode` — Geocode a location

### User
- `GET /api/users/profile` — Get profile
- `PUT /api/users/profile` — Update profile
- `PUT /api/users/change-password` — Change password

### Admin (requires admin role)
- `GET /api/admin/dashboard` — System statistics
- `GET /api/admin/users` — List all users
- `PUT /api/admin/users/{id}/status` — Toggle user status

## Admin Access

An admin account is auto-created on first startup:
- Email: `admin@smartagri.com`
- Password: `admin123456`

## ML Models

| Model | Type | Approach |
|-------|------|----------|
| Disease Detection | Computer Vision | OpenCV color analysis (demo) / TensorFlow CNN (when model available) |
| Crop Recommendation | Classification | Random Forest trained on 20 crop profiles with known optimal conditions |
| Yield Prediction | Regression | Random Forest Regressor trained on synthetic data encoding real yield relationships |

**Note:** The disease detection demo mode is NOT random — it uses deterministic OpenCV image analysis based on green/brown/yellow pixel ratios to produce explainable predictions.

## Testing

Run backend tests:

```bash
cd backend
pytest
```

Build frontend:

```bash
cd frontend
npm run build
```

## License

© 2026 SmartAgri ML. Educational project.
