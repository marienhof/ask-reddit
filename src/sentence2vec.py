import re
import numpy as np
import gensim
from scipy.spatial.distance import cosine


WHITESPACE_REGEX = re.compile("\s+")

REPLACEMENTS = {  # todo: improve this
    "'s": " is",
    "'d": " would",
    "'re": " are"
}


def normalize(sentence):    
    sentence = re.sub("[\.\?,!:' ]+", " ", sentence, flags=re.I + re.S).strip().lower()
    for (to_replace, replacement) in REPLACEMENTS.items():
        sentence = sentence.replace(to_replace, replacement)
    return sentence


def split_words(sentence):
    return WHITESPACE_REGEX.split(sentence)


def load_word2vec():
    BASE_DIR = "/Users/stuhlmueller/Projects/dialogue-markets/theory/replaybot/word2vec"
    model_download_path = "%s/blog_posts_300_c_40.word2vec" % BASE_DIR
    model = gensim.models.Word2Vec.load(model_download_path)
    return model


def sentence2vec(sentence):
    # Split sentence into lowercase words
    words = split_words(normalize(sentence))
    # Remove words that word2vec model doesn't know
    words = [w for w in words if w in word2vec]
    # Get list of vectors
    vectors = [word2vec[w] for w in words]
    if len(vectors) == 0:
        return None
    # Compute average vector
    count = 1
    vector_sum = vectors[0]
    for v in vectors[1:]:
        count += 1
        vector_sum = np.add(vector_sum, v)
    avg_vector = np.nan_to_num(vector_sum/count)
    return avg_vector


def distance(s1, s2):
    v1 = sentence2vec(s1)
    v2 = sentence2vec(s2)
    if v1 is None or v2 is None:
        return 1.0 # FIXME: what to do here?
    return cosine(v1, v2)


def similarity(s1, s2):
    return -distance(s1, s2)


word2vec = load_word2vec()
