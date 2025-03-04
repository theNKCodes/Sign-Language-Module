from flask import Flask, request, jsonify
from flask_cors import CORS
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import spacy
from collections import Counter
import re
import sacrebleu
from rouge_score import rouge_scorer

# Initialize the app
app = Flask(__name__)
CORS(app)

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# Load spaCy model
nlp = spacy.load('en_core_web_sm')


@app.route('/evaluate', methods=['POST'])
def evaluate_translation():
    data = request.get_json()
    reference = data['reference']  # Correct human translation
    hypothesis = data['hypothesis']  # Machine-generated translation

    # BLEU Score (1-gram to 4-gram)
    bleu_score = sacrebleu.corpus_bleu([hypothesis], [[reference]]).score

    # METEOR Score
    meteor = meteor_score([reference.split()], hypothesis.split())

    # TER (Translation Edit Rate)
    ter_score = sacrebleu.corpus_ter([hypothesis], [[reference]]).score

    # ROUGE Scores
    rouge = rouge_scorer.RougeScorer(['rouge-1', 'rouge-2', 'rouge-l'], use_stemmer=True)
    rouge_scores = rouge.score(reference, hypothesis)
    
    return jsonify({
        'message': 'Translation evaluation complete',
        'BLEU Score': bleu_score,
        'METEOR Score': meteor,
        'TER Score': ter_score,
        'ROUGE Scores': {
            'ROUGE-1': rouge_scores['rouge-1'].fmeasure,
            'ROUGE-2': rouge_scores['rouge-2'].fmeasure,
            'ROUGE-L': rouge_scores['rouge-l'].fmeasure,
        }
    })


@app.route('/process', methods=['POST'])
def process_text():
    data = request.get_json()
    text = data['text']
    print(f'Received text for processing: {text}')  # Log the received text

    # Tokenization
    tokens = word_tokenize(text)
    num_tokens = len(tokens)

    # Normalization: Remove special characters and convert to lowercase
    tokens = [re.sub(r'[^a-zA-Z]', '', word).lower() for word in tokens if re.sub(r'[^a-zA-Z]', '', word)]
    avg_token_length = sum(len(word) for word in tokens) / len(tokens) if tokens else 0

    # Stop words removal
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in stop_words]
    num_stopwords_removed = num_tokens - len(filtered_tokens)
    stopwords_removal_percentage = (num_stopwords_removed / num_tokens) * 100 if num_tokens > 0 else 0

    # POS Tagging
    pos_tags = nltk.pos_tag(filtered_tokens)
    pos_counts = Counter(tag for _, tag in pos_tags)

    # Process text with spaCy
    doc = nlp(text)

    # Named Entity Recognition (NER)
    entities = [(entity.text, entity.label_) for entity in doc.ents]
    num_entities = len(entities)
    entity_counts = Counter(entity[1] for entity in entities)

    # Lemmatization
    lemmas = [token.lemma_ for token in doc]
    unique_lemmas = set(lemmas)
    num_lemmas = len(unique_lemmas)
    lemmatization_reduction = ((num_tokens - num_lemmas) / num_tokens) * 100 if num_tokens > 0 else 0

    # Return metrics
    return jsonify({
        'message': 'Text successfully processed',
        'input_text': text,
        'tokens': tokens,
        'filtered_tokens': filtered_tokens,
        'pos_tags': pos_tags,
        'entities': entities,
        'lemmas': lemmas,
        'metrics': {
            'num_tokens': num_tokens,
            'avg_token_length': avg_token_length,
            'num_stopwords_removed': num_stopwords_removed,
            'stopwords_removal_percentage': stopwords_removal_percentage,
            'pos_distribution': dict(pos_counts),
            'num_entities': num_entities,
            'entity_distribution': dict(entity_counts),
            'num_lemmas': num_lemmas,
            'lemmatization_reduction': lemmatization_reduction
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
