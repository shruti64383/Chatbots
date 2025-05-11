from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import re
import spacy
from fuzzywuzzy import fuzz
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Load English NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Enhanced knowledge base with patterns and entities
knowledge_base = {
    "greetings": {
        "responses": [
            "How can I help you?"
        ],
        "patterns": [
            r"\b(hi|hello|hey|greetings|good morning|good afternoon|yes)\b",
            r"^start$"
        ]
    },
    "end": {
        "response": "Have a good day!!!",
        "patterns": [
            r"\b(bye|see.*you|no)\b"             
    ],
    "entities": ["BYE"]
  },
    "referral_code": {
        "response": "You can request a referral code through any of the following ways:\n1. From a TagAboutIt user in your contacts\n2. By scanning a business QR code\n3. By joining communities within the app",
        "patterns": [
            r"\b(referral code|referral|code)\b",
            r"\bhow.*get.*referral\b",
            r"\bwhere.*find.*referral code\b"
    ],
    "entities": ["REFERRAL", "CODE"]
  },
  "add_review": {
    "response": "To add a review:\n1. Go to your profile > Personal > My Reviews > Add Review, then fill in the details.\n2. Or, open the QuickSelect page > Tap the \"Write a Review\" button, and choose the category you're interested in.",
    "patterns": [
      r"\b(review|rating|feedback)\b",
      r"\bhow.*add.*review\b",
      r"\bwhere.*write.*review\b"
    ],
    "entities": ["REVIEW", "RATING"]
  },
  "add_recommendation": {
    "response": "To add a recommendation:\n1. Go to your profile > Personal > My Recommendations > Add Recommendation, then fill in the details.\n2. Or, open the QuickSelect page > Tap the \"Write a Recommendation\" button, and choose the category you're interested in.",
    "patterns": [
      r"\b(recommendation|recommend|suggest)\b",
      r"\bhow.*add.*recommendation\b",
      r"\bwhere.*write.*recommendation\b"
    ],
    "entities": ["RECOMMENDATION"]
  },
  "register_business": {
    "response": "To register your business:\nGo to your profile > Sign Up Details > Professional Details > Add My Details > Select 'Professional', then fill in your business information and save.",
    "patterns": [
      r"\b(business|register|professional)\b",
      r"\bhow.*register.*business\b",
      r"\badd.*business profile\b"
    ],
    "entities": ["BUSINESS", "REGISTRATION"]
  },
  "add_hobby": {
    "response": "To add your hobbies:\nNavigate to your profile > Sign Up Details > Social Details > Add My Details > Add Hobby, then choose from the available list or type your own.",
    "patterns": [
      r"\b(hobby|interest|activity)\b",
      r"\bhow.*add.*hobby\b",
      r"\bwhere.*put.*hobbies\b"
    ],
    "entities": ["HOBBY", "INTEREST"]
  },
  "community": {
    "response": "A community on TagAboutIt is a group where users with shared interests can connect, interact, and share content.",
    "patterns": [
      r"\b(community|group|network)\b",
      r"\bwhat.*community\b",
      r"\bmeaning.*community\b"
    ],
    "entities": ["COMMUNITY"]
  },
  "circle": {
    "response": "A circle is your personal network of trusted users or friends within TagAboutIt, where you can connect and share experiences.",
    "patterns": [
      r"\b(circle|network|friends)\b",
      r"\bwhat.*circle\b",
      r"\bmeaning.*circle\b"
    ],
    "entities": ["CIRCLE", "NETWORK"]
  },
  "request_suggestion": {
    "response": "To create a request:\nOpen the QuickSelect page > Tap the \"Create a Request\" button, and choose the category you're interested in.",
    "patterns": [
      r"\b(suggestion|request|ask)\b",
      r"\bhow.*request.*suggestion\b",
      r"\bwhere.*ask.*recommendation\b"
    ],
    "entities": ["SUGGESTION", "REQUEST"]
  },
  "sign_up": {
    "response": "To sign up:\nOpen the TagAboutIt app, tap on \"Sign Up\" > Verify your mobile number > Enter a referral code.",
    "patterns": [
      r"\b(sign up|register|join)\b",
      r"\bhow.*sign up\b",
      r"\bcreate.*account\b"
    ],
    "entities": ["SIGNUP", "REGISTRATION"]
  },
  "sign_up_without_referral": {
    "response": "Yes, you can skip the referral code step during sign-up. However, entering a referral code may unlock extra features if you have one.",
    "patterns": [
      r"\b(without referral|no referral|skip referral)\b",
      r"\bcan.*sign up.*without.*referral\b",
      r"\bregister.*no.*code\b"
    ],
    "entities": ["SIGNUP", "REFERRAL"]
  },
  "add_feedback": {
    "response": "To add feedback:\nGo to your profile > Feedback & Report > Add Feedback, then fill in the details.",
    "patterns": [
      r"\b(feedback|report|issue)\b",
      r"\bhow.*add.*feedback\b",
      r"\bwhere.*submit.*feedback\b"
    ],
    "entities": ["FEEDBACK", "REPORT"]
  }
}

def preprocess_text(text):
    """Clean and normalize text"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    return text

def regex_match(text, patterns):
    """Check if text matches any regex pattern"""
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def fuzzy_match(text, targets, threshold=70):
    """Check for similar strings using fuzzy matching"""
    text = preprocess_text(text)
    for target in targets:
        if fuzz.partial_ratio(text, target) >= threshold:
            return True
    return False

def nlp_analysis(text):
    """Extract entities and meaning using NLP"""
    doc = nlp(text)
    
    # Extract entities
    entities = defaultdict(list)
    for ent in doc.ents:
        entities[ent.label_].append(ent.text)
    
    # Extract important nouns and verbs
    keywords = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "VERB"]]
    
    return entities, keywords

def find_best_response(user_input):
    """Enhanced response finding with multiple techniques"""
    # Preprocess input
    cleaned_input = preprocess_text(user_input)
    
    # 1. Check for greetings first (exact + regex)
    if any(greet in cleaned_input for greet in ["hi", "hello", "hey"]) or \
       regex_match(user_input, knowledge_base["greetings"]["patterns"]):
        return knowledge_base["greetings"]["responses"]
    
    # 2. NLP analysis
    entities, keywords = nlp_analysis(user_input)
    
    # 3. Check all categories with multiple matching techniques
    for category, data in knowledge_base.items():
        if category == "greetings":
            continue
        
        # Check regex patterns
        if "patterns" in data and regex_match(user_input, data["patterns"]):
            return data["response"]
        
        # Check NLP entities
        if "entities" in data:
            for entity_type in data["entities"]:
                if entity_type in entities:
                    return data["response"]
        
        # Check fuzzy matching with keywords
        if fuzzy_match(user_input, data.get("keywords", [])):
            return data["response"]
    
    # 4. Fallback to fuzzy matching with category names
    for category, data in knowledge_base.items():
        if category == "greetings":
            continue
        if fuzzy_match(user_input, [category]):
            return data["response"]
    
    return None

@app.route('/')
def home():
    return send_file('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').strip()
    
    if not user_message:
        return jsonify({'response': "Please type something so I can help you."})
    
    response = find_best_response(user_message)
    
    if response is None:
        return jsonify({
            'response': "That seems a bit complex for me to handle right now. You can visit the Feedback section in your profile to reach the our team. \nOr email us directly at xyz@gmail.com — they’ll be happy to help!",
            'end_conversation': False
        })
    
    if isinstance(response, list):
        return jsonify({'response': "\n".join(response)})
    
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True, port=5000)