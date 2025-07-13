from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from datetime import datetime
from bson import ObjectId
import json
from .models import UserProfile
from . import memory_system

bp = Blueprint('profile', __name__, url_prefix='/profile')

# Profile questions
PROFILE_QUESTIONS = [
    "What's your name?",
    "What are your top 3 goals for this year?",
    "What daily habits help you be your best self?",
    "How do you typically deal with stress or setbacks?",
    "What are your favorite ways to learn new things?",
    "What time of day are you most productive?",
    "How do you prefer to receive feedback?",
    "What's your approach to work-life balance?",
    "What motivates you when you're feeling stuck?",
    "How do you like to celebrate your achievements?"
]

@bp.route('/', methods=['GET', 'POST'])
def profile():
    """Handle profile creation and updates."""
    if 'user_id' not in session:
        session['user_id'] = str(ObjectId())  # Generate a new user ID if none exists
    
    user_id = session['user_id']
    error = None
    
    if request.method == 'POST':
        # Get form data
        answers = {}
        for i, question in enumerate(PROFILE_QUESTIONS):
            answer = request.form.get(f'q{i+1}', '').strip()
            if answer:
                answers[f'q{i+1}'] = answer
        
        # Validate form
        if not answers:
            error = 'Please answer at least one question'
        else:
            # Save profile to database
            if not user_id:
                error = 'Session expired. Please refresh the page and try again.'
            else:
                # Check if profile exists and update or create
                existing_profile = UserProfile.get_by_user_id(user_id)
        
                if existing_profile:
                    # Update existing profile
                    UserProfile.update(user_id, answers)
                    message = 'Profile updated successfully!'
                    success = True
                else:
                    # Create new profile
                    UserProfile.create(user_id, answers)
                    message = 'Profile created successfully!'
                    success = True
                
                if success:
                    # Save to vector memory
                    memory_text = " ".join([f"Q: {PROFILE_QUESTIONS[int(k[1:])-1]} A: {v}" for k, v in answers.items()])
                    memory_system.save_memory(
                        user_id=user_id,
                        text=memory_text,
                        tags=['profile'],
                        metadata={'type': 'profile'}
                    )
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'message': message})
                    return redirect(url_for('daily.daily'))
    
    # For GET requests or if there was an error
    profile_data = UserProfile.get_by_user_id(user_id) or {}
    
    # Prepare existing answers for the form
    existing_answers = {}
    if profile_data and 'answers' in profile_data:
        existing_answers = profile_data['answers']
    
    # If it's an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if error:
            return jsonify({'error': error}), 400
        return jsonify(profile_data or {})
    
    # For regular requests, render the template
    return render_template(
        'profile_new.html',
        questions=PROFILE_QUESTIONS,
        profile=profile_data,
        existing_answers=existing_answers,
        error=error
    )

@bp.route('/get', methods=['GET'])
def get_profile():
    """Get the user's profile data."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    profile = UserProfile.get_by_user_id(user_id)
    
    if not profile or 'answers' not in profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    return jsonify({'answers': profile['answers']})
