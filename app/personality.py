"""
Personality module for the AI companion.
Defines different personality aspects, tones, and behaviors with a focus on natural, human-like interaction.
"""
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple, Any
import random
import re
from enum import Enum, auto

class ConversationTone(Enum):
    """Different tones the AI can use in conversation."""
    CASUAL = auto()
    PROFESSIONAL = auto()
    ENCOURAGING = auto()
    PLAYFUL = auto()
    EMPATHETIC = auto()
    MOTIVATIONAL = auto()
    FIRM = auto()
    
class TimeOfDay(Enum):
    """Different times of day for appropriate greetings and responses."""
    MORNING = (5, 11)    # 5am - 11:59am
    AFTERNOON = (12, 16) # 12pm - 4:59pm
    EVENING = (17, 21)   # 5pm - 9:59pm
    NIGHT = (22, 4)      # 10pm - 4:59am

class PersonalityTraits:
    """
    Defines the core personality traits and conversational style of the AI companion.
    Designed to create natural, engaging, and human-like interactions.
    """
    
    def __init__(self):
        # Core personality traits with intensity scores (1-10)
        self.traits = {
            'warmth': 9,           # Friendly and approachable
            'humor': 7,            # Playful and fun
            'empathy': 9,          # Understanding and caring
            'curiosity': 8,        # Interested in the user
            'authenticity': 9,     # Genuine and real
            'positivity': 8,       # Optimistic outlook
            'reliability': 10,     # Dependable and consistent
            'playfulness': 7,      # Light-hearted and fun
            'wisdom': 8,           # Thoughtful and insightful
            'passion': 7           # Enthusiastic and engaged
        }
        
        # Current conversation context
        self.context = {
            'last_topic': None,
            'user_mood': None,
            'last_interaction': None,
            'conversation_history': [],
            'user_preferences': {}
        }
        
        # Different interaction styles with weights for random selection
        self.styles = {
            'supportive': (self._supportive_style, 0.4),
            'motivational': (self._motivational_style, 0.3),
            'playful': (self._playful_style, 0.2),
            'firm': (self._firm_style, 0.1)
        }
        
        # Conversation fillers and natural language patterns
        self.conversation_patterns = {
            'acknowledgments': [
                "Hmm, I see...", "Got it!", "Makes sense!", "I hear you.",
                "That's interesting!", "No way!", "Really?", "Wow!",
                "I get that.", "Tell me more.", "And then what?", "Seriously?"
            ],
            'agreements': [
                "Totally!", "Absolutely!", "For sure!", "Definitely!",
                "100%!", "No doubt!", "You're right!", "I agree!"
            ],
            'transitions': [
                "Anyway...", "So...", "By the way...", "Speaking of which...",
                "Random thought...", "You know what's funny?", "Wait, I just remembered..."
            ],
            'fillers': [
                "Hmm", "Well", "You know", "I mean", "Like", "So",
                "Actually", "Basically", "Honestly", "Seriously",
                "I guess", "I suppose", "Kinda", "Sort of"
            ]
        }
        
        # Time-based greetings with more personality
        self.greetings = {
            'morning': [
                "Mornin' sunshine! ☀️ Ready to make today amazing?",
                "Rise and shine! What's cookin', good lookin'? 😄",
                "Top of the morning to you! What's the game plan for today?",
                "Hey early bird! Catch any worms yet? 🐦"
            ],
            'afternoon': [
                "Afternoon! How's your day treating you so far?",
                "Hey there! How's it going? Need a quick break? ☕",
                "Afternoon vibes! What's shakin', bacon? 🥓",
                "Hope you're having a fab day! What's new?"
            ],
            'evening': [
                "Evening! How was your day? Spill the tea! ☕",
                "Hey you! How'd today treat you? 🌆",
                "Evening, night owl! What's the haps?",
                "How's your evening shaping up? Need to vent or celebrate? 🎉"
            ],
            'late_night': [
                "Still up? Don't make me turn this app into a bedtime story generator! 😴",
                "Past your bedtime, isn't it? Or are we having a late-night genius moment? 🌙",
                "Late night crew represent! What's keeping you up?",
                "You know what they say about burning the midnight oil... it leads to great conversations!"
            ]
        }
        
        # Emoji mapping for different emotions
        self.emojis = {
            'happy': ['😊', '😄', '😃', '😁', '😆', '🤗'],
            'sad': ['😔', '😢', '😞', '😕', '😟'],
            'excited': ['🤩', '🎉', '✨', '😆', '🤯'],
            'thinking': ['🤔', '🧐', '💭', '💡'],
            'love': ['❤️', '💕', '💖', '😍', '🥰'],
            'playful': ['😜', '🤪', '😝', '🤗', '😎']
        }
        
        # Motivational and supportive phrases
        self.encouragements = [
            "You're doing better than you think! Progress, not perfection, right?",
            "Remember how far you've come, not just how far you have to go.",
            "One step at a time - you've got this! 💪",
            "Small progress is still progress. Keep going! 🚀",
            "Every expert was once a beginner. You're on your way! 🌟",
            "The fact that you're trying says a lot about you. Keep at it! 😊",
            "You're stronger than you think. I believe in you! ✨"
        ]
        
        # Conversation memory tracking
        self.conversation_history = []
        self.last_interaction_time = datetime.now()
    
    def get_time_based_greeting(self, user_name: str = None) -> str:
        """
        Get an appropriate greeting based on the time of day with natural variations.
        
        Args:
            user_name: Optional name for personalization
            
        Returns:
            str: A natural-sounding greeting
        """
        current_hour = datetime.now().hour
        
        # Determine time of day category
        if 5 <= current_hour < 12:
            time_category = 'morning'
        elif 12 <= current_hour < 17:
            time_category = 'afternoon'
        elif 17 <= current_hour < 22:
            time_category = 'evening'
        else:
            time_category = 'late_night'
        
        # Select a random greeting
        greeting = random.choice(self.greetings[time_category])
        
        # Personalize if name is available
        if user_name and random.random() > 0.3:  # 70% chance to use name
            greeting = greeting.replace('!', f', {user_name}!')
            greeting = greeting.replace('.', f', {user_name}.')
            greeting = greeting.replace('?', f', {user_name}?')
        
        # Add some variety with occasional follow-up questions
        if random.random() > 0.7:  # 30% chance to add a follow-up
            follow_ups = [
                " What's on your mind today?",
                " How are you feeling?",
                " What's new with you?",
                " What's the plan for today?"
            ]
            greeting += random.choice(follow_ups)
            
        return greeting
    
    def get_encouragement(self, context: str = None) -> str:
        """
        Get an encouraging message, optionally related to a specific context.
        
        Args:
            context: Optional context for the encouragement
            
        Returns:
            str: An encouraging message
        """
        encouragement = random.choice(self.encouragements)
        
        # Add context if provided
        if context:
            if random.random() > 0.5:
                encouragement = f"About {context.lower()}, {encouragement.lower()}"
            else:
                encouragement = f"{encouragement} About {context.lower()}, remember..."
        
        # Add occasional emoji
        if random.random() > 0.7:  # 30% chance to add emoji
            emoji = random.choice(self.emojis['happy'] + self.emojis['excited'])
            encouragement += f" {emoji}"
            
        return encouragement
    
    def _supportive_style(self, message: str, user_name: str = None) -> str:
        """
        Format message in a warm, supportive style.
        
        Args:
            message: The base message
            user_name: Optional name for personalization
            
        Returns:
            str: A supportive version of the message
        """
        name = user_name or ''
        
        supportive_phrases = [
            "I believe in you" + (f", {name}!" if name else "!"),
            "You've got this" + (f", {name}!" if name else "!"),
            "I'm here for you, every step of the way.",
            "Remember how far you've come" + (f", {name}!" if name else "!"),
            "Sending you good vibes! ✨",
            "I'm in your corner! 🥊"
        ]
        
        # Add some natural variation
        if random.random() > 0.7:  # 30% chance to add a follow-up
            follow_ups = [
                " How does that sound?",
                " What do you think?",
                " You with me?",
                " Cool?"
            ]
            return f"{message} {random.choice(supportive_phrases)}{random.choice(follow_ups)}"
            
        return f"{message} {random.choice(supportive_phrases)}"
    
    def _motivational_style(self, message: str, user_name: str = None) -> str:
        """
        Format message in an uplifting, motivational style.
        
        Args:
            message: The base message
            user_name: Optional name for personalization
            
        Returns:
            str: A motivational version of the message
        """
        name = user_name or ''
        
        motivational_phrases = [
            f"Let's turn those dreams into plans{' like the rockstar you are' if random.random() > 0.7 else ''}!",
            "Every small step counts! Rome wasn't built in a day, right? 🏛️",
            f"You're capable of amazing things{' when you put your mind to it' if random.random() > 0.5 else ''}!",
            "Success is built one day at a time, and you're doing great! 🚀",
            f"The only limit is the one you set for yourself{' ' + name if name and random.random() > 0.6 else ''}!"
        ]
        
        # Add some enthusiasm
        if random.random() > 0.6:  # 40% chance to add emphasis
            emphasis = ["💪", "✨", "🔥", "🚀", "🌟"][random.randint(0, 4)]
            return f"{message} {random.choice(motivational_phrases)} {emphasis}"
            
        return f"{message} {random.choice(motivational_phrases)}"
    
    def _firm_style(self, message: str, user_name: str = None) -> str:
        """
        Format message in a firm but caring style.
        
        Args:
            message: The base message
            user_name: Optional name for personalization
            
        Returns:
            str: A firm but caring version of the message
        """
        name = user_name or ''
        
        firm_openings = [
            "I need to be real with you: ",
            "Let's be honest here: ",
            "I'm saying this because I care: ",
            "Time for some tough love: "
        ]
        
        firm_closings = [
            " I know you can handle this.",
            " You're stronger than you think.",
            " I believe in your ability to do this.",
            " Let's tackle this together."
        ]
        
        # Construct the firm but caring message
        opening = random.choice(firm_openings)
        closing = random.choice(firm_closings)
        
        # Add name if available
        if name and random.random() > 0.7:  # 30% chance to use name
            closing = f" {name}, {closing.lstrip()}"
            
        return f"{opening}{message}{closing}"
    
    def _playful_style(self, message: str, user_name: str = None) -> str:
        """
        Format message in a fun, playful style.
        
        Args:
            message: The base message
            user_name: Optional name for personalization
            
        Returns:
            str: A playful version of the message
        """
        name = user_name or ''
        
        # Add playful elements to the message
        playful_elements = [
            (" ", [" 😊", " 😄", " 😎", " 🤔", " 🤗"][random.randint(0, 4)]),
            (".", ["! 😊", "! 🎉", ". 😄", ". 😊", "."][random.randint(0, 4)]),
            ("?", ["? 🤔", "? 🧐", "?"][random.randint(0, 2)])
        ]
        
        # Add emojis based on punctuation
        for punct, replacement in playful_elements:
            if punct in message and random.random() > 0.7:  # 30% chance per punctuation
                parts = message.split(punct)
                if len(parts) > 1:
                    message = replacement.join(parts[:-1]) + punct + parts[-1]
        
        # Add occasional playful phrases
        if random.random() > 0.8:  # 20% chance to add a playful phrase
            playfulness = [
                "Just saying!",
                "No pressure though!",
                "Easy peasy!",
                "Piece of cake!",
                "You know what I mean?",
                "Right?",
                "Am I right or am I right?",
                "Boom! 💥"
            ]
            message = f"{message} {random.choice(playfulness)}"
        
        # Add playful nickname if name is available
        if name and random.random() > 0.7:  # 30% chance to use a nickname
            nicknames = [
                f"{name}-inator",
                f"Captain {name}",
                f"{name} the Great",
                f"Super {name}",
                f"{name} Mc{name}face"
            ]
            message = message.replace(name, random.choice(nicknames))
        
        return message
    
    def get_style(self, style_name: str, message: str, user_name: str = None) -> str:
        """
        Apply the specified style to a message with natural variations.
        
        Args:
            style_name: Name of the style to apply
            message: The message to style
            user_name: Optional name for personalization
            
        Returns:
            str: The styled message
        """
        # Get the style function and weight
        style_info = self.styles.get(style_name.lower(), (self._supportive_style, 0.4))
        style_func, _ = style_info
        
        # Apply the style
        styled_message = style_func(message, user_name)
        
        # Sometimes add a conversational filler at the start
        if random.random() > 0.7:  # 30% chance to add a filler
            fillers = [
                "You know",
                "Well",
                "So",
                "I mean",
                "Honestly",
                "Actually"
            ]
            if random.random() > 0.5:  # 50% chance to add a comma
                styled_message = f"{random.choice(fillers)}, {styled_message[0].lower()}{styled_message[1:]}"
            else:
                styled_message = f"{random.choice(fillers)}... {styled_message}"
        
        return styled_message
    
    def get_response(self, message: str, user_name: str = None, context: Dict = None) -> str:
        """
        Generate a natural-sounding response to the user's message.
        
        Args:
            message: The user's message
            user_name: Optional name for personalization
            context: Optional context about the conversation
            
        Returns:
            str: A natural-sounding response
        """
        # Update conversation history (for context, not shown to user)
        self._update_conversation_history(message, user_name, is_user=True)
        
        # Clean and normalize the message
        message = message.lower().strip()
        
        # Choose a random style based on weights
        styles = list(self.styles.items())
        style_names = [s[0] for s in styles]
        weights = [s[1][1] for s in styles]
        chosen_style = random.choices(style_names, weights=weights, k=1)[0]
        
        # Generate a base response based on message content
        if not message or message in ['hi', 'hello', 'hey']:
            response = self.get_time_based_greeting(user_name)
        elif '?' in message:
            response = self._generate_question_response(message, user_name)
        elif any(word in message for word in ['work', 'task', 'todo', 'do today']):
            response = self._handle_work_related(message, user_name)
        elif any(word in message for word in ['meet', 'see', 'hang out', 'get together']):
            response = self._handle_meet_someone(message, user_name)
        else:
            response = self._generate_statement_response(message, user_name)
        
        # Apply the chosen style
        styled_response = self.get_style(chosen_style, response, user_name)
        
        # Sometimes add a follow-up question (40% chance)
        if random.random() > 0.6:
            follow_ups = [
                " What do you think?",
                " How does that sound?",
                " What's on your mind about that?",
                " What else is going on?",
                " How's everything else?"
            ]
            styled_response += random.choice(follow_ups)
        
        # Update conversation history with AI response
        self._update_conversation_history(styled_response, "AI", is_user=False)
        
        return styled_response
        
    def _handle_work_related(self, message: str, user_name: str = None) -> str:
        """Handle work/task related messages in a conversational way."""
        responses = [
            "Work stuff, huh? Let's tackle this one step at a time. What's the most important thing on your plate right now?",
            "I'm here to help with your tasks! What would you like to focus on first?",
            "Let's make today productive! What's one thing you'd like to accomplish?",
            "Work can be overwhelming sometimes. Let's break it down - what's your top priority?"
        ]
        return random.choice(responses)
        
    def _handle_meet_someone(self, message: str, user_name: str = None) -> str:
        """Handle messages about meeting people in a natural way."""
        name = user_name or 'there'
        responses = [
            f"That sounds great, {name}! Meeting new people can be really exciting. What kind of person are you hoping to connect with?",
            f"I'd love to help you meet someone, {name}! What are some of your interests? That might help find common ground.",
            f"Meeting new people is always an adventure! What kind of activities do you enjoy? That could be a great way to connect with others.",
            f"That's a wonderful idea! Meeting new people can lead to amazing opportunities. What's drawing you to want to connect with someone new?"
        ]
        return random.choice(responses)
    
    def _generate_question_response(self, question: str, user_name: str = None) -> str:
        """Generate a natural-sounding response to a question."""
        name = user_name or ''
        
        # Categorize question type based on keywords
        question = question.lower()
        
        if any(word in question for word in ['how are you', 'how do you do', "how's it going"]):
            responses = [
                "I'm doing well, thanks for asking! How about you?",
                "I'm great! Just here to help you out. What's new with you?",
                "Doing good! What's on your mind today?"
            ]
        elif any(word in question for word in ['what', 'when', 'where', 'why', 'how', 'who', 'which']):
            responses = [
                "That's an interesting question. What's making you ask?",
                "I'd love to help with that. Could you tell me more about what you're thinking?",
                "Hmm, that makes me curious too. What are your thoughts on it?"
            ]
        elif any(word in question for word in ['can you', 'could you', 'would you']):
            responses = [
                "I'll do my best to help with that. What specifically do you need?",
                "I can certainly try! Tell me more about what you're looking for.",
                "I'd be happy to help. Could you give me a bit more detail?"
            ]
        else:
            responses = [
                "That's a great question! What's your take on it?",
                "Hmm, interesting point. What made you think of that?",
                "I've been wondering about that too. What are your thoughts?"
            ]
            
        return random.choice(responses)
    
    def _generate_statement_response(self, statement: str, user_name: str = None) -> str:
        """Generate a natural response to a statement."""
        name = user_name or ''
        statement = statement.lower()
        
        # Check for different types of statements
        if any(word in statement for word in ['i feel', "i'm feeling", 'i am feeling']):
            responses = [
                f"I hear you, {name}. What's been on your mind?" if name else "I hear you. What's been on your mind?",
                "That's completely valid. Want to talk more about it?",
                "I understand. Sometimes putting feelings into words helps. What else is going on?"
            ]
        elif any(word in statement for word in ['i need', 'i want', 'i would like']):
            responses = [
                "I'm listening. Tell me more about what you're looking for.",
                "I hear you. What would be most helpful right now?",
                "I understand. What's the best way I can support you with that?"
            ]
        elif any(word in statement for word in ['i think', 'i believe', 'in my opinion']):
            responses = [
                "That's an interesting perspective. What led you to that thought?",
                "I see where you're coming from. What else do you think about that?",
                "That's a thoughtful point. How did you arrive at that conclusion?"
            ]
        else:
            # Generic but natural-sounding responses
            responses = [
                "I see. What else is happening with you?",
                "Got it. What's new on your end?",
                "I understand. What's been keeping you busy lately?",
                "Makes sense. How's everything else going?"
            ]
            
        return random.choice(responses)
    
    def _update_conversation_history(self, message: str, sender: str, is_user: bool = True) -> None:
        """Update the conversation history."""
        self.conversation_history.append({
            'message': message,
            'sender': 'user' if is_user else 'ai',
            'name': sender,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only the last 20 messages to prevent memory issues
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        self.last_interaction_time = datetime.now()
    
    def check_urgent_tasks(self, tasks: List[Dict]) -> Optional[str]:
        """Check for urgent or overdue tasks."""
        now = datetime.now()
        urgent_tasks = []
        
        for task in tasks:
            due_date = task.get('due_date')
            if due_date and isinstance(due_date, str):
                try:
                    due_date = datetime.fromisoformat(due_date)
                    if due_date < now and not task.get('completed', False):
                        urgent_tasks.append(task)
                except (ValueError, TypeError):
                    continue
        
        if urgent_tasks:
            task_list = '\n'.join([f"- {t['description']}" for t in urgent_tasks[:3]])
            return self.get_style('firm', 
                f"⚠️ You have {len(urgent_tasks)} overdue task{'s' if len(urgent_tasks) > 1 else ''}:\n{task_list}\n\nLet's tackle these together! Which one should we start with?"
            )
        return None

# Create a global instance
personality = PersonalityTraits()
