import openai
import os

openai.api_key = os.environ.get("OPENAI_API_KEY")


def gen_summary(file_name):
    # open the srt file
    srt_path = os.path.join("tmp_audio", file_name + ".srt")
    with open(srt_path, "r") as f:
        srt = f.read()
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following text and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points."
                },
                {
                    "role": "user",
                    "content": srt
                }
            ]
        )
        str = response['choices'][0]['message']['content']
    with open(os.path.join("tmp_summary", file_name + ".txt"), "w") as f:
        f.write(str)    
    
    
def action_item_extraction(file_name):
    srt_path = os.path.join("tmp_audio", file_name + ".srt")
    with open(srt_path, "r") as f:
        srt = f.read()
        response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI expert in analyzing conversations and extracting action items. \
                        Please review the text and identify any tasks, assignments, \
                        or actions that were agreed upon or mentioned as needing to be done. \
                        These could be tasks assigned to specific individuals, or general actions that the group has decided to take. \
                        Please list these action items clearly and concisely. \
                        And the format of the action items should be json array. \
                        if there is no action item, please return empty array."
                },
                {
                    "role": "user",
                    "content": srt
                }
            ]
        )
        return response['choices'][0]['message']['content']

# print(openai.api_key)
# print(openai.Model.list())
# print(openai.Engine.list())

def get_transcript(file_name, format="srt"):
    srt_path = os.path.join("tmp_audio", file_name + "." + format)
    with open(srt_path, "r", encoding='utf-8-sig') as f:
        transcript = f.read()
        return transcript

def potential_question_extraction(file_name):
    transcript = get_transcript(file_name=file_name)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are an AI expert in analyzing conversations and extracting action items. \
                    Please review the text and ask some possible questions abhout the text. \
                    These sould be questions based on the text and catch the main points. \
                    Please list these questions clearly and concisely. \
                    And the format of the questions should be json array. \
                    if there is no question, please return empty array."
            },
            {
                "role": "user",
                "content": transcript
            }
        ]
    )
    questions = response['choices'][0]['message']['content']
    question_path = os.path.join('tmp_questions', file_name + '.txt')
    with open(question_path, 'w') as f:
        f.write(questions)
    return questions

# potential_question_extraction('default')
# gen_summary('default')
import re
from nltk.translate.bleu_score import corpus_bleu, sentence_bleu
from nltk.tokenize import word_tokenize
import nltk
# nltk.download('punkt')
str = get_transcript(file_name='default', format='txt')
srt_path = os.path.join("tmp_audio", "default" + ".txt")
f = open(srt_path, "r", encoding='utf-8-sig')
transcript = f.read().lower()
speakerRegex = re.compile(r'Speaker \d:')
str = speakerRegex.sub('', transcript).replace('\n', ' ')

sentences = nltk.tokenize.sent_tokenize(str)

# references = [word_tokenize(str)]
print(sentences)
references = []

for sent in sentences:
    references.append(word_tokenize(sent))

with open('tmp_summary/default.txt', 'r', encoding='utf-8-sig') as f:
    candidate = word_tokenize(f.read().lower())
    # print(candidate)
 
    # 将文本分成单词
    # reference = [nltk.word_tokenize(' '.join(ref)) for ref in reference]
    score = sentence_bleu(references, candidate)
    print(score)




# tokenize the references
# for sent in references:
#     for i in range(len(sent)):
#         sent[i] = word_tokenize(sent[i])

# namesRegex = re.compile(r'Speaker \d:')
# str = namesRegex.sub('', str)
# print(nltk.tokenize.sent_tokenize(str))

# print(re.split('\n', str))
# reference = [word_tokenize(str)]
# print(reference)
# # read the generated summary
# with open('tmp_summary/default.txt', 'r', encoding='utf-8-sig') as f:
#     candidate = [word_tokenize(f.read())]
#     score = corpus_bleu(reference, candidate)
#     print(score)
