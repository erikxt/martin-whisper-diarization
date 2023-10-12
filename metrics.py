import nltk
# nltk.download('wordnet')
import re
from nltk.translate import meteor_score
from rouge import Rouge


rouge = Rouge()


def remove_speaker_tag(transcript):
    transcript = transcript.lower()
    speakerRegex = re.compile(r'Speaker \d:')
    return speakerRegex.sub('', transcript).replace('\n', ' ')


def get_references(transcript):
    sentences = nltk.tokenize.sent_tokenize(transcript)
    references = []
    for sent in sentences:
        references.append(nltk.tokenize.word_tokenize(sent))
    return references


def get_candidate(summary):
    summary = summary.lower()
    candidate = nltk.tokenize.word_tokenize(summary)
    return candidate


def get_bleu_score(references, candidate):
    score = nltk.translate.bleu_score.sentence_bleu(references, candidate)
    return score


def get_rouge_score(references, candidate):
    score = rouge.get_scores(candidate, references)
    return score[0]['rouge-l']['f']


def get_meteor_score(reference_text, predicted_text):
    """
    Calculates the METEOR score for a predicted text compared to a reference text.
    reference_text: a string representing the reference text.
    predicted_text: a string representing the predicted text.
    returns: a float representing the METEOR score.
    """
    return meteor_score.meteor_score(reference_text, predicted_text)