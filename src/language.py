STOP_WORDS = ['a', 'the', 'of', 'is', 'for', 'i', 'to']

BAD_WORDS = set(open("../data/bad_words.txt").read().split("\n"))


def clean_step(s):
    s = s.replace("\n", " ")
    s = s.replace("  ", " ")
    s = s.replace("[serious]", " ")
    s = s.strip("\n ")
    return s


def clean(s):
    while True:
        s_next = clean_step(s)
        if s == s_next:
            break
        else:
            s = s_next
    return s


def sentence_to_words(sentence):
    sentence = sentence.strip("\n .!?")
    words = [word.strip(",.") for word in sentence.split(" ")]
    return words


def is_nasty(sentence):
    words = sentence_to_words(sentence)
    for word in words:
        if word in BAD_WORDS:
            return True
    return False


def filter_stopwords(words):
    return [word for word in words if word not in STOP_WORDS]
