# Lumi - Your AI Friend

Lumi is a Flask-based AI companion that helps you stay productive, organized, and emotionally supported. It features a chat interface, daily planning, and personalized suggestions based on your profile and goals.

## Features

- **Personalized Chat**: Have meaningful conversations with an AI that remembers your preferences and history
- **Daily Planning**: Set and track your daily tasks and mood
- **Profile Builder**: Create a personal profile to help the AI understand you better
- **Memory System**: Powered by ChromaDB and OpenAI embeddings for contextual conversations
- **Responsive UI**: Built with TailwindCSS for a clean, mobile-friendly experience

## Prerequisites

- Python 3.8+
- MongoDB (local or remote)
- OpenAI API key
- Google Gemini API key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lumi-ai-friend.git
   cd lumi-ai-friend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_API_KEY=your_google_gemini_api_key
   MONGODB_URI=mongodb://localhost:27017/lumi
   SECRET_KEY=your-secret-key-here
   ```

## Running the Application

1. Start MongoDB if it's not already running
2. Start the Flask development server:
   ```bash
   python run.py
   ```
3. Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
lumi-ai-friend/
├── app/
│   ├── __init__.py       # Application factory and configuration
│   ├── routes.py         # Main routes and chat functionality
│   ├── memory.py         # Vector memory system with ChromaDB
│   ├── profile_builder.py # User profile management
│   ├── daily_planner.py  # Daily planning functionality
│   ├── suggestion_engine.py # AI response generation
│   ├── models.py         # Database models and schemas
│   └── templates/        # HTML templates
│       ├── base.html     # Base template
│       ├── chat.html     # Chat interface
│       ├── profile.html  # Profile builder
│       └── daily.html    # Daily planner
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
└── run.py              # Application entry point
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required for embeddings)
- `GOOGLE_API_KEY`: Your Google Gemini API key (required for chat)
- `MONGODB_URI`: MongoDB connection string (default: `mongodb://localhost:27017/lumi`)
- `SECRET_KEY`: Secret key for session encryption
- `FLASK_ENV`: Set to `development` or `production`

## Development

### Running Tests

To run the test suite:

```bash
pytest
```

### Code Style

This project uses `black` for code formatting and `flake8` for linting.

```bash
# Format code
black .

# Lint code
flake8
```

## Deployment

For production deployment, consider using:

- Gunicorn or uWSGI as the WSGI server
- Nginx as a reverse proxy
- Supervisor or systemd for process management

Example Gunicorn command:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "run:create_app()"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Flask, TailwindCSS, and Google's Gemini API
- Inspired by personal productivity and mental health applications
