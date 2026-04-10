# NLP Specs: Topic Modeling Pipeline

## 1. Objective
Transform scraped review text into topic distributions using LDA. Output: 5 tourism themes (e.g., adventure, relaxation, culture).

## 2. Tech Stack
- **Spacy**: `en_core_web_sm` model for tokenization, lemmatization, stop words
- **Scikit-learn**: `TfidfVectorizer`, `LatentDirichletAllocation`
- **Numpy**: Matrix operations

## 3. Pipeline Stages

### Stage 1: Text Cleaning
- **Module**: `src/nlp/cleaner.py`
- **Function**:
```python
def clean_text(text: str) -> str:
    """
    Remove HTML tags, special chars, lowercase.
    
    Args:
        text: Raw review text from scraper
    
    Returns:
        Cleaned text (lowercase, no special chars)
    """
    pass
```
- **Operations**:
  1. Remove HTML tags (`<p>`, `<br>`, etc.)
  2. Remove special chars (keep alphanumeric + spaces)
  3. Lowercase all text
  4. Strip leading/trailing whitespace

### Stage 2: Spacy Preprocessing
- **Module**: `src/nlp/preprocessor.py`
- **Function**:
```python
import spacy

nlp = spacy.load("en_core_web_sm")

def preprocess(text: str) -> list[str]:
    """
    Tokenize, lemmatize, remove stop words.
    
    Args:
        text: Cleaned text from Stage 1
    
    Returns:
        List of lemmatized tokens (no stop words)
    """
    pass
```
- **Operations**:
  1. Tokenize with Spacy
  2. Lemmatize each token
  3. Remove stop words (Spacy default list)
  4. Remove tokens < 3 chars

### Stage 3: Vectorization
- **Module**: `src/nlp/vectorizer.py`
- **Function**:
```python
from sklearn.feature_extraction.text import TfidfVectorizer

def vectorize(docs: list[list[str]]) -> tuple[csr_matrix, TfidfVectorizer]:
    """
    Convert token lists to TF-IDF matrix.
    
    Args:
        docs: List of token lists from Stage 2
    
    Returns:
        (tfidf_matrix, fitted_vectorizer)
    """
    pass
```
- **Parameters**:
  - `max_features=1000`: Limit vocabulary size
  - `min_df=2`: Ignore terms in < 2 docs
  - `max_df=0.8`: Ignore terms in > 80% of docs

### Stage 4: Topic Modeling
- **Module**: `src/nlp/topic_model.py`
- **Function**:
```python
from sklearn.decomposition import LatentDirichletAllocation

def fit_lda(tfidf_matrix, n_topics: int = 5) -> LatentDirichletAllocation:
    """
    Fit LDA model to TF-IDF matrix.
    
    Args:
        tfidf_matrix: Output from Stage 3
        n_topics: Number of topics to extract
    
    Returns:
        Fitted LDA model
    """
    pass
```
- **Parameters**:
  - `n_components=5`: Default topic count
  - `max_iter=10`: Iterations (fast for testing)
  - `random_state=42`: Reproducibility

## 4. Input/Output
- **Input**: `.jsonl` file from scraper (only `review_text` field used)
- **Output**:
  - Topic-document matrix: `numpy.ndarray` shape `(n_docs, n_topics)`
  - Top terms per topic: `dict[int, list[str]]` (top 10 terms)

## 5. Model Parameters
- Default topics: `n_topics=5`
- LDA iterations: `max_iter=10` (increase to 100 for production)
- Random seed: `random_state=42` (all random operations)

## 6. Testing Requirements
- **Fixture**: `tests/fixtures/sample_reviews.json` with 5 sample reviews
- **Test cases**:
  - Stage 1: "Hello <b>World</b>!" → "hello world"
  - Stage 2: "running quickly" → ["run", "quickly"]
  - Stage 3: Token lists → sparse matrix shape correct
  - Stage 4: With fixed seed → same topics each run
- **Reproducibility**: All tests use `random_state=42`

## 7. Entry Points
- **Individual stages**: `cleaner.py`, `preprocessor.py`, `vectorizer.py`, `topic_model.py`
- **Pipeline orchestrator**: `src/nlp/pipeline.py`
```python
def run_pipeline(input_file: str, n_topics: int = 5) -> dict:
    """
    Run full NLP pipeline: clean → preprocess → vectorize → model.
    
    Args:
        input_file: Path to .jsonl from scraper
        n_topics: Number of topics to extract
    
    Returns:
        {
            "topic_terms": dict[int, list[str]],
            "doc_topics": numpy.ndarray
        }
    """
    pass
```
