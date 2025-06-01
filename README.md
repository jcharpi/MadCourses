# Skill Course Aggregator

Automatically rank university courses against a set of skill phrases using sentence embeddings.

The script **`skill_course_aggregator.py`** turns a plain‑text CSV of course titles & descriptions into recommendations that best match your chosen skills. It downloads the `all‑mpnet‑base‑v2` embedding model on first run and caches course vectors, so subsequent runs are instant.

---

## ✨ Features

| Feature | Details |
|---------|---------|
| **Semantic matching** | Uses normalized cosine‑similarity between skill vectors and course vectors (Sentence‑Transformers) |
| **Batch ranking** | Returns top‑k courses _per skill_ **and** overall centroid ranking |
| **Disk cache** | Persists course embeddings to a companion `.npy` file; recompute only when the CSV changes |
| **Configurable** | Change skills, model, `TOP_K`, and CSV path at the top of the script |

---

## 🚀 Quick Start

### 1. Prerequisites

* **Python 3.9 – 3.12** (check with `python --version`)
* An internet connection the first time you run the script (≈830 MB model download)

### 2. Clone & setup

```bash
# Clone your repo or copy the files into a folder
cd skill‑course‑aggregator

# Create & activate a fresh virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Always upgrade pip & wheel first
python -m pip install --upgrade pip wheel

# Install required packages
pip install -r requirements.txt
```

### 3. Prepare your data

Place **`courses.csv`** in the project root. The file **must** contain the columns:

* `Title` – course code or name
* `Description` – one‑paragraph summary

### 4. Run the script

```bash
python skill_course_aggregator.py
```

Sample console output (with the default skills):

```
Skill: 'Building athlete analytics dashboards and user interfaces'
  → KINES 350 – Sports Data Visualization (score 0.823)
  → CS 559 – Computer Graphics (score 0.812)
  …

Top 5 courses overall:
  → STAT 471 – Applied Regression (centroid_score 0.812)
  → KINES 350 – Sports Data Visualization (centroid_score 0.808)
  …
```

The first run may take a minute while the model downloads and the script builds the vector cache. Subsequent runs finish in seconds.

---

## 🛠 Configuration

Open **`skill_course_aggregator.py`** and tweak the block near the top:

```python
CSV_PATH   = Path("./courses.csv")
SKILLS     = ["Build dashboards …", "Implement real‑time …", …]
TOP_K      = 5
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
```

* **Changing the CSV path** automatically creates/uses a matching `.npy` cache.
* **Switching to another Sentence‑Transformer** will download that model on first use.

---

## 🗂 Project Structure

```
│  README.md
│  requirements.txt
│  skill_course_aggregator.py
│  courses.csv               <- your input data
│  courses.npy               <- auto‑generated embedding cache
└─ .venv/                     <- (optional) virtual‑environment files
```
