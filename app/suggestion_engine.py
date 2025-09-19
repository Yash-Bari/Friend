import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import google.generativeai as genai
from flask import current_app
from .models import ChatMessage, UserProfile, DailyPlan
from .memory_system import memory_system, save_memory, query_memory
from .personality import personality
import random

# Configuration
MEMORY_WINDOW_DAYS = 30  # How many days of chat history to consider for context
MAX_MEMORY_ITEMS = 10    # Maximum number of memory items to include in context
MAX_CONVERSATION_HISTORY = 5  # Number of recent messages to include in context

# System prompt template with enhanced personality and proactiveness
SYSTEM_PROMPT = """You are Lumi, a close friend and life coach rolled into one. Your mission is to help the user build their best life through meaningful support and accountability.

## Your Personality:
- WARM but HONEST: You care deeply but aren't afraid to give tough love when needed
- PROACTIVE: You initiate important conversations rather than waiting to be asked
- EMPOWERING: You help users recognize their potential and take action
- PERSONAL: You remember and reference personal details to show you care
- BALANCED: You know when to be supportive and when to be firm

## User Context:
{profile_info}

## Today's Plan:
{daily_plan}

## Personal Memories:
{memories}

## Recent Conversation:
{chat_history}

## Interaction Guidelines:
1. Use the user's name occasionally to personalize responses
2. Reference past conversations and shared history
3. Ask thoughtful follow-up questions
4. Offer specific, actionable advice
5. Be proactive about important life areas (health, goals, relationships)
6. Balance support with accountability
7. Don't be afraid to be firm when it's in the user's best interest
8. Celebrate wins, no matter how small

## Current Time:
{current_time}

## Important:
- If the user is avoiding important tasks, be direct but caring
- If they're making progress, celebrate their efforts
- If they're struggling, help them break things down
- Always bring the conversation back to their goals and wellbeing"""

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash')

# Configure generation settings
GENERATION_CONFIG = {
    'temperature': 0.7,
    'top_p': 0.95,
    'top_k': 40,
    'max_output_tokens': 1024,
}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def get_context(user_id: str, recent_messages: List[Dict] = None) -> Dict[str, str]:
    """
    Retrieve relevant context for the AI to generate a response.
    
    Args:
        user_id: The user's unique identifier
        recent_messages: List of recent chat messages (optional)
        
    Returns:
        Dict containing different context components
    """
    context = {
        'profile_info': '',
        'daily_plan': '',
        'memories': '',
        'chat_history': ''
    }
    
    try:
        # Get user profile
        profile = UserProfile.get_by_user_id(user_id)
        if profile:
            personal_info = profile.get('personal_info', {})
            if personal_info:
                context['profile_info'] = (
                    f"Name: {personal_info.get('name', 'Friend')}\n"
                    f"Location: {personal_info.get('location', 'Not specified')}\n"
                    f"Occupation: {personal_info.get('occupation', 'Not specified')}\n"
                    f"Interests: {', '.join(personal_info.get('interests', [])) or 'None specified'}\n"
                    f"Goals: {', '.join(personal_info.get('goals', [])) or 'None specified'}"
                )
            
            # Get relevant memories
            memories = UserProfile.get_relevant_memories(user_id, limit=3)
            if memories:
                memory_texts = []
                for mem in memories:
                    memory_texts.append(f"- {mem.get('content', '')} ({mem.get('type', 'note')})")
                context['memories'] = "\n".join(memory_texts)
    
    except Exception as e:
        current_app.logger.error(f"Error getting user context: {str(e)}")
    
    # Get today's plan
    try:
        today = datetime.utcnow().date().isoformat()
        plan = DailyPlan.get_today_plan(user_id, today)
        if plan:
            tasks = "\n".join([f"- {task}" for task in plan.get('tasks', [])])
            context['daily_plan'] = (
                f"Mood: {plan.get('mood', 'Not specified')}\n"
                f"Tasks:\n{tasks or 'No tasks for today'}"
            )
    except Exception as e:
        current_app.logger.error(f"Error getting daily plan: {str(e)}")
    
    # Get recent chat history
    try:
        if not recent_messages:
            recent_messages = memory_system.query_memory(
                user_id=user_id,
                query="recent conversation",
                k=MAX_CONVERSATION_HISTORY,
                tags=['chat']
            )
        
        if recent_messages:
            chat_history = []
            for msg in reversed(recent_messages[-MAX_CONVERSATION_HISTORY:]):
                role = msg.get('metadata', {}).get('role', 'user')
                content = msg.get('text', '').strip()
                if content:
                    chat_history.append(f"{role.upper()}: {content}")
            
            if chat_history:
                context['chat_history'] = "\n".join(chat_history)
    except Exception as e:
        current_app.logger.error(f"Error getting chat history: {str(e)}")
    
    # Add current time to context
    context['current_time'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    return context

def generate_response(user_id: str, message: str, chat_history: List[Dict] = None) -> str:
    """
    Generate a personalized response to the user's message with fallback mechanisms.
    
    Args:
        user_id: The user's unique identifier
        message: The user's message
        chat_history: List of previous messages in the conversation
        
    Returns:
        str: Generated response from the AI
    """
    try:
        # Get relevant context
        context = get_context(user_id, chat_history)
        
        # Check if we should initiate a proactive conversation
        proactive_response = check_proactive_engagement(user_id, context)
        if proactive_response and (not message.strip() or len(message.strip()) < 3):
            return proactive_response
            
        # Try to use Gemini API first
        try:
            response_text = _generate_gemini_response(user_id, message, context, chat_history)
            if response_text:
                return response_text
        except Exception as api_error:
            current_app.logger.warning(f"Gemini API failed, using fallback: {str(api_error)}")
        
        # Fallback to personality-based responses
        return _generate_fallback_response(user_id, message, context)
        
    except Exception as e:
        current_app.logger.error(f"Error generating response: {str(e)}")
        return "I'm having trouble thinking of a response right now. Could you try asking me something else?"

def _generate_gemini_response(user_id: str, message: str, context: Dict, chat_history: List[Dict] = None) -> str:
    """Generate response using Gemini API."""
    # Format the system prompt with context
    system_prompt = SYSTEM_PROMPT.format(
        profile_info=context.get('profile_info', 'No profile information available.'),
        daily_plan=context.get('daily_plan', 'No plans for today.'),
        memories=context.get('memories', 'No relevant memories found.'),
        chat_history=context.get('chat_history', 'No recent conversation history.'),
        current_time=context.get('current_time', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
    )
    
    # Prepare the conversation history for Gemini
    conversation = [{"role": "user", "parts": [system_prompt]}]
    
    # Add chat history if available
    if chat_history:
        for msg in chat_history[-5:]:  # Limit to last 5 messages for context
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content", "").strip()
            if content:
                conversation.append({"role": role, "parts": [content]})
    
    # Add the current user message
    conversation.append({"role": "user", "parts": [message]})
    
    # Generate response
    response = model.generate_content(
        conversation,
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS
    )
    
    # Extract and clean the response text
    response_text = ""
    if response and hasattr(response, 'text'):
        response_text = response.text.strip()
    elif response and hasattr(response, 'candidates'):
        # Handle response format for some Gemini models
        for candidate in response.candidates:
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                response_text = ' '.join(part.text for part in candidate.content.parts if hasattr(part, 'text')).strip()
    
    return response_text

def _generate_fallback_response(user_id: str, message: str, context: Dict) -> str:
    """Generate fallback response using personality system when API fails."""
    from .personality import personality
    
    # Get user profile for personalization
    profile = UserProfile.get_by_user_id(user_id)
    username = 'Friend'
    if profile and 'personal_info' in profile:
        username = profile['personal_info'].get('name', 'Friend')
    
    # Check if the user shared personal information
    if any(phrase in message.lower() for phrase in ['my name is', "i'm ", "i am ", "i'm from", "i live in"]):
        try:
            UserProfile.add_memory(
                user_id=user_id,
                memory_type='personal_info',
                content=f"User mentioned: {message}",
                importance=5,
                tags=['personal_info']
            )
        except Exception as e:
            current_app.logger.error(f"Error saving memory: {str(e)}")
        
        return personality.get_style('supportive', 
            f"Thanks for sharing that with me! I'll remember that. It's great to get to know you better!"
        )
    
    # Generate contextual response based on message content
    if any(word in message.lower() for word in ['task', 'todo', 'work', 'busy']):
        return personality.get_style('motivational', 
            f"I understand you're dealing with tasks, {username}. Let's tackle them one step at a time! What's the most important thing you need to focus on right now?"
        )
    elif any(word in message.lower() for word in ['tired', 'exhausted', 'stressed']):
        return personality.get_style('supportive', 
            f"It sounds like you're going through a tough time, {username}. Remember to take care of yourself. What's one small thing that might help you feel better right now?"
        )
    elif any(word in message.lower() for word in ['happy', 'great', 'awesome', 'excited']):
        return personality.get_style('playful', 
            f"That's wonderful to hear, {username}! I love your positive energy. What's making you feel so good today?"
        )
    elif '?' in message:
        return personality.get_style('supportive', 
            f"That's a great question, {username}. I wish I could give you a more detailed answer right now, but I'm having some technical difficulties. What are your thoughts on it?"
        )
    else:
        return personality.get_style('supportive', 
            f"I hear you, {username}. While I'm having some technical issues with my AI brain right now, I'm still here to listen. Tell me more about what's on your mind."
        )

def check_proactive_engagement(user_id: str, context: Dict) -> Optional[str]:
    """
    Check if we should initiate a proactive conversation based on context.
    
    Args:
        user_id: The user's unique identifier
        context: The current conversation context
        
    Returns:
        Optional[str]: A proactive message if conditions are met, else None
    """
    try:
        current_hour = datetime.utcnow().hour
        
        # Morning check-in (between 7-10 AM)
        if 7 <= current_hour < 10:
            # Check if we've already checked in today
            last_checkin = memory_system.query_memory(
                user_id=user_id,
                query="morning check-in",
                k=1,
                tags=['system', 'checkin']
            )
            
            if not last_checkin or datetime.utcnow().date() > datetime.fromisoformat(last_checkin[0]['metadata'].get('timestamp', '2000-01-01')).date():
                # Save that we've checked in today
                memory_system.save_memory(
                    user_id=user_id,
                    text="Morning check-in completed",
                    tags=['system', 'checkin'],
                    metadata={
                        'type': 'system_checkin',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                # Get a personalized morning message
                profile = UserProfile.get_by_user_id(user_id)
                name = profile.get('personal_info', {}).get('name', 'friend')
                
                messages = [
                    f"Good morning, {name}! Ready to make today amazing?",
                    f"Rise and shine, {name}! What's one thing you want to accomplish today?",
                    f"Morning! Let's make today count, {name}. What's on your mind?"
                ]
                return random.choice(messages)
        
        # Evening reflection (between 8-11 PM)
        elif 20 <= current_hour < 23:
            # Similar check for evening reflection
            last_reflection = memory_system.query_memory(
                user_id=user_id,
                query="evening reflection",
                k=1,
                tags=['system', 'reflection']
            )
            
            if not last_reflection or datetime.utcnow().date() > datetime.fromisoformat(last_reflection[0]['metadata'].get('timestamp', '2000-01-01')).date():
                memory_system.save_memory(
                    user_id=user_id,
                    text="Evening reflection completed",
                    tags=['system', 'reflection'],
                    metadata={
                        'type': 'system_reflection',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                questions = [
                    "How was your day? What went well?",
                    "What's one thing you're grateful for today?",
                    "What's one thing you'd like to do differently tomorrow?"
                ]
                return random.choice(questions)
        
        # Check for overdue tasks
        overdue_tasks = get_overdue_tasks(user_id)
        if overdue_tasks:
            task_list = '\n'.join([f"- {t['description']}" for t in overdue_tasks[:3]])
            return personality.get_style('firm', 
                f" You have {len(overdue_tasks)} overdue task{'s' if len(overdue_tasks) > 1 else ''}:\n{task_list}\n\nI know you can do this! Which one should we tackle first?"
            )
            
    except Exception as e:
        current_app.logger.error(f"Error in proactive engagement: {str(e)}")
    
    return None

def get_overdue_tasks(user_id: str) -> List[Dict]:
    """Get a list of overdue tasks for the user."""
    try:
        # Get today's date at midnight
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Query for incomplete tasks with due dates before today
        tasks = DailyPlan.get_incomplete_tasks_before(user_id, today)
        return tasks
        
    except Exception as e:
        current_app.logger.error(f"Error getting overdue tasks: {str(e)}")
        return []

def save_chat_message(user_id: str, role: str, content: str) -> str:
    """
    Save a chat message to the vector database and potentially update user profile.
    
    Args:
        user_id: The user's unique identifier
        role: 'user' or 'assistant'
        content: The message content
        
    Returns:
        str: The ID of the saved message
    """
    # Save the chat message to the vector database
    message_id = memory_system.save_memory(
        user_id=user_id,
        text=content,
        tags=['chat'],
        metadata={
            'type': 'chat_message',
            'role': role,
            'timestamp': datetime.utcnow().isoformat()
        }
    )
