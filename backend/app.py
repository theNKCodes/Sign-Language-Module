from flask import Flask, request, jsonify
from flask_cors import CORS
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import spacy

# Initialize the app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

@app.route('/process', methods=['POST'])
def process_text():
    data = request.get_json()
    text = data['text']
    print(f'Received text for processing: {text}')  # Log the received text

    # Tokenization
    tokens = word_tokenize(text)

    # Normalization
    tokens = [word.lower() for word in tokens if word.isalpha()]

    # Stop words removal
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if not word in stop_words]

    # POS Tagging
    pos_tags = nltk.pos_tag(filtered_tokens)

    # Process text with spaCy
    doc = nlp(text)

    # NER
    entities = [(entity.text, entity.label_) for entity in doc.ents]

    # Lemmatization
    lemmas = [token.lemma_ for token in doc]

    return jsonify({
        'message': 'Text successfully processed',
        'input_text': text,
        'tokens': tokens,
        'filtered_tokens': filtered_tokens,
        'pos_tags': pos_tags,
        'entities': entities,
        'lemmas': lemmas
    })

if __name__ == '__main__':
    app.run(debug=True)
