from datetime import datetime
from typing import List, Dict, Optional, Any
from bson import ObjectId
from flask import current_app
from .extensions import mongo

# Database collections
def get_collection(name):
    """Get a collection by name."""
    return mongo.db[name]

# Collection properties
def user_profiles():
    """Get the user_profiles collection."""
    return get_collection('user_profiles')

def daily_plans():
    """Get the daily_plans collection."""
    return get_collection('daily_plans')

def chat_messages():
    """Get the chat_messages collection."""
    return get_collection('chat_messages')

class UserProfile:
    """User profile model with enhanced personal details and memory capabilities."""
    
    @staticmethod
    def create(user_id: str, answers: dict) -> dict:
        """Create a new user profile with default personal details."""
        profile = {
            'user_id': user_id,
            'personal_info': {
                'name': answers.get('name', ''),
                'age': answers.get('age', ''),
                'location': answers.get('location', ''),
                'occupation': answers.get('occupation', ''),
                'interests': answers.get('interests', []),
                'goals': answers.get('goals', []),
                'preferences': {
                    'communication_style': 'friendly',
                    'formality': 'casual',
                    'topics': []
                }
            },
            'answers': answers,
            'memories': [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = user_profiles().insert_one(profile)
        profile['_id'] = str(result.inserted_id)
        return profile
    
    @staticmethod
    def get_by_user_id(user_id: str) -> dict:
        """Get a user profile by user ID."""
        profile = user_profiles().find_one({'user_id': user_id})
        if profile and '_id' in profile:
            profile['_id'] = str(profile['_id'])
            
            # Ensure all required fields exist
            if 'personal_info' not in profile:
                profile['personal_info'] = {
                    'name': '',
                    'age': '',
                    'location': '',
                    'occupation': '',
                    'interests': [],
                    'goals': [],
                    'preferences': {
                        'communication_style': 'friendly',
                        'formality': 'casual',
                        'topics': []
                    }
                }
            if 'memories' not in profile:
                profile['memories'] = []
                
        return profile
    
    @staticmethod
    def update(user_id: str, updates: dict) -> bool:
        """Update a user profile."""
        updates['updated_at'] = datetime.utcnow()
        result = user_profiles().update_one(
            {'user_id': user_id},
            {'$set': updates}
        )
        return result.modified_count > 0
    
    @staticmethod
    def add_memory(user_id: str, memory_type: str, content: str, importance: int = 1, tags: list = None) -> bool:
        """Add a new memory to the user's profile."""
        if tags is None:
            tags = []
            
        memory = {
            'type': memory_type,
            'content': content,
            'tags': tags,
            'importance': importance,
            'created_at': datetime.utcnow()
        }
        
        result = user_profiles().update_one(
            {'user_id': user_id},
            {
                '$push': {'memories': memory},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    def get_relevant_memories(user_id: str, query: str = None, limit: int = 5) -> list:
        """Get relevant memories for the user, optionally filtered by query."""
        profile = user_profiles().find_one({'user_id': user_id})
        if not profile or 'memories' not in profile:
            return []
            
        memories = profile.get('memories', [])
        
        # If no query, return most recent memories
        if not query:
            return sorted(memories, key=lambda x: x.get('created_at', datetime.min), reverse=True)[:limit]
            
        # Simple keyword matching for now
        # In a real app, you'd want to use vector similarity search here
        query = query.lower()
        relevant = []
        
        for memory in memories:
            content = memory.get('content', '').lower()
            tags = [t.lower() for t in memory.get('tags', [])]
            
            if (query in content or 
                any(query in tag for tag in tags) or
                query in memory.get('type', '').lower()):
                relevant.append(memory)
                
        # Sort by importance and recency
        relevant.sort(key=lambda x: (
            -x.get('importance', 0),
            x.get('created_at', datetime.min)
        ))
        
        return relevant[:limit]

class DailyPlan:
    """Daily plan model."""
    
    @staticmethod
    def create(user_id: str, date: str, tasks: list, mood: str, mood_note: str = '') -> dict:
        """Create a new daily plan."""
        plan = {
            'user_id': user_id,
            'date': date,
            'tasks': tasks,
            'mood': mood,
            'mood_note': mood_note,
            'created_at': datetime.utcnow()
        }
        result = daily_plans().insert_one(plan)
        plan['_id'] = str(result.inserted_id)
        return plan
    
    @staticmethod
    def get_today_plan(user_id: str, date: str = None) -> dict:
        """Get today's plan for a user."""
        if date is None:
            date = datetime.utcnow().date().isoformat()
            
        plan = daily_plans().find_one({
            'user_id': user_id,
            'date': date
        })
        
        if plan and '_id' in plan:
            plan['_id'] = str(plan['_id'])
        return plan
    
    @staticmethod
    def update_or_create(user_id: str, date: str, updates: dict) -> dict:
        """Update or create a daily plan."""
        updates['updated_at'] = datetime.utcnow()
        
        result = daily_plans().update_one(
            {'user_id': user_id, 'date': date},
            {'$set': updates},
            upsert=True
        )
        
        if result.upserted_id:
            return {'_id': str(result.upserted_id), **updates}
        
        plan = daily_plans().find_one({'user_id': user_id, 'date': date})
        if plan and '_id' in plan:
            plan['_id'] = str(plan['_id'])
        return plan
        
    @staticmethod
    def get_incomplete_tasks_before(user_id: str, before_date: datetime) -> List[Dict]:
        """
        Get all incomplete tasks before a specific date.
        
        Args:
            user_id: The user's unique identifier
            before_date: Get tasks before this date
            
        Returns:
            List of tasks with their plan dates
        """
        try:
            # Find all plans before the specified date
            plans = daily_plans().find({
                'user_id': user_id,
                'date': {'$lt': before_date.isoformat()}
            })
            
            incomplete_tasks = []
            
            for plan in plans:
                if not isinstance(plan, dict):
                    current_app.logger.warning(f"Unexpected plan format: {plan}")
                    continue
                    
                try:
                    # Handle both string and datetime plan dates
                    plan_date = plan.get('date')
                    if isinstance(plan_date, str):
                        plan_date = datetime.fromisoformat(plan_date)
                    elif not isinstance(plan_date, datetime):
                        plan_date = datetime.utcnow()
                        
                    tasks = plan.get('tasks', [])
                    if not isinstance(tasks, list):
                        current_app.logger.warning(f"Unexpected tasks format in plan {plan.get('_id')}: {tasks}")
                        continue
                    
                    for task in tasks:
                        try:
                            # Skip if task is not a dictionary
                            if not isinstance(task, dict):
                                current_app.logger.warning(f"Skipping non-dict task: {task}")
                                continue
                                
                            # Check if task is incomplete (completed is either False or not set)
                            completed = task.get('completed')
                            if completed is True:
                                continue
                                
                            # Get task description, default to 'Unnamed task' if not available
                            description = task.get('description')
                            if not description:
                                if 'text' in task:  # Try alternate field names
                                    description = task['text']
                                elif 'name' in task:
                                    description = task['name']
                                else:
                                    description = 'Unnamed task'
                            
                            incomplete_tasks.append({
                                'description': description,
                                'due_date': plan_date,
                                'plan_date': plan_date,
                                'task_id': str(task.get('id') or task.get('_id') or ''),
                                'raw_task': task  # Include raw task for debugging
                            })
                            
                        except Exception as task_error:
                            current_app.logger.error(f"Error processing task {task}: {str(task_error)}", 
                                                  exc_info=True)
                            continue
                            
                except Exception as plan_error:
                    current_app.logger.error(f"Error processing plan {plan.get('_id')}: {str(plan_error)}", 
                                          exc_info=True)
                    continue
            
            return incomplete_tasks
            
        except Exception as e:
            current_app.logger.error(f"Error in get_incomplete_tasks_before: {str(e)}", exc_info=True)
            return []

class ChatMessage:
    """Chat message model."""
    
    @staticmethod
    def create(user_id: str, role: str, content: str, **metadata) -> dict:
        """Create a new chat message."""
        message = {
            'user_id': user_id,
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'timestamp': datetime.utcnow(),
            **metadata
        }
        result = chat_messages().insert_one(message)
        message['_id'] = str(result.inserted_id)
        return message
    
    @staticmethod
    def get_user_messages(user_id: str, limit: int = 50) -> list:
        """Get recent chat messages for a user."""
        messages = chat_messages().find(
            {'user_id': user_id}
        ).sort('timestamp', -1).limit(limit)
        
        result = []
        for msg in messages:
            if '_id' in msg:
                msg['_id'] = str(msg['_id'])
                if 'timestamp' in msg:
                    msg['timestamp'] = msg['timestamp'].isoformat()
                result.append(msg)
        return result
    
    @staticmethod
    def get_conversation_history(user_id: str, limit: int = 10) -> list:
        """Get recent conversation history for context."""
        messages = chat_messages().find(
            {'user_id': user_id}
        ).sort('timestamp', -1).limit(limit)
        
        result = []
        for msg in reversed(list(messages)):
            if 'role' in msg and 'content' in msg and 'timestamp' in msg:
                result.append({
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp'].isoformat()
                })
        return result


def create_indexes():
    """Create database indexes for better query performance."""
    try:
        # Create indexes for user_profiles collection
        user_profiles().create_index('user_id', unique=True)
        
        # Create indexes for daily_plans collection
        daily_plans().create_index([('user_id', 1), ('date', 1)], unique=True)
        
        # Create indexes for chat_messages collection
        chat_messages().create_index([('user_id', 1), ('timestamp', -1)])
        chat_messages().create_index('timestamp', expireAfterSeconds=60*60*24*30)  # Auto-expire after 30 days
        
        current_app.logger.info("Database indexes created successfully")
    except Exception as e:
        current_app.logger.error(f"Error creating database indexes: {str(e)}")
        raise
