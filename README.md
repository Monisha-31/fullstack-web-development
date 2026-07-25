# AI Resume Matching & Skill Gap Analyzer

A web app that scores how well a resume fits a target job role and lists
which skills are already present vs. missing, based on a TF-IDF model
trained on a real resume dataset (24 job categories, ~2,500 resumes).

Includes two front ends that both talk to the same model:
- A custom HTML/CSS/JS site (in `frontend/`), served by Flask (`server.py`)
- A Streamlit app (`app.py`), if you'd rather not deal with a frontend at all

The model is **already trained** — `vectorizer.pkl`, `category_vectors.pkl`,
and `category_keywords.pkl` are included, built from `Resume.csv`. You do
not need to run `train.py` unless you want to retrain on different data.

## 1. Install dependencies

From inside this folder:

```
pip install -r requirements.txt
```

## 2. Run it

**Option A — HTML/CSS/JS website (recommended, matches the design in `frontend/`)**

```
python server.py
```

Then open **http://127.0.0.1:5000** in your browser (not the `frontend/index.html`
file directly, and not through a separate tool like VS Code Live Server —
open that exact URL).

**Option B — Streamlit app**

```
streamlit run app.py
```

This opens automatically in your browser.

## 3. Using it

1. Select a target job role from the dropdown (24 roles available: HR,
   INFORMATION-TECHNOLOGY, ENGINEERING, SALES, etc.)
2. Upload a resume (PDF, DOCX, or TXT)
3. Click "Analyze Resume"
4. You'll see:
   - A suitability score (0–100%) shown as a gauge
   - **Matched Skills** — keywords from the target role's profile that your
     resume already has
   - **Missing Skills** — keywords common in that role's resumes but not
     found in yours, i.e. what to add to strengthen the resume for that role

## Folder structure

```
resume-analyzer/
├── app.py                  Streamlit UI
├── server.py                Flask API + serves the HTML frontend
├── model.py                 Scoring/matching logic
├── utils.py                 Resume text extraction (PDF/DOCX/TXT)
├── train.py                 Retrains the model from Resume.csv (optional)
├── requirements.txt
├── Resume.csv                Training dataset
├── vectorizer.pkl            \
├── category_vectors.pkl       > Pre-trained model artifacts
├── category_keywords.pkl     /
└── frontend/
    ├── index.html
    ├── script.js
    └── style.css
```

## Retraining on different/updated data (optional)

Replace `Resume.csv` with your own dataset (must have `Resume_str` and
`Category` columns), then run:

```
python train.py
```

This regenerates the three `.pkl` files.

## Troubleshooting

- **"Error loading roles"** — make sure you opened the site at
  `http://127.0.0.1:5000` (from `python server.py`), not via a separate
  static file server or by double-clicking `index.html`.
- **`ModuleNotFoundError`** — run `pip install -r requirements.txt` again;
  if you have multiple Python installs, use `python -m pip install -r requirements.txt`
  to be sure it installs into the Python you're actually running.
- **Port 5000 already in use** — close whatever else is using it, or edit
  the last line of `server.py` to use a different port (e.g. `port=5050`)
  and update `frontend/script.js`'s `API_URL` to match.
