import os
from flask import Flask
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# Disable ChromaDB telemetry
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY_TESTING'] = 'True'

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure app
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key'),
        MONGO_URI=os.getenv('MONGODB_URI', 'mongodb://localhost:27017/ai_friend'),
        GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
    )
    
    # Initialize extensions
    from .extensions import mongo
    mongo.init_app(app)
    
    # Initialize ChromaDB with telemetry disabled
    chroma_client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Add context processor to make current datetime available in all templates
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.utcnow()}
    
    # Register blueprints
    from . import routes, profile_builder, daily_planner
    app.register_blueprint(routes.bp)
    app.register_blueprint(profile_builder.bp)
    app.register_blueprint(daily_planner.bp)
    
    # Create database indexes on first request
    with app.app_context():
        from .models import create_indexes
        create_indexes()
    
    return app
