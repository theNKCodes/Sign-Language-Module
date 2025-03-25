from flask import Flask, request, jsonify, g
from flask_cors import CORS
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import spacy
from collections import Counter
import re
import sacrebleu
from rouge_score import rouge_scorer
import time
from nltk.translate.meteor_score import meteor_score
from gramformer import Gramformer
import torch
import mysql.connector
from mysql.connector import pooling
import os
import logging
from dotenv import load_dotenv
from html import escape

load_dotenv()

# Configuration
MAX_TEXT_LENGTH = 5000
DATABASE_TIMEOUT = 5
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
POOL_SIZE = 5

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NLTK setup
nltk.download('wordnet', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# spaCy model setup
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load('en_core_web_sm')

# Gramformer initialization
try:
    gf = Gramformer(models=1, use_gpu=torch.cuda.is_available())
except Exception as e:
    logger.error(f"Gramformer initialization failed: {str(e)}")
    raise


# Database connection pool
db_pool = pooling.MySQLConnectionPool(
    pool_name="app_pool",
    pool_size=POOL_SIZE,
    host=os.getenv('DB_HOST'),
    port=3306,
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASS'),
    database=os.getenv('DB_NAME'),
    auth_plugin='mysql_native_password',
    autocommit=False,
    pool_reset_session=True
)

def get_db_connection():
    """Get and validate database connection"""
    try:
        conn = db_pool.get_connection()
        conn.ping(reconnect=True, attempts=3)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS)

def test_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print("Connection successful")
    except Exception as e:
        print(f"Connection failed: {str(e)}")

app = Flask(__name__)
CORS(app)


@app.route('/health')
def health_check():
    """Endpoint for service health monitoring"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'models_loaded': True
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy'}), 500

@app.route('/evaluate', methods=['POST'])
def evaluate_translation():
    """Evaluate translation quality between reference and hypothesis texts"""
    start_time = time.time()
    data = request.get_json()

    # Input validation
    if not data or 'reference' not in data or 'hypothesis' not in data:
        return jsonify({'error': 'Missing reference or hypothesis in request'}), 400
    
    reference = data['reference'].strip()
    hypothesis = data['hypothesis'].strip()
    
    # Validate text content and length
    if not reference or not hypothesis:
        return jsonify({'error': 'Reference or hypothesis cannot be empty'}), 400
    
    if len(reference) > MAX_TEXT_LENGTH or len(hypothesis) > MAX_TEXT_LENGTH:
        return jsonify({'error': f'Text exceeds maximum length of {MAX_TEXT_LENGTH} characters'}), 400

    try:
        # Grammar correction with safety checks
        try:
            corrections = gf.correct(hypothesis, max_candidates=1)
            corrected_hypothesis = list(corrections)
            if corrected_hypothesis:
                hypothesis = corrected_hypothesis[0]
        except Exception as e:
            logger.warning(f"Grammar correction failed: {str(e)}")

        # Process texts with spaCy
        reference_doc = nlp(reference)
        hypothesis_doc = nlp(hypothesis)

        # Calculate metrics
        metrics = calculate_metrics(reference, hypothesis, reference_doc, hypothesis_doc)
        
        # Store results in database
        evaluation_id = store_evaluation_results(reference, hypothesis, metrics, start_time)
        
        return jsonify({
            'evaluation_id': evaluation_id,
            'message': 'Translation evaluation complete',
            'metrics': metrics,
            'processing_time': time.time() - start_time
        })

    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}")
        return jsonify({'error': 'An error occurred during evaluation', 'details': str(e)}), 500

def calculate_metrics(reference, hypothesis, reference_doc, hypothesis_doc):
    """Calculate all NLP evaluation metrics"""
    # Tokenization
    reference_tokens = [token.text for token in reference_doc]
    hypothesis_tokens = [token.text for token in hypothesis_doc]

    # Initialize metrics dictionary
    metrics = {
        'BLEU': sacrebleu.corpus_bleu([hypothesis], [[reference]]).score,
        'METEOR': meteor_score([reference_tokens], hypothesis_tokens),
        'TER': sacrebleu.metrics.TER().corpus_score([hypothesis], [[reference]]).score,
        'linguistic_accuracy': calculate_linguistic_accuracy(reference_doc, hypothesis_doc)
    }

    # ROUGE scores
    rouge = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    rouge_scores = rouge.score(reference, hypothesis)
    metrics['ROUGE'] = {
        'ROUGE-1': rouge_scores['rouge1'].fmeasure,
        'ROUGE-2': rouge_scores['rouge2'].fmeasure,
        'ROUGE-L': rouge_scores['rougeL'].fmeasure,
    }

    return metrics

def calculate_linguistic_accuracy(reference_doc, hypothesis_doc):
    """Calculate linguistic accuracy metrics"""
    # POS Accuracy
    reference_pos = {token.text: token.pos_ for token in reference_doc}
    pos_matches = sum(1 for token in hypothesis_doc if reference_pos.get(token.text) == token.pos_)
    pos_accuracy = safe_division(pos_matches, len(reference_doc)) * 100

    # NER Accuracy
    reference_entities = {(ent.text, ent.start_char, ent.end_char): ent.label_ for ent in reference_doc.ents}
    hypothesis_entities = {(ent.text, ent.start_char, ent.end_char): ent.label_ for ent in hypothesis_doc.ents}
    ner_matches = sum(1 for ent in hypothesis_entities if ent in reference_entities and reference_entities[ent] == hypothesis_entities[ent])
    ner_accuracy = safe_division(ner_matches, len(reference_entities)) * 100

    # Lemmatization Accuracy
    reference_lemmas = {token.text.lower(): token.lemma_ for token in reference_doc}
    hypothesis_lemmas = {token.text.lower(): token.lemma_ for token in hypothesis_doc}
    lemma_matches = sum(1 for word in hypothesis_lemmas if word in reference_lemmas and reference_lemmas[word] == hypothesis_lemmas[word])
    lemma_accuracy = safe_division(lemma_matches, len(reference_lemmas)) * 100

    # Phrase Preservation
    reference_phrases = set(chunk.text.lower() for chunk in reference_doc.noun_chunks)
    hypothesis_phrases = set(chunk.text.lower() for chunk in hypothesis_doc.noun_chunks)
    phrase_matches = len(reference_phrases.intersection(hypothesis_phrases))
    phrase_preservation = safe_division(phrase_matches, len(reference_phrases)) * 100

    return {
        'POS': pos_accuracy,
        'NER': ner_accuracy,
        'lemmatization': lemma_accuracy,
        'phrase_preservation': phrase_preservation
    }

def safe_division(numerator, denominator):
    """Safe division to handle zero denominators"""
    return numerator / denominator if denominator else 0

def store_evaluation_results(reference, hypothesis, metrics, start_time):
    """Store evaluation results in database"""
    try:
        with get_db_connection() as db:
            with db.cursor() as cursor:
                sql = """
                INSERT INTO evaluations (
                    reference, hypothesis, bleu_score, meteor_score, ter_score,
                    rouge1, rouge2, rougeL, pos_accuracy, ner_accuracy,
                    lemmatization_accuracy, phrase_preservation, execution_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    reference, hypothesis,
                    metrics['BLEU'], metrics['METEOR'], metrics['TER'],
                    metrics['ROUGE']['ROUGE-1'], metrics['ROUGE']['ROUGE-2'], metrics['ROUGE']['ROUGE-L'],
                    metrics['linguistic_accuracy']['POS'],
                    metrics['linguistic_accuracy']['NER'],
                    metrics['linguistic_accuracy']['lemmatization'],
                    metrics['linguistic_accuracy']['phrase_preservation'],
                    time.time() - start_time
                )
                
                cursor.execute(sql, values)
                evaluation_id = cursor.lastrowid  # Get the last inserted ID
                db.commit()
                return evaluation_id
    except Exception as db_error:
        logger.error(f"Database error: {str(db_error)}")
        return None
    

@app.route('/get_evaluations', methods=['GET'])
def get_evaluations():
    """Endpoint to retrieve previous evaluations"""
    try:
        with get_db_connection() as db:
            with db.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT id, reference, hypothesis, bleu_score, meteor_score, ter_score,
                           rouge1, rouge2, rougeL, pos_accuracy, ner_accuracy,
                           lemmatization_accuracy, phrase_preservation,
                           execution_time, created_at
                    FROM evaluations
                    ORDER BY created_at DESC
                    LIMIT 100
                """)
                return jsonify(cursor.fetchall())
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({'error': 'Failed to fetch evaluations'}), 500

@app.route('/process', methods=['POST'])
def process_text():
    """Endpoint for text processing"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        # Validate input
        if not text:
            return jsonify({'error': 'Text cannot be empty'}), 400
        if len(text) > MAX_TEXT_LENGTH:
            return jsonify({'error': f'Text exceeds {MAX_TEXT_LENGTH} characters'}), 400

        # Grammar correction
        try:
            corrections = list(gf.correct(text, max_candidates=1))
            corrected_text = corrections[0] if corrections else text
        except Exception as e:
            logger.warning(f"Grammar correction failed: {str(e)}")
            corrected_text = text

        # Text processing
        result = process_text_content(corrected_text)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': 'Text processing failed'}), 500

def process_text_content(text):
    """Process text and extract linguistic features"""
    # Tokenization and cleaning
    tokens = [re.sub(r'[^a-zA-Z]', '', word).lower() 
             for word in word_tokenize(text)]
    tokens = [word for word in tokens if word]
    
    # Stopwords processing
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in stop_words]
    
    # POS tagging
    pos_tags = nltk.pos_tag(filtered_tokens)
    
    # spaCy processing
    doc = nlp(text)
    
    # Entity recognition
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    # Lemmatization
    lemmas = [token.lemma_ for token in doc]
    
    return {
        'input_text': text,
        'corrected_text': text,
        'tokens': tokens,
        'filtered_tokens': filtered_tokens,
        'pos_tags': pos_tags,
        'entities': entities,
        'lemmas': lemmas,
        'metrics': calculate_text_metrics(tokens, filtered_tokens, pos_tags, entities, lemmas)
    }

def calculate_text_metrics(tokens, filtered_tokens, pos_tags, entities, lemmas):
    """Calculate text processing metrics"""
    num_tokens = len(tokens)
    num_filtered = len(filtered_tokens)
    
    return {
        'num_tokens': num_tokens,
        'avg_token_length': safe_division(sum(len(w) for w in tokens), num_tokens),
        'num_stopwords_removed': num_tokens - num_filtered,
        'stopwords_removal_percentage': safe_division(num_tokens - num_filtered, num_tokens) * 100,
        'pos_distribution': dict(Counter(tag for _, tag in pos_tags)),
        'num_entities': len(entities),
        'unique_lemmas': len(set(lemmas))
    }

@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def log_latency(response):
    if hasattr(g, 'start_time'):
        latency = time.time() - g.start_time
        response.headers['X-Response-Time'] = f"{latency:.4f} sec"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')

