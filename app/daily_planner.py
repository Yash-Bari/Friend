from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from datetime import datetime, date
from bson import ObjectId
from .models import DailyPlan
from . import memory_system

bp = Blueprint('daily', __name__, url_prefix='/daily')

@bp.route('/', methods=['GET', 'POST'])
def daily():
    """Handle daily planning and mood tracking."""
    if 'user_id' not in session:
        return redirect(url_for('profile.profile'))
    
    user_id = session['user_id']
    today = date.today().isoformat()
    
    if request.method == 'POST':
        # Get form data
        tasks_raw = request.form.getlist('tasks[]')
        mood = request.form.get('mood', '').strip()
        
        # Filter out empty tasks and format as dictionaries
        tasks = []
        for i, task in enumerate(tasks_raw):
            if task.strip():
                tasks.append({
                    'id': str(ObjectId()),  # Generate unique ID
                    'description': task.strip(),
                    'completed': False,
                    'created_at': datetime.utcnow().isoformat()
                })
        
        # Prepare plan data
        plan_data = {
            'tasks': tasks,
            'mood': mood,
            'mood_note': request.form.get('mood_note', '').strip()
        }
        
        # Update or create the daily plan using the model
        DailyPlan.update_or_create(
            user_id=user_id,
            date=today,
            updates=plan_data
        )
        
        # Save to vector memory
        task_descriptions = [task['description'] for task in tasks]
        memory_text = f"Today's mood: {mood}. Tasks: {', '.join(task_descriptions)}"
        try:
            memory_system.save_memory(
                user_id=user_id,
                text=memory_text,
                tags=['daily_plan', 'mood'],
                metadata={
                    'type': 'daily_plan',
                    'date': today,
                    'mood': mood,
                    'task_count': len(tasks)
                }
            )
        except Exception as e:
            current_app.logger.error(f"Error saving daily plan to memory: {str(e)}")
            # Continue even if memory save fails
        
        return redirect(url_for('chat.chat'))
    
    # For GET request, check if today's plan exists
    today_plan = DailyPlan.get_today_plan(user_id, today)
    
    return render_template('daily.html', today_plan=today_plan)

@bp.route('/today', methods=['GET'])
def get_today_plan():
    """Get today's plan for the current user."""
    if 'user_id' not in session:
        return jsonify({'error': 'No user session'}), 401
    
    # Get today's plan if it exists
    plan = DailyPlan.get_today_plan(session['user_id'], date.today().isoformat())
    
    # Get previous plans for reference
    # Note: This would need a new method in DailyPlan model
    # For now, we'll just pass an empty list
    previous_plans = []
    
    if plan:
        # Convert ObjectId to string for JSON serialization
        plan['_id'] = str(plan['_id'])
        return jsonify(plan)
    else:
        return jsonify({'error': 'No plan for today'}), 404
