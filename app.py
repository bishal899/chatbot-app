import os
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_socketio import SocketIO, emit
import spacy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import wikipediaapi
import random

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')  # Default secret key if not set
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

jokes = [
    "What did one ocean say to the other ocean? Nothing, they just waved."
    "Parallel lines have so much in common. It’s a shame they’ll never meet.",
    "I told my wife she should embrace her mistakes. She gave me a hug.",
    "I'm reading a book on anti-gravity. It's impossible to put down!",
    "I used to play piano by ear, but now I use my hands.",
    "What do you call fake spaghetti? An impasta!",
    "I would tell you a joke about an elevator, but it’s an uplifting experience."
    "How do you organize a space party? You planet."
    "Why did the tomato turn red? Because it saw the salad dressing."
    "Why did the bicycle fall over? Because it was two-tired!"
    "What do you call a can opener that doesn’t work? A can’t opener."
    "How do you catch a squirrel? Climb a tree and act like a nut!"
    "What’s the difference between a hippo and a Zippo? One is heavy, the other is a little lighter."
]

# Initialize Flask extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)
nlp = spacy.load('en_core_web_sm')

# Ensure logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')

# Define User model for database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/message', methods=['POST'])
def handle_message():
    data = request.json
    message = data['message'].lower()
    
    # Handle specific queries
    if 'what is your name' in message:
        response = "My name is Wikipedia Bot. I'm here to assist you with information from Wikipedia."
    else:
        # Default response
        response = "I'm sorry, I don't understand that."
    
    return jsonify({'response': response})

# Rule-based response using spaCy
def get_bot_response(user_input):
    doc = nlp(user_input.lower())

    if "weather" in user_input:
        return get_weather_response(user_input)
    elif "wikipedia" in user_input:
        return get_wikipedia_response(user_input)
    elif any(token.lemma_ == "hello" for token in doc):
        return "Hello! How can I help you today?"
    elif any(token.text == "how" and token.nbor().lemma_ == "be" for token in doc):
        return "I'm just a bot, but I'm doing great! How about you?"
    elif any(token.text == "who" and token.nbor().text == "are" for token in doc):
        return "I am Wikipedia Bot, your friendly assistant for fetching information!"
    elif any(token.text == "what" and token.nbor().text == "is" and token.nbor(2).text == "your" and token.nbor(3).text == "name" for token in doc):
        return "My name is Wikipedia Bot."
    elif any(token.text == "thank" for token in doc):
        return "You're welcome!"
    elif any(token.lemma_ == "bye" for token in doc):
        return "Goodbye! Have a great day!"
    elif any(token.text == "tell" and token.nbor().text == "me" and token.nbor(2).text == "about" for token in doc):
        return "Sure! What would you like to know about?"
    elif any(token.text == "help" for token in doc):
        return "How can I assist you?"
    elif any(token.text == "what" and token.nbor().text == "can" and token.nbor(2).text == "you" and token.nbor(3).text == "do" for token in doc):
        return "I can provide information from Wikipedia and weather updates. What do you need?"
    elif any(token.text == "who" and token.nbor().text == "invented" for token in doc):
        return "The concept of invention dates back to ancient times, with many contributors throughout history."
    elif any(token.text == "when" and token.nbor().text == "is" and token.nbor(2).text == "your" and token.nbor(3).text == "birthday" for token in doc):
        return "I don't have a birthday, as I'm not a person. But I started functioning on the day I was programmed!"
    elif any(token.text == "where" and token.nbor().text == "are" and token.nbor(2).text == "you" and token.nbor(3).text == "from" for token in doc):
        return "I exist in the digital realm, ready to assist you wherever you are!"
    elif any(token.text == "why" and token.nbor().text == "do" and token.nbor(2).text == "you" and token.nbor(3).text == "exist" for token in doc):
        return "I exist to provide information and assist users like you!"
    elif any(token.text == "how" and token.nbor().text == "old" and token.nbor(2).text == "are" and token.nbor(3).text == "you" for token in doc):
        return "I'm as old as the version of me that's running right now!"
    elif any(token.text == "tell" and token.nbor().text == "me" and token.nbor(2).text == "a" and token.nbor(3).text == "joke" for token in doc):
        return "Why don't scientists trust atoms? Because they make up everything!"
    elif any(token.text == "tell" and token.nbor().text == "me" and token.nbor(2).text == "another" and token.nbor(3).text == "joke" for token in doc):
        return random.choice(jokes)  # Select a random joke from the list
    elif any(token.text == "can" and token.nbor().text == "you" and token.nbor(2).text == "tell" and token.nbor(3).text == "me" and token.nbor(4).text == "a" and token.nbor(5).text == "story" for token in doc):
        return "Once upon a time, in a land far, far away..."
    elif any(token.text == "how" and token.nbor().text == "do" and token.nbor(2).text == "I" and token.nbor(3).text == "contact" and token.nbor(4).text == "you" for token in doc):
        return "You can contact me through this chat interface!"
    elif any(token.text == "what" and token.nbor().text == "are" and token.nbor(2).text == "the" and token.nbor(3).text == "latest" and token.nbor(4).text == "news" for token in doc):
        return "I can't provide real-time news updates, but you can check news websites or apps for the latest updates!"
    else:
        return "I'm sorry, I don't understand that."

# External API integration for weather information
def get_weather_response(user_input):
    location = user_input.split("weather in")[-1].strip()
    api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
    response = requests.get(url).json()
    
    if response.get("weather"):
        weather = response["weather"][0]["description"]
        temperature = response["main"]["temp"] - 273.15  # Convert Kelvin to Celsius
        return f"The weather in {location} is currently {weather} with a temperature of {temperature:.1f}°C."
    else:
        return "Weather information not available for that location."

# Wikipedia API integration
# Wikipedia API integration
def get_wikipedia_response(user_input):
    topic = user_input.split("wikipedia")[-1].strip()
    wiki = wikipediaapi.Wikipedia(user_agent='YourBotName/1.0')  # Replace with your bot name and version
    
    if "avengers" in topic.lower():
        page = wiki.page("Avengers (comics)")
    else:
        page = wiki.page(topic)
        
    if "earth" in topic.lower():
        page = wiki.page("Earth")
    else:
        page = wiki.page(topic)
    
    if "computer science" in topic.lower():
        page = wiki.page("Computer science")
    else:
        page = wiki.page(topic)
          
    if page.exists():
        summary = page.summary[:500]  # Limit summary length
        return f"According to Wikipedia, {summary}"
    else:
        return f"Sorry, I couldn't find any information about {topic} on Wikipedia."


# Log conversations to a file
def log_conversation(user_input, bot_response):
    with open('logs/conversations.log', 'a') as log_file:
        log_file.write(f'User: {user_input}\n')
        log_file.write(f'Bot: {bot_response}\n\n')

# Routes and views
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')  # Use pbkdf2:sha256
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# SocketIO event handler for chat messages
@socketio.on('user_message')
def handle_user_message(data):
    user_input = data['message']
    bot_response = get_bot_response(user_input)
    log_conversation(user_input, bot_response)
    emit('bot_response', {'response': bot_response})

# Main entry point to run the application
if __name__ == '__main__':
    socketio.run(app, debug=True)  # Run the Flask application with SocketIO support
