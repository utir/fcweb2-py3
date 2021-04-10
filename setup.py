import nltk

def download_nltk_data():
    nltk.download('stopwords')
    nltk.download('punkt')
    nltk.download('conll2002')
    nltk.download('wordnet')
    nltk.download('maxent_treebank_pos_tagger')