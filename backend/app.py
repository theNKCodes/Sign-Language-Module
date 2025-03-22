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
from flask import g
import time
from nltk.translate.meteor_score import meteor_score
from gramformer import Gramformer
import torch

app = Flask(__name__)
CORS(app)

nltk.download('wordnet')
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
# nltk.download('omw-1.4')
# nltk.download('punkt_tab')
# nltk.download('averaged_perceptron_tagger_eng')

nlp = spacy.load('en_core_web_sm')

gf = Gramformer(models=1, use_gpu=torch.cuda.is_available())
from nltk.corpus import wordnet
print(wordnet.synsets("example"))


def calculate_accuracy(reference_tokens, hypothesis_tokens):
    """Calculate word-level matching accuracy."""
    matches = sum(1 for word in hypothesis_tokens if word in reference_tokens)
    return (matches / len(reference_tokens)) * 100 if reference_tokens else 0


@app.route('/evaluate', methods=['POST'])
def evaluate_translation():
    start_time = time.time()
    data = request.get_json()

    # Ensure keys exist in request
    if 'reference' not in data or 'hypothesis' not in data:
        return jsonify({'error': 'Missing reference or hypothesis in request'}), 400

    reference = data['reference']  # Correct human translation
    hypothesis = data['hypothesis']  # Machine-generated translation

    # Tokenization
    reference_tokens = word_tokenize(reference)
    hypothesis_tokens = word_tokenize(hypothesis)

    # BLEU Score
    bleu_score = sacrebleu.corpus_bleu([hypothesis], [[reference]]).score

    # METEOR Score
    meteor = meteor_score([reference.split()], hypothesis.split())

    # TER Score
    ter_score = sacrebleu.corpus_ter([hypothesis], [[reference]]).score

    # ROUGE Scores
    rouge = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    rouge_scores = rouge.score(reference, hypothesis)

    # POS Tagging Accuracy
    reference_pos = dict(nltk.pos_tag(reference_tokens))
    hypothesis_pos = dict(nltk.pos_tag(hypothesis_tokens))
    pos_matches = sum(1 for word in hypothesis_pos if word in reference_pos and reference_pos[word] == hypothesis_pos[word])
    pos_accuracy = (pos_matches / len(reference_pos)) * 100 if reference_pos else 0

    # Named Entity Recognition (NER) Accuracy
    reference_doc = nlp(reference)
    hypothesis_doc = nlp(hypothesis)
    reference_entities = {ent.text: ent.label_ for ent in reference_doc.ents}
    hypothesis_entities = {ent.text: ent.label_ for ent in hypothesis_doc.ents}
    ner_matches = sum(1 for entity in hypothesis_entities if entity in reference_entities and reference_entities[entity] == hypothesis_entities[entity])
    ner_accuracy = (ner_matches / len(reference_entities)) * 100 if reference_entities else 0

    # Lemmatization Accuracy
    reference_lemmas = {token.text: token.lemma_ for token in reference_doc}
    hypothesis_lemmas = {token.text: token.lemma_ for token in hypothesis_doc}
    lemma_matches = sum(1 for word in hypothesis_lemmas if word in reference_lemmas and reference_lemmas[word] == hypothesis_lemmas[word])
    lemma_accuracy = (lemma_matches / len(reference_lemmas)) * 100 if reference_lemmas else 0

    # Phrase Preservation (Checking noun phrases in hypothesis)
    reference_phrases = set([chunk.text.lower() for chunk in reference_doc.noun_chunks])
    hypothesis_phrases = set([chunk.text.lower() for chunk in hypothesis_doc.noun_chunks])
    phrase_matches = len(reference_phrases.intersection(hypothesis_phrases))
    phrase_preservation = (phrase_matches / len(reference_phrases)) * 100 if reference_phrases else 0
    execution_time = time.time() - start_time  # Calculate execution time

    reference_entities = set((ent.text, ent.label_) for ent in reference_doc.ents)
    hypothesis_entities = set((ent.text, ent.label_) for ent in hypothesis_doc.ents)
    ner_matches = len(reference_entities.intersection(hypothesis_entities))
    ner_accuracy = (ner_matches / len(reference_entities)) * 100 if reference_entities else 0
    print(rouge_scorer.RougeScorer.__dict__)

    return jsonify ({
            'message': 'Translation evaluation complete',
            'BLEU Score': bleu_score,
            'METEOR Score': meteor,
            'TER Score': ter_score,
            'Execution Time (seconds)': execution_time,
            'ROUGE Scores': {
                'ROUGE-1': rouge_scores['rouge1'].fmeasure,
                'ROUGE-2': rouge_scores['rouge2'].fmeasure,
                'ROUGE-L': rouge_scores['rougeL'].fmeasure,
            },
            'Linguistic Accuracy': {
                'POS Accuracy': pos_accuracy,
                'NER Accuracy': ner_accuracy,
                'Lemmatization Accuracy': lemma_accuracy,
                'Phrase Preservation': phrase_preservation
            }
    })



@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def log_latency(response):
    if hasattr(g, 'start_time'):
        latency = time.time() - g.start_time
        response.headers['X-Response-Time'] = f"{latency:.4f} sec"
    return response


@app.route('/process', methods=['POST'])
def process_text():
    data = request.get_json()
    text = data['text']
    # text = gf.correct(text)
    print(f'Received text for processing: {text}')  # Log the received text

    # Correct Grammar using Gramformer
    corrected_text = list(gf.correct(text, max_candidates=1))[0]  # Get the best correction
    print(f'Corrected text: {corrected_text}')  # Log corrected text

    tokens = word_tokenize(corrected_text)
    num_tokens = len(tokens)

    tokens = [re.sub(r'[^a-zA-Z]', '', word).lower() for word in tokens if re.sub(r'[^a-zA-Z]', '', word)]
    avg_token_length = sum(len(word) for word in tokens) / len(tokens) if tokens else 0

    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in stop_words]
    num_stopwords_removed = num_tokens - len(filtered_tokens)
    stopwords_removal_percentage = (num_stopwords_removed / num_tokens) * 100 if num_tokens > 0 else 0

    pos_tags = nltk.pos_tag(filtered_tokens)
    pos_counts = Counter(tag for _, tag in pos_tags)

    doc = nlp(corrected_text)

    entities = [(entity.text, entity.label_) for entity in doc.ents]
    num_entities = len(entities)
    entity_counts = Counter(entity[1] for entity in entities)

    lemmas = [token.lemma_ for token in doc]
    unique_lemmas = set(lemmas)
    num_lemmas = len(unique_lemmas)
    lemmatization_reduction = ((num_tokens - num_lemmas) / num_tokens) * 100 if num_tokens > 0 else 0

    return jsonify({
        'message': 'Text successfully processed',
        'input_text': text,
        'corrected_text': corrected_text,
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
        }
    })

if __name__ == '__main__':
    app.run(debug=True)