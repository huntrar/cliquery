# -*- coding: utf-8 -*-
"""Credit to https://github.com/xiaoxu193/PyTeaser"""

from __future__ import print_function
from collections import Counter
import itertools
from math import fabs
from re import split as regex_split, sub as regex_sub, UNICODE as REGEX_UNICODE

from .compat import iterkeys, uni


STOPWORDS = set([
    "-", " ", ",", ".", "a", "e", "i", "o", "u", "t", "about", "above",
    "above", "across", "after", "afterwards", "again", "against", "all",
    "almost", "alone", "along", "already", "also", "although", "always",
    "am", "among", "amongst", "amoungst", "amount", "an", "and",
    "another", "any", "anyhow", "anyone", "anything", "anyway",
    "anywhere", "are", "around", "as", "at", "back", "be", "became",
    "because", "become", "becomes", "becoming", "been", "before",
    "beforehand", "behind", "being", "below", "beside", "besides",
    "between", "beyond", "both", "bottom", "but", "by", "call", "can",
    "cannot", "can't", "co", "con", "could", "couldn't", "de",
    "describe", "detail", "did", "do", "done", "down", "due", "during",
    "each", "eg", "eight", "either", "eleven", "else", "elsewhere",
    "empty", "enough", "etc", "even", "ever", "every", "everyone",
    "everything", "everywhere", "except", "few", "fifteen", "fifty",
    "fill", "find", "fire", "first", "five", "for", "former",
    "formerly", "forty", "found", "four", "from", "front", "full",
    "further", "get", "give", "go", "got", "had", "has", "hasnt",
    "have", "he", "hence", "her", "here", "hereafter", "hereby",
    "herein", "hereupon", "hers", "herself", "him", "himself", "his",
    "how", "however", "hundred", "i", "ie", "if", "in", "inc", "indeed",
    "into", "is", "it", "its", "it's", "itself", "just", "keep", "last",
    "latter", "latterly", "least", "less", "like", "ltd", "made", "make",
    "many", "may", "me", "meanwhile", "might", "mill", "mine", "more",
    "moreover", "most", "mostly", "move", "much", "must", "my", "myself",
    "name", "namely", "neither", "never", "nevertheless", "new", "next",
    "nine", "no", "nobody", "none", "noone", "nor", "not", "nothing",
    "now", "nowhere", "of", "off", "often", "on", "once", "one", "only",
    "onto", "or", "other", "others", "otherwise", "our", "ours",
    "ourselves", "out", "over", "own", "part", "people", "per",
    "perhaps", "please", "put", "rather", "re", "said", "same", "see",
    "seem", "seemed", "seeming", "seems", "several", "she", "should",
    "show", "side", "since", "sincere", "six", "sixty", "so", "some",
    "somehow", "someone", "something", "sometime", "sometimes",
    "somewhere", "still", "such", "take", "ten", "than", "that", "the",
    "their", "them", "themselves", "then", "thence", "there",
    "thereafter", "thereby", "therefore", "therein", "thereupon",
    "these", "they", "thickv", "thin", "third", "this", "those",
    "though", "three", "through", "throughout", "thru", "thus", "to",
    "together", "too", "top", "toward", "towards", "twelve", "twenty",
    "two", "un", "under", "until", "up", "upon", "us", "use", "very",
    "via", "want", "was", "we", "well", "were", "what", "whatever",
    "when", "whence", "whenever", "where", "whereafter", "whereas",
    "whereby", "wherein", "whereupon", "wherever", "whether", "which",
    "while", "whither", "who", "whoever", "whole", "whom", "whose",
    "why", "will", "with", "within", "without", "would", "yet", "you",
    "your", "yours", "yourself", "yourselves", "the", "reuters", "news",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday", "mon", "tue", "wed", "thu", "fri", "sat", "sun",
    "rappler", "rapplercom", "inquirer", "yahoo", "home", "sports",
    "1", "10", "2012", "sa", "says", "tweet", "pm", "home", "homepage",
    "sports", "section", "newsinfo", "stories", "story", "photo",
    "2013", "na", "ng", "ang", "year", "years", "percent", "ko", "ako",
    "yung", "yun", "2", "3", "4", "5", "6", "7", "8", "9", "0", "time",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "government", "police"
])

IDEAL = 20.0


def summarize(title, text):
    """Summarize text using the title as a reference"""
    summaries = []
    sentences = split_sentences(text)
    keys = get_keywords(text)
    title_words = split_words(title)

    if len(sentences) <= 5:
        return sentences

    # Score sentences, and use the top 5 sentences
    ranks = get_score(sentences, title_words, keys).most_common(5)
    for rank in ranks:
        summaries.append(rank[0])

    return [uni(x) for x in summaries]


def get_score(sentences, title_words, keywords):
    """Score sentences based on different features"""
    sen_size = len(sentences)
    ranks = Counter()
    for i, sen in enumerate(sentences):
        sentence = split_words(sen)
        title_feature = title_score(title_words, sentence)
        sentence_length = length_score(sentence)
        sentence_pos = sentence_position(i+1, sen_size)
        sbs_feature = sbs(sentence, keywords)
        dbs_feature = dbs(sentence, keywords)
        frequency = (sbs_feature + dbs_feature) / 2.0 * 10.0

        # Weighted average of scores from four categories
        total_score = (title_feature*1.5 + frequency*2.0 +
                       sentence_length*1.0 + sentence_pos*1.0) / 4.0
        ranks[sen] = total_score
    return ranks


def sbs(words, keywords):
    """Summation based selection"""
    score = 0.0
    if len(words) == 0:
        return 0
    for word in words:
        if word in keywords:
            score += keywords[word]
    return (1.0 / fabs(len(words)) * score)/10.0


def dbs(words, keywords):
    """Density based selection"""
    if len(words) == 0:
        return 0

    summ = 0
    first = []
    second = []

    for i, word in enumerate(words):
        if word in keywords:
            score = keywords[word]
            if first == []:
                first = [i, score]
            else:
                second = first
                first = [i, score]
                dif = first[0] - second[0]
                summ += (first[1]*second[1]) / (dif ** 2)

    # Number of intersections
    k = len(set(iterkeys(keywords)).intersection(set(words))) + 1
    return 1/(k*(k+1.0))*summ


def split_words(text):
    """Split a string into array of words"""
    try:
        # Strip special characters
        text = regex_sub(r'[^\w ]', '', text, flags=REGEX_UNICODE)
        return [x.strip('.').lower() for x in text.split()]
    except TypeError:
        print("Error while splitting characters.")
        return None


def get_keywords(text):
    """Get the top 10 keywords and their frequency scores
        ignores blacklisted words in STOPWORDS,
        counts the number of occurrences of each word
    """
    text = split_words(text)
    num_words = len(text)  # of words before removing blacklist words
    freq = Counter(x for x in text if x not in STOPWORDS)

    min_size = min(10, len(freq))  # get first 10
    keywords = {x: y for x, y in freq.most_common(min_size)}  # recreate a dict

    for k in keywords:
        article_score = keywords[k]*1.0 / num_words
        keywords[k] = article_score * 1.5 + 1

    return keywords


def split_sentences(text):
    """
    The regular expression matches all sentence ending punctuation and
    splits the string at those points.
    At this point in the code, the list looks like this ["Hello, world", "!"
    ... ]. The punctuation and all quotation marks
    are separated from the actual text. The first s_iter line turns each group
    of two items in the list into a tuple,
    excluding the last item in the list (the last item in the list does not
    need to have this performed on it). Then,
    the second s_iter line combines each tuple in the list into a single item
    and removes any whitespace at the beginning
    of the line. Now, the s_iter list is formatted correctly but it is missing
    the last item of the sentences list. The second to last line adds this
    item to the s_iter list and the last line returns the full list.
    """
    sentences = regex_split('(?<![A-ZА-ЯЁ])([.!?]"?)(?=\s+\"?[A-ZА-ЯЁ])',
                            text, flags=REGEX_UNICODE)
    s_iter = itertools.izip(*[iter(sentences[:-1])] * 2)
    s_iter = [''.join(x for x in y).lstrip() for y in s_iter]
    s_iter.append(sentences[-1])
    return s_iter


def length_score(sentence):
    """Score the sentence based on length"""
    return 1 - fabs(IDEAL - len(sentence)) / IDEAL


def title_score(title, sentence):
    """Score the title based on occurrence of words in the sentence"""
    title = [x for x in title if x not in STOPWORDS]
    count = 0.0
    for word in sentence:
        if word not in STOPWORDS and word in title:
            count += 1.0

    if len(title) == 0:
        return 0.0

    return count/len(title)


def sentence_position(i, size):
    """Different sentence positions indicate different
        probability of being an important sentence
    """
    normalized = i*1.0 / size
    if 0 < normalized <= 0.1:
        return 0.17
    elif 0.1 < normalized <= 0.2:
        return 0.23
    elif 0.2 < normalized <= 0.3:
        return 0.14
    elif 0.3 < normalized <= 0.4:
        return 0.08
    elif 0.4 < normalized <= 0.5:
        return 0.05
    elif 0.5 < normalized <= 0.6:
        return 0.04
    elif 0.6 < normalized <= 0.7:
        return 0.06
    elif 0.7 < normalized <= 0.8:
        return 0.04
    elif 0.8 < normalized <= 0.9:
        return 0.04
    elif 0.9 < normalized <= 1.0:
        return 0.15
    else:
        return 0
