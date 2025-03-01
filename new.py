import json
import os
import time
import sys
import zipfile
import ssl
from flask import Flask, request, jsonify, render_template, send_from_directory
from six.moves import urllib
import stanza
from nltk.parse.stanford import StanfordParser
from nltk.tree import ParentedTree
import torch
import numpy as np

torch.serialization.add_safe_globals([np.core.multiarray._reconstruct])
ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__, static_folder='static', static_url_path='')

# Global configuration
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
STANFORD_DIR = os.path.join(BASE_DIR, 'stanford-parser-full-2018-10-17')
STANFORD_MODEL_PATH = os.path.join(STANFORD_DIR, 'edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz')
NLTK_DATA_PATH = '/usr/local/share/nltk_data/'

# Set environment variables
os.environ['CLASSPATH'] = STANFORD_DIR
os.environ['STANFORD_MODELS'] = STANFORD_MODEL_PATH
os.environ['NLTK_DATA'] = NLTK_DATA_PATH

# Load valid words for final output
with open(os.path.join(BASE_DIR, 'words.txt'), 'r') as f:
    VALID_WORDS = set(line.strip() for line in f)

# Initialize NLP components
stanza.download('en', model_dir=os.path.join(BASE_DIR, 'stanza_resources'))
STANZA_PIPELINE = stanza.Pipeline('en', processors={'tokenize': 'spacy'})
STOP_WORDS = {
    "am", "are", "is", "was", "were", "be", "being", "been",
    "have", "has", "had", "does", "did", "could", "should",
    "would", "can", "shall", "will", "may", "might", "must", "let"
}


class StanfordParserSetup:
    @staticmethod
    def download_parser():
        jar_path = f"{os.environ['CLASSPATH']}.jar"
        if not os.path.exists(jar_path):
            StanfordParserSetup._download_parser_jar(jar_path)
        if not os.path.exists(os.environ['CLASSPATH']):
            StanfordParserSetup._extract_parser_jar(jar_path)
        if not os.path.exists(os.environ['STANFORD_MODELS']):
            StanfordParserSetup._extract_models_jar()

    @staticmethod
    def _download_parser_jar(jar_path):
        url = "https://nlp.stanford.edu/software/stanford-parser-full-2018-10-17.zip"
        urllib.request.urlretrieve(url, jar_path, StanfordParserSetup._reporthook)

    @staticmethod
    def _extract_parser_jar(jar_path):
        try:
            with zipfile.ZipFile(jar_path) as z:
                z.extractall(path=BASE_DIR)
        except (zipfile.BadZipFile, IOError):
            os.remove(jar_path)
            StanfordParserSetup.download_parser()
            StanfordParserSetup._extract_parser_jar(jar_path)

    @staticmethod
    def _extract_models_jar():
        models_jar = os.path.join(os.environ['CLASSPATH'], 'stanford-parser-3.9.2-models.jar')
        with zipfile.ZipFile(models_jar) as z:
            z.extractall(path=os.environ['CLASSPATH'])

    @staticmethod
    def _reporthook(count, block_size, total_size):
        global start_time
        if count == 0:
            start_time = time.perf_counter()
            return
        duration = time.perf_counter() - start_time
        progress_size = int(count * block_size)
        speed = int(progress_size / (1024 * duration))
        percent = min(int(count*block_size*100/total_size), 100)
        sys.stdout.write(f"\r...{percent}%, {progress_size / (1024 * 1024)} MB, {speed} KB/s, {duration} seconds passed")
        sys.stdout.flush()


class ISLTranslator:
    def __init__(self):
        self.sentences = []
        self.detailed_sentences = []
        self.words = []
        self.detailed_words = []
        self.final_words = []
        self.processed_output = []

    def process_text(self, text_input):
        self._clear_state()
        cleaned_text = self._clean_input(text_input)
        doc = STANZA_PIPELINE(cleaned_text)
        
        self._extract_sentences(doc)
        self._extract_words()
        self._reorder_words()
        self._preprocess()
        self._generate_final_output()
        
        return self._format_response()

    def _clean_input(self, text):
        return text.strip().replace("\n", "").replace("\t", "")

    def _extract_sentences(self, doc):
        for sentence in doc.sentences:
            self.sentences.append(sentence.text)
            self.detailed_sentences.append(sentence)

    def _extract_words(self):
        for sentence in self.detailed_sentences:
            words = [word.text for word in sentence.words]
            detailed_words = [word for word in sentence.words]
            self.words.append(words)
            self.detailed_words.append(detailed_words)

    def _reorder_words(self):
        for i, sentence_words in enumerate(self.words):
            self.words[i] = self._reorder_sentence(sentence_words)

    def _reorder_sentence(self, words):
        if all(len(word) == 1 for word in words):
            return words
            
        parser = StanfordParser()
        parse_tree = next(parser.parse(words))
        parent_tree = ParentedTree.convert(parse_tree)
        modified_tree = self._modify_tree_structure(parent_tree)
        return modified_tree.leaves()

    def _modify_tree_structure(self, parent_tree):
        tree_traversal_flag = self._label_subtrees(parent_tree)
        modified_tree = Tree('ROOT', [])
        i = 0

        for subtree in parent_tree.subtrees():
            if subtree.label() == "NP":
                i, modified_tree = self._handle_noun_clause(i, tree_traversal_flag, modified_tree, subtree)
            elif subtree.label() in ("VP", "PRP"):
                i, modified_tree = self._handle_verb_clause(i, tree_traversal_flag, modified_tree, subtree)

        for subtree in parent_tree.subtrees():
            for child in subtree.subtrees():
                if len(child.leaves()) == 1 and not tree_traversal_flag[child.treeposition()]:
                    tree_traversal_flag[child.treeposition()] = 1
                    modified_tree.insert(i, child)
                    i += 1

        return modified_tree

    def _label_subtrees(self, tree):
        return {subtree.treeposition(): 0 for subtree in tree.subtrees()}

    def _handle_noun_clause(self, index, flags, modified_tree, subtree):
        if not flags[subtree.treeposition()] and not flags[subtree.parent().treeposition()]:
            flags[subtree.treeposition()] = 1
            modified_tree.insert(index, subtree)
            index += 1
        return index, modified_tree

    def _handle_verb_clause(self, index, flags, modified_tree, subtree):
        for child in subtree.subtrees():
            if child.label() in ("NP", "PRP") and not flags[child.treeposition()]:
                flags[child.treeposition()] = 1
                modified_tree.insert(index, child)
                index += 1
        return index, modified_tree

    def _preprocess(self):
        self._remove_punctuation()
        self._filter_stop_words()
        self._lemmatize_words()

    def _remove_punctuation(self):
        for i, (words, details) in enumerate(zip(self.words, self.detailed_words)):
            filtered_words = []
            filtered_details = []
            for word, detail in zip(words, details):
                if detail.upos != 'PUNCT':
                    filtered_words.append(word)
                    filtered_details.append(detail)
            self.words[i] = filtered_words
            self.detailed_words[i] = filtered_details

    def _filter_stop_words(self):
        self.final_words = []
        for words, details in zip(self.words, self.detailed_words):
            filtered = [word for word, detail in zip(words, details) if word.lower() not in STOP_WORDS]
            self.final_words.append(filtered)

    def _lemmatize_words(self):
        for i, (details, words) in enumerate(zip(self.detailed_words, self.final_words)):
            for j, (detail, word) in enumerate(zip(details, words)):
                if len(word) > 1:
                    self.final_words[i][j] = detail.lemma

    def _generate_final_output(self):
        self.processed_output = []
        for sentence in self.final_words:
            processed = []
            for word in sentence:
                if word.lower() not in VALID_WORDS:
                    processed.extend(list(word.upper()))
                else:
                    processed.append(word.lower())
            self.processed_output.append(processed)

    def _format_response(self):
        response = {}
        for i, word in enumerate([item for sublist in self.processed_output for item in sublist], 1):
            response[i] = word.upper() if len(word) == 1 else word
        return response

    def _clear_state(self):
        self.sentences.clear()
        self.detailed_sentences.clear()
        self.words.clear()
        self.detailed_words.clear()
        self.final_words.clear()
        self.processed_output.clear()


# Initialize application components
StanfordParserSetup.download_parser()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    text = request.form.get('text', '')
    if not text:
        return jsonify({})
    
    translator = ISLTranslator()
    return jsonify(translator.process_text(text))

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0')