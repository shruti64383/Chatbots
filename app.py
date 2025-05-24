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
    "response": """You can obtain a referral code in one of the following ways:<br><br>
      • <strong>From Your Contacts:</strong> If any of your phonebook contacts are already registered, you can request a referral code from them.<br><br>
      • <strong>Scan a Business QR Code:</strong> Scanning a business's QR code will provide a referral code and automatically follow that business. You can then start leaving reviews for them.<br><br>
      • <strong>Explore Communities:</strong> Browse and join communities. For public communities, you’ll be connected instantly. For private communities, you’ll need to wait for referral code approval.<br>""",
    "patterns": [
      r"\b(?!.*without)(need|looking for)\b.*\b(referral code)\b", 
      r"\b(how|where|ways)\b.*\b(get|find|acquire)\b.*\b(referral code|referral)\b",
         
    ],
    "entities": ["REFERRAL_CODE_SOURCES", "HOW_TO_GET_REFERRAL"],
    "priority": 50 

    },

    "add_review": {
    "response": """
     You can add a review by following one of these steps: <br><br>

    <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 1: Navigate to My Profile</strong><br><br>

    <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 2: Select Personal</strong><br><br>

    <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 3: Select My Reviews/ Recommadation</strong><br><br>

    <details>
    <summary><strong>Step 4: Click on Add Review/Recommadations and earn eTags</strong></summary><br>
    You will be prompted with a list of categories. Please selct one of them. It will redirect you to fill in the required review/recommadation details. Now simply fill out the form with the required details and  submit it.<br>
    </details><br>

    <strong class="space">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; OR </strong><br><br>
     
    <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 1: Open the QuickSelect page </strong><br><br>
     
    <details>
    <summary><strong>Step 2: Tap Write a Review/Recommadation</strong></summary><br> 
    Choose the category you're interested in. Please selct one of them. It will redirect you to fill in the required review/recommadation
     details. Now simply fill out the form with the required details and  submit it.
    </details><br>""",

    "patterns": [
      r"\b(review|rating|recommendation|recommend|suggest)\b",
      r"\bhow.*add.*recommendation\b",
      r"\bhow.*add.*review\b",
      r"\bwhere.*write.*review\b"
      r"\bwhere.*write.*recommendation\b"
    ],
    "entities": ["REVIEW", "RATING", "RECOMMENDATION"]
  },
  
    "register_business": {
    "response": """
    Follow these steps to register your business on the platform:<br><br>

    <details>
    <summary><strong>Step 1: Navigate to your profile</strong></summary>
    <br>
    Click on the light blue section right below your Profile Picture
    </details><br> 

    <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 2: Click on Sign Up Details</strong><br><br>

    <details>
    <summary><strong>Step 3: Spot on Professional Details</strong></summary>
    <br>
    Now click on Add My Details </strong><br>
    </details><br>

    <details>
    <summary><strong>Step 4: Select Professional for profile type</strong></summary>
    <br> 
    Enter your business information and save the changes
    </details><br>""", 

    "patterns": [
      r"\b(business|register|professional)\b",
      r"\bhow.*register.*business\b",
      r"\badd.*business profile\b",
      r"\bwhere.*list.*profession\b",
      r"\bhow.*add.*professional details\b",
      r"\bset.*up.*professional profile\b",
      r"\bupdate.*professional information\b"
    ],
    "entities": ["BUSINESS", "REGISTRATION", "PROFESSIONAL"]
  },

    "find_community": {
    "response": """
     Follow these steps to find a community to join: <br><br>

     <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 1: Navigate to My Profile</strong><br><br>

     <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 2: Select Network</strong><br><br>

     <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 3: Tap on My Communities</strong><br><br>

     <details>
     <summary><strong>Step 4: Go to Suggestions tab</strong></summary><br><br> 
     Search the community of your choice by typing a few words, a list of related communities will be there. Join the communities of your interest.<br>
     </details>""",

    "patterns": [
      r"\b^(?!.*what).*\b(community)\b",
      r"\b(community|join|find)\b",
      r"\bhow.*find.*community\b",
      r"\bsearch.*for.*communities\b",
      r"\bwhere.*join.*community\b",
      r"\bdiscover.*new.*communities\b"
    ],
    "entities": ["COMMUNITY", "NETWORK"]
  },

    "add_hobby": {
    "response": """
      Add your hobbies to your profile using these steps:<br><br>

      <details>
      <summary><strong>Step 1: Navigate to your profile</strong></summary>
      <br>
      Click on the light blue section right below your Profile Picture
      </details><br>

      <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 2: Click on Sign Up Details</strong><br><br>

      <details>
      <summary><strong>Step 3: Spot on Social Details</strong></summary>
      <br>
      Now click on Add My Details </strong><br>
      </details>

      <br>
      <details>
      <summary><strong>Step 4: Add Hobby</strong></summary>
      <br>
      Choose from the available list or type your own.<br>
      </details><br>""",

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
    "response": """
    Requesting a suggestion is quick and easy:</strong><br><br>
    
    <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 1: Open the QuickSelect page </strong><br><br>
    
    <details>
    <summary><strong>Step 2: Tap on Create a Request </strong></summary><br>
    You will now be able to see categories to select based upon your query type<br>
    </details><br>

    <details>
    <summary><strong>Step 3: Select the category you're interested</strong></summary><br>
    Simply fill out the form with the required details and your query. Once you submit it, you’ll receive a suggestion as soon as someone responds
    </details><br>""",

    "patterns": [
      r"\b(suggestion|request|ask|suggestions)\b",
      r"\bhow.*request.*suggestion\b",
      r"\bwhere.*ask.*recommendation\b"
    ],
    "entities": ["SUGGESTION", "REQUEST"]
  },

    "sign_up": {
    "response": """To sign up, please follow the steps below:<br><br>
    <details>
    <summary><strong>Step 1: Select a Sign-Up Method </strong></summary>
    <br>
    Choose one of the following options to begin:<br><br>
    • Sign up with Email<br>
    • Sign up with Google<br>
    • Sign up with Apple ID<br>
    </details><br>

    <details>
    <summary><strong>Step 2: Fill in Your Details </strong></summary>
    <br>
    After selecting a sign-up method, you'll be directed to a registration page. Enter the required basic information such as:<br><br>
    • Full Name<br>
    • Username<br>
    • Email Address<br>
    • Phone Number<br>
    • Date of Birth<br>
    • Password<br>
    </details><br>

    <details>
    <summary><strong>Step 3: Enter a Referral Code </strong></summary>
    <br>
    After completing your basic details, you'll be prompted to enter a referral code.<br>
    To know about referral codes, 
      <details class="custom-underline"><summary>click here</summary>
      <br> 
      <br>
      You can obtain a referral code in one of the following ways:<br><br>
      • <strong>From Your Contacts:</strong> If any of your phonebook contacts are already registered, you can request a referral code from them.<br><br>
      • <strong>Scan a Business QR Code:</strong> Scanning a business's QR code will provide a referral code and automatically follow that business. You can then start leaving reviews for them.<br><br>
      • <strong>Explore Communities:</strong> Browse and join communities. For public communities, you'll be connected instantly. For private communities, you’ll need to wait for referral code approval.<br>
      </details><br>
    </details><br> 

    <details>
    <summary><strong>(Optional) Set Networking Preference </strong></summary>
    <br>
    After signing up, you have the option to add networking preferences by sharing your current industry and hobbies. This helps others connect with you for professional insights or shared interests. You may also skip this step and explore the app freely.<br>
    </details>""",

    "patterns": [
      r"\b(sign up|register|join)\b",
      r"\bhow.*sign up\b",
      r"\bcreate.*account\b"
    ],
    "entities": ["SIGNUP", "REGISTRATION"]
  },

    "sign_up_without_referral": {
    "response": """You must enter a referral code during sign-up, as it is required to proceed.<br>
     To know about referral codes,

      <details class="custom-underline"><summary>click here</summary>
      <br> 
      <br>
      You can obtain a referral code in one of the following ways:<br><br>
      • <strong>From Your Contacts:</strong> If any of your phonebook contacts are already registered, you can request a referral code from them.<br><br>
      • <strong>Scan a Business QR Code:</strong> Scanning a business's QR code will provide a referral code and automatically follow that business. You can then start leaving reviews for them.<br><br>
      • <strong>Explore Communities:</strong> Browse and join communities. For public communities, you'll be connected instantly. For private communities, you’ll need to wait for referral code approval.<br>
      </details><br>""",

    
  "patterns": [
        
      r"\b(can i|is it possible)\b.*\b(sign\s*up|register|join)\b.*\b(without|no)\b.*\b(referral|ref|code)\b",
      r"\b(sign\s*up|register)\b.*\b(without|no)\b.*\b(referral|ref)\b",
       
      r"\b(do i need|is a referral required)\b.*\b(to (sign\s*up|register))\b"
    ],
    "entities": ["SIGNUP_REQUIREMENTS", "REFERRAL_POLICY"],
    "priority": 100   
    },

    "add_feedback": {
    "response": """
     Share your feedback by following these steps:<br><br>

     <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 1: Navigate to My Profile</strong><br><br>

    <strong>&nbsp;&nbsp;&nbsp;&nbsp;Step 2: Select Feedback & Report</strong><br><br>

    <details>
    <summary><strong>Step 3: Click on Add your valuable feedback</strong></summary><br>
     You will be redirected  to fill in the required details. Here you can fill in the comment box to describe your issues as well as add photos/videos to support your description.
     Now you're ready to fill out the form with the required details and  submit it.<br>
    </details><br> """,

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
    app.run(host='0.0.0.0', port=5000, debug=True)
