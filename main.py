import os
import sys
import time
import json
import zipfile
import ssl
import torch
import numpy as np
from flask import Flask, request, render_template, send_from_directory, jsonify
from six.moves import urllib
import stanza
from nltk.parse.stanford import StanfordParser
from nltk.tree import Tree

# Configure safe globals for torch serialization
torch.serialization.add_safe_globals([np.core.multiarray._reconstruct])

# Download and initialize Stanza
stanza.download('en', model_dir='stanza_resources')
en_nlp = stanza.Pipeline('en', processors={'tokenize': 'spacy'})

# Define global variables
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
STANFORD_PARSER_DIR = os.path.join(BASE_DIR, 'stanford-parser-full-2018-10-17')
STANFORD_MODELS_PATH = os.path.join(STANFORD_PARSER_DIR, 'edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz')
NLTK_DATA_PATH = '/usr/local/share/nltk_data/'
os.environ.update({'CLASSPATH': STANFORD_PARSER_DIR, 'STANFORD_MODELS': STANFORD_MODELS_PATH, 'NLTK_DATA': NLTK_DATA_PATH})

# Define stop words
STOP_WORDS = {"am", "are", "is", "was", "were", "be", "being", "been", "have", "has", "had", "does", "did", "could", "should", "would", "can", "shall", "will", "may", "might", "must", "let"}

# Flask app initialization
app = Flask(__name__, static_folder='static', static_url_path='')


def is_parser_jar_file_present():
    return os.path.exists(STANFORD_PARSER_DIR + ".jar")


def download_file(url, destination):
    urllib.request.urlretrieve(url, destination, reporthook)


def extract_zip_file(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.perf_counter()
        return
    duration = time.perf_counter() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = min(int(count * block_size * 100 / total_size), 100)
    sys.stdout.write(f"\r...{percent}%, {progress_size // (1024 * 1024)} MB, {speed} KB/s, {duration:.1f} seconds passed")
    sys.stdout.flush()


def setup_stanford_parser():
    if not os.path.exists(STANFORD_PARSER_DIR):
        if not is_parser_jar_file_present():
            download_file("https://nlp.stanford.edu/software/stanford-parser-full-2018-10-17.zip", STANFORD_PARSER_DIR + ".jar")
        extract_zip_file(STANFORD_PARSER_DIR + ".jar", BASE_DIR)
    
    if not os.path.exists(STANFORD_MODELS_PATH):
        extract_zip_file(os.path.join(STANFORD_PARSER_DIR, 'stanford-parser-3.9.2-models.jar'), STANFORD_PARSER_DIR)


def preprocess_text(text):
    sent_list, sent_list_detailed = [], []
    word_list, word_list_detailed = [], []
    
    for sentence in text.sentences:
        sent_list.append(sentence.text)
        sent_list_detailed.append(sentence)
    
    for sentence in sent_list_detailed:
        temp_list, temp_list_detailed = [], []
        for word in sentence.words:
            temp_list.append(word.text)
            temp_list_detailed.append(word)
        word_list.append(temp_list)
        word_list_detailed.append(temp_list_detailed)
    
    return sent_list, sent_list_detailed, word_list, word_list_detailed


def remove_stopwords(word_list):
    return [[word for word in words if word not in STOP_WORDS] for words in word_list]


def lemmatize_words(word_list_detailed, final_word_list):
    for words, final in zip(word_list_detailed, final_word_list):
        for i, (word, fin) in enumerate(zip(words, final)):
            final[i] = word.lemma if len(fin) > 1 else fin
    return final_word_list


def modify_tree_structure(parent_tree):
    tree_traversal_flag = {sub_tree.treeposition(): 0 for sub_tree in parent_tree.subtrees()}
    modified_parse_tree = Tree('ROOT', [])
    i = 0

    for sub_tree in parent_tree.subtrees():
        if sub_tree.label() in ["NP", "VP", "PRP"]:
            for child_sub_tree in sub_tree.subtrees():
                if child_sub_tree.label() in ["NP", "PRP"] and not tree_traversal_flag[child_sub_tree.treeposition()]:
                    tree_traversal_flag[child_sub_tree.treeposition()] = 1
                    modified_parse_tree.insert(i, child_sub_tree)
                    i += 1
    
    return modified_parse_tree


def reorder_eng_to_isl(input_string):
    setup_stanford_parser()
    return input_string  # Placeholder for further processing


if __name__ == "__main__":
    app.run(debug=True)
