live server : https://ui-consistency-checker-sigma.vercel.app/ # AI-Powered UI Consistency Checker

A full-stack application that analyzes the visual consistency of a web application's UI using Generative AI (Gemini 2.0 Flash) and Playwright.

## Features

- **Screenshot Analysis**: Upload multiple screenshots of your UI. The vision AI extracts components and checks them for consistency.
- **URL Analysis**: Provide a public URL. The system automatically crawls up to 5 pages, captures multiple viewports (desktop, tablet, mobile), and inspects the DOM/CSS for accurate styling data.
- **Deterministic Consistency Engine**: Computes scores (0-100) across 8 categories (Buttons, Typography, Spacing, Colors, Cards, Navbar, Forms, Responsive).
- **AI Recommendations**: Explains why inconsistencies matter and provides copy-paste ready CSS and Tailwind utility fixes.
- **Premium UI**: Modern dark-mode dashboard built with React, Vite, and Tailwind CSS.

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite + TypeScript + Tailwind CSS
- **AI Engine**: Google Gemini 2.0 Flash
- **Browser Automation**: Playwright

## Installation & Setup

### Prerequisites

- Node.js (v18+)
- Python (v3.10+)
- A Google Gemini API Key

### 1. Backend Setup

```bash
cd backend
python -m venv env

# Activate env
# Windows:
env\Scripts\activate
# Mac/Linux:
# source env/bin/activate

pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

Run the backend:
```bash
python -m uvicorn app.main:app
# Runs on http://localhost:8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

Run the frontend:
```bash
npm run dev
# Runs on http://localhost:5173
```

### 3. Test Website (Optional)

A small test website with intentional UI inconsistencies is included for testing the URL analysis feature.

```bash
# From the root of the project
npx serve test-website/
```
Once it's running (e.g., via `ngrok` or deployed publicly), you can use its URL in the UI Consistency Checker.

## Folder Structure

- `backend/`: FastAPI application.
  - `app/api/`: API routes.
  - `app/models/`: Pydantic models.
  - `app/services/`: AI, Playwright, Consistency logic.
- `frontend/`: React application.
  - `src/components/`: Reusable UI elements.
  - `src/pages/`: Main application views.
  - `src/services/`: API client.
- `test-website/`: HTML files with intentional styling inconsistencies.
