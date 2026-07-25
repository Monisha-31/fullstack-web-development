import pandas as pd
import numpy as np
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils import clean_resume_text

# Resolve artifact paths relative to this file, not the process's current
# working directory. This avoids "Failed to load category models" errors
# when the app is launched from a different folder (e.g. via a launcher
# script, systemd service, or an IDE's run button).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTORIZER_PATH = os.path.join(BASE_DIR, "vectorizer.pkl")
CATEGORY_VECTORS_PATH = os.path.join(BASE_DIR, "category_vectors.pkl")
CATEGORY_KEYWORDS_PATH = os.path.join(BASE_DIR, "category_keywords.pkl")


def extract_keywords(text, vectorizer):
    """
    Tokenize `text` using the SAME analyzer (lowercasing, tokenization,
    stop-word removal) that was used to fit `vectorizer` and build
    category_keywords during training.

    This used to be done with a separate spaCy pipeline that lemmatized
    words (e.g. "managed" -> "manage", "skills" -> "skill") while
    category_keywords were built from the vectorizer's raw, unlemmatized
    vocabulary (e.g. "managed", "skills"). Because the two token sets
    lived in different vocabularies, matched_skills/missing_skills were
    frequently wrong (skills the resume clearly had would show up as
    "missing"). Reusing the vectorizer's own analyzer guarantees both
    sides speak the same vocabulary, and also removes the spaCy model
    download step, which could fail or hang the app in environments
    without internet access.
    """
    analyzer = vectorizer.build_analyzer()
    return set(analyzer(text))


def train_and_save_model(csv_path):
    print("Loading dataset...")
    df = pd.read_csv(csv_path)

    print("Cleaning text...")
    df['Cleaned_Resume'] = df['Resume_str'].astype(str).apply(clean_resume_text)

    print("Training Vectorizer...")
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    X = vectorizer.fit_transform(df['Cleaned_Resume'])

    categories = df['Category'].unique()
    category_vectors = {}
    category_keywords = {}

    feature_names = vectorizer.get_feature_names_out()

    for cat in categories:
        cat_indices = df[df['Category'] == cat].index
        cat_vector = np.squeeze(np.asarray(X[cat_indices].mean(axis=0)))
        category_vectors[cat] = cat_vector

        top_indices = cat_vector.argsort()[-30:][::-1]
        top_keywords = set([feature_names[i] for i in top_indices])
        category_keywords[cat] = top_keywords

    print("Saving Models to disk...")
    with open(VECTORIZER_PATH, 'wb') as f:
        pickle.dump(vectorizer, f)
    with open(CATEGORY_VECTORS_PATH, 'wb') as f:
        pickle.dump(category_vectors, f)
    with open(CATEGORY_KEYWORDS_PATH, 'wb') as f:
        pickle.dump(category_keywords, f)

    print("Model training complete and saved.")


def load_models():
    """Loads previously saved artifacts."""
    if not (os.path.exists(VECTORIZER_PATH) and os.path.exists(CATEGORY_VECTORS_PATH)):
        return None, None, None
    with open(VECTORIZER_PATH, 'rb') as f:
        vectorizer = pickle.load(f)
    with open(CATEGORY_VECTORS_PATH, 'rb') as f:
        category_vectors = pickle.load(f)
    with open(CATEGORY_KEYWORDS_PATH, 'rb') as f:
        category_keywords = pickle.load(f)
    return vectorizer, category_vectors, category_keywords


def analyze_resume(resume_text, target_category):
    """Takes in raw user text and target category. Calculates suitability & skill gap."""
    vectorizer, category_vectors, category_keywords = load_models()
    if vectorizer is None:
        raise Exception("Model not trained yet.")

    cleaned_txt = clean_resume_text(resume_text)

    resume_vector = vectorizer.transform([cleaned_txt]).toarray()[0]

    target_vector = category_vectors.get(target_category)
    if target_vector is None:
        raise ValueError("Invalid target category.")

    score = cosine_similarity([resume_vector], [target_vector])[0][0] * 100
    if score < 50:
        score = score * 1.5
    score = min(100.0, score)

    # Keyword extraction — now uses the vectorizer's own analyzer so it
    # matches the vocabulary category_keywords was built from.
    resume_keywords = extract_keywords(cleaned_txt, vectorizer)
    target_keywords = category_keywords[target_category]

    matched_skills = target_keywords.intersection(resume_keywords)
    missing_skills = target_keywords.difference(resume_keywords)

    return {
        "score": score,
        "matched_skills": list(matched_skills),
        "missing_skills": list(missing_skills)
    }
