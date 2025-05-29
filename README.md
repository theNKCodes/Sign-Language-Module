
---

# 🤟 Sign Language Translation Evaluation API

This project provides a **Flask-based backend API** that evaluates sign language-translated text (hypothesis) against reference text using various NLP metrics. It aims to assess the linguistic quality and correctness of machine-translated sign language text.

---

## 🚀 Features

* ✅ Grammar correction using [Gramformer](https://github.com/PrithivirajDamodaran/Gramformer)
* 📊 Evaluation Metrics:

  * **BLEU, METEOR, TER, ROUGE-1, ROUGE-2, ROUGE-L**
* 💬 Linguistic Quality Analysis:

  * Part-of-Speech (POS) Accuracy
  * Named Entity Recognition (NER) Accuracy
  * Lemmatization Accuracy
  * Phrase Preservation (Noun Phrases)
* 🔍 Text Preprocessing Statistics:

  * Token count
  * Average token length
  * Stopwords removal stats
  * POS tag distribution
* 🧠 Named Entity & Lemma Stats
* 🗄️ MySQL integration for storing evaluations

---

## 📂 Project Structure

```
SIGN-LANGUAGE-MODULE/
├── app/
│   └── backend/
│       ├── new/
│       └── old/
│       ├── app.py
│       ├── eva_with_headers.csv
│       ├── evaluation_data.csv
│       ├── graphs.ipynb
│       ├── new.py
│       └── nlp.ipynb
│       └── requirements.txt
├── components/
├── hooks/
├── lib/
├── node_modules/
├── public/
├── styles/
├── .gitignore
├── bun.lockb
├── components.json
├── gram.ipynb
├── next-env.d.ts
├── next.config.mjs
├── package.json
├── postcss.config.mjs
├── README.md
├── tailwind.config.js

```

---

## ⚙️ Tech Stack

* **Python 3.8+**
* **Flask**
* **MySQL**
* **spaCy**
* **NLTK**
* **SacreBLEU, ROUGE, METEOR**
* **Gramformer (for grammar correction)**

---

## 🛠️ Setup Instructions

### 🔧 Backend Setup (Python)

> Navigate to the backend folder and install the dependencies.

### 1. Clone the Repository

```bash
git clone https://github.com/theNKCodes/Sign-Language-Module.git
cd Sign-Language-Module/backend
```

### 2. Install Dependencies

> It's recommended to use a virtual environment.

```bash
pip install -r requirements.txt
```

Sample `requirements.txt`:

```txt
Flask
flask-cors
nltk
spacy
sacrebleu
rouge-score
torch
gramformer
python-dotenv
mysql-connector-python
```

### 3. Download Gramformer

```bash
pip install -U git+https://github.com/PrithivirajDamodaran/Gramformer.git
```

### 4. Configure `.env` file

Create a `.env` file in the `backend` directory:

```
DB_HOST=localhost
DB_USER=root
DB_PASS=yourpassword
DB_NAME=sign_language
```

### 5. Run the Flask App

```bash
python app.py
```

---

---

### 🧩 Frontend Setup (Next.js)

1. Ensure you have [`bun`](https://bun.sh/) installed.
2. Start the development server:

```bash
bun install
bun run dev
```

> You should see the app running at: [http://localhost:3000](http://localhost:3000)

---

---

## 🔁 Workflow Diagram
<p align="center">
  <img src="https://github.com/theNKCodes/Sign-Language-Module/blob/main/Workflow.jpg?raw=true" width="600" />
</p>



---

## 📡 API Endpoints

### `/evaluate` - Evaluate Translation

**Method**: `POST`
**Content-Type**: `application/json`

#### Request Body:

```json
{
  "reference": "The boy is playing football.",
  "hypothesis": "Boy play foot ball."
}
```

#### Response:

```json
{
  "message": "Translation evaluation complete",
  "Execution Time (seconds)": 1.23,
  "BLEU Score": 85.21,
  "METEOR Score": 0.65,
  "TER Score": 12.34,
  "ROUGE Scores": {
    "ROUGE-1": 0.88,
    "ROUGE-2": 0.70,
    "ROUGE-L": 0.85
  },
  "Linguistic Accuracy": {
    "POS Accuracy": 90.0,
    "NER Accuracy": 100.0,
    "Lemmatization Accuracy": 92.3,
    "Phrase Preservation": 80.0
  },
  "metrics": {
    "num_tokens": 5,
    "avg_token_length": 4.2,
    "num_stopwords_removed": 1,
    "stopwords_removal_percentage": 20.0,
    "pos_distribution": {
      "NN": 2,
      "VB": 1
    }
  }
}
```

---

### `/process` - Grammar Correction & Preprocessing

**Method**: `POST`
**Content-Type**: `application/json`

#### Request Body:

```json
{
  "text": "He go to school every day"
}
```

#### Response:

```json
{
  "corrected_text": "He goes to school every day",
  "tokens": [...],
  ...
}
```

---

## 🧠 Example Use Case

This API is useful for:

* Evaluating outputs from sign language translation models
* Assessing translation quality from educational or accessibility tools
* NLP research focused on grammar correction and linguistic evaluation

---

## 🧾 Database Schema (MySQL)

Table: `evaluations`

| Column                         | Type     |
| ------------------------------ | -------- |
| id                             | INT (PK) |
| input                          | TEXT     |
| reference                      | TEXT     |
| hypothesis                     | TEXT     |
| bleu\_score                    | FLOAT    |
| meteor\_score                  | FLOAT    |
| ter\_score                     | FLOAT    |
| rouge1, rouge2, rougeL         | FLOAT    |
| pos\_accuracy                  | FLOAT    |
| ner\_accuracy                  | FLOAT    |
| lemmatization\_accuracy        | FLOAT    |
| phrase\_preservation           | FLOAT    |
| num\_tokens                    | INT      |
| avg\_token\_length             | FLOAT    |
| num\_stopwords\_removed        | INT      |
| stopwords\_removal\_percentage | FLOAT    |
| pos\_distribution              | JSON     |
| execution\_time                | FLOAT    |

---

## 🙌 Credits

* Built with ❤️ using Flask, spaCy, NLTK, and Gramformer.
* Created as part of a **Sign Language Translation Evaluation System** project.

---

## 📄 License

[MIT License](LICENSE)

---
