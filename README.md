# Formulation Engine

A 100% clean, natural ingredients formulation engine with a FastAPI backend and React frontend.

## Features

- **AI-Powered Formulation**: Uses OpenAI GPT-4 to generate natural ingredient formulations
- **Clean Architecture**: Separated backend (FastAPI) and frontend (React + TypeScript)
- **Modern UI**: Beautiful, responsive interface with real-time ingredient display
- **Type Safety**: Full TypeScript support for better development experience

## Project Structure

```
formulation-engine/
├── backend/
│   ├── .env                    # Environment variables (create from env.example)
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   └── app/
│       ├── core/
│       │   └── config.py      # Configuration management
│       ├── models/
│       │   └── ingredient.py  # Pydantic models
│       ├── services/
│       │   └── formulation_service.py  # OpenAI integration
│       └── routes/
│           └── formulation.py  # API endpoints
└── frontend/
    ├── index.html             # Main HTML file
    ├── package.json           # Node.js dependencies
    ├── tsconfig.json          # TypeScript configuration
    ├── vite.config.ts         # Vite configuration
    └── src/
        ├── main.tsx           # React entry point
        ├── App.tsx            # Main App component
        ├── index.css          # Global styles
        ├── components/
        │   └── FormulationForm.tsx  # Main form component
        └── services/
            └── api.ts         # API client
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd formulation-engine/backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

5. **Start the backend server:**
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd formulation-engine/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:3000`

## Usage

1. Open your browser and go to `http://localhost:3000`
2. Enter your formulation requirements in the text area (e.g., "natural skincare for sensitive skin")
3. Click "Generate Formulation"
4. View the generated list of natural ingredients with their attributes

## API Endpoints

### POST `/formulation/`

Generates a list of natural ingredients based on the provided query.

**Request Body:**
```json
{
  "query": "natural skincare for sensitive skin"
}
```

**Response:**
```json
[
  {
    "name": "Aloe Vera",
    "attributes": {
      "benefits": "Soothing and hydrating",
      "usage": "Apply directly to skin",
      "safety": "Generally safe for most skin types"
    }
  }
]
```

## Development

### Backend Development

- The backend uses FastAPI with automatic API documentation
- Visit `http://localhost:8000/docs` for interactive API documentation
- All models use Pydantic for validation and serialization

### Frontend Development

- Built with React 18 and TypeScript
- Uses Vite for fast development and building
- CSS supports both light and dark themes
- Responsive design with CSS Grid

## Environment Variables

### Backend (.env)

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## Technologies Used

### Backend
- **FastAPI**: Modern, fast web framework
- **Pydantic**: Data validation and settings management
- **OpenAI**: AI-powered formulation generation
- **Uvicorn**: ASGI server

### Frontend
- **React 18**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **CSS**: Modern styling with responsive design

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both backend and frontend
5. Submit a pull request

## License

This project is open source and available under the MIT License. 