from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app
from bson import ObjectId
from datetime import datetime
import json

from .models import UserProfile, DailyPlan, ChatMessage
from .suggestion_engine import generate_response

bp = Blueprint('chat', __name__)

@bp.route('/')
def index():
    """Redirect to the appropriate page based on user's progress."""
    if 'user_id' not in session:
        return redirect(url_for('profile.profile'))
    
    # Check if user has completed profile
    user_id = session['user_id']
    has_profile = UserProfile.get_by_user_id(user_id) is not None
    
    if not has_profile:
        return redirect(url_for('profile.profile'))
    
    # Check if user has set up today's plan
    today = datetime.utcnow().date().isoformat()
    has_today_plan = DailyPlan.get_today_plan(user_id) is not None
    
    if not has_today_plan:
        return redirect(url_for('daily.daily'))
    
    return redirect(url_for('chat.chat'))

@bp.route('/chat')
def chat():
    """Render the main chat interface."""
    if 'user_id' not in session:
        return redirect(url_for('profile.profile'))
    
    user_id = session['user_id']
    user_profile = UserProfile.get_by_user_id(user_id)
    
    if not user_profile:
        return redirect(url_for('profile.profile'))
    
    # Get username from profile answers if available
    username = 'Friend'
    if user_profile and 'answers' in user_profile:
        username = user_profile['answers'].get('name', 'Friend')
    
    return render_template('chat.html', username=username)

@bp.route('/api/chat', methods=['POST'])
def chat_api():
    """Handle chat messages via API."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    user_id = session['user_id']
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    try:
        # Save user message using ChatMessage model
        ChatMessage.create(
            user_id=user_id,
            role='user',
            content=message
        )
        
        # Generate AI response
        response = generate_response(user_id, message)
        
        # Save AI response using ChatMessage model
        ChatMessage.create(
            user_id=user_id,
            role='assistant',
            content=response
        )
        
        return jsonify({
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in chat_api: {str(e)}')
        return jsonify({'error': 'An error occurred'}), 500

@bp.route('/api/chat/history')
def chat_history():
    """Get chat history for the current user."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user_id = session['user_id']
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 messages
        
        # Get messages using ChatMessage model
        messages = ChatMessage.get_user_messages(user_id, limit)
        
        return jsonify({'messages': messages})
        
    except Exception as e:
        current_app.logger.error(f'Error fetching chat history: {str(e)}')
        return jsonify({'error': 'Failed to fetch chat history'}), 500

@bp.route('/api/status', methods=['GET'])
def status():
    """Check the status of the application and user session."""
    status = {
        'authenticated': 'user_id' in session,
        'has_profile': False,
        'has_today_plan': False,
        'status': 'ok'
    }
    
    if 'user_id' in session:
        user_id = session['user_id']
        status['user_id'] = user_id
        
        # Check if user has a profile
        profile = UserProfile.get_by_user_id(user_id)
        status['has_profile'] = profile is not None
        
        # Check if user has a plan for today
        plan = DailyPlan.get_today_plan(user_id)
        status['has_today_plan'] = plan is not None
    
    return jsonify(status)
