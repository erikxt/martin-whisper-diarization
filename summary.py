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



origin_text = '''
尊敬的先生/女士，

我叫张子立，我写这封信是为了表达对最近在西班牙签证申请过程中遇到的不满。

我最近在贵领事馆指定的武汉签证中心申请了西班牙签证，我的参考编号是 WUH11310230014。然而，在申请过程中，我发现签证中心存在乱收费的现象，这让我感到非常不满。我希望能够引起贵馆的关注，以解决这个问题。

首先，就快递费用而言，武汉签证中心告知每人的快递收费标准为60元，包括从武汉签证中心到北京领馆、领馆办理完成后寄回武汉签证中心以及签证中心到申请人指定地址的3笔快递费用。然而，根据bls官网首页发布的信息，签证中心和领事馆之间的往返快递费用应当包含在118元的签证服务费用里面了。因此，我认为这前2笔快递费用涉及重复收费的问题，需要领事馆予以调查和确认。另外，我家离签证中心很近，我根本不需要快递服务。由于签证中心强调60元中包含3笔快递费用，所以我被迫缴纳，无法选择自行领取。因此，我想知道签证中心所告知的武汉签证中心到北京领馆、领馆办理完成后寄回武汉签证中心这2笔快递服务费用是否需要申请人在60元快递费用中单独支付？如果这确实是需要我们支付的费用，那么为何在官方网站上公示的60元快递费用是可选的？并且公告通知“在所有的西班牙签证申请中心领取护照全部免费。”

其次，对于照片服务费用，我按照要求准备了2张符合要求的白底照片，并且签证中心工作人员审核并认可了我的照片，给我胶水要将照片粘贴在签证申请表上了。然而，在付款的时候，签证中心仍然要求我支付35元的照片费用。工作人员称这是因为生物监测中“活体照片”的要求。我当场向工作人员提出了质疑，询问是否既然一定要交35元，是否原本就不需要自行准备照片的？他们回答说不需要。既然不需要自行准备照片，那为何工作人员还收下了我自行付费打印出来的两张白底照片并将它用于申请表呢？这增加了我的签证开销，并且与官网公布的照片可选服务的信息相矛盾。我想指出的是，我是通过新上线的签证服务系统预约的签证服务，在预约网站上我已经上传了照片并进行了人脸识别，并且录入指纹和活体照片等生物检测费用应当包含在118元服务费里面的，工作人员声称的35元照片费用是“活体检测”是否涉及欺骗？

我理解武汉签证中心是第三方外包的服务商，其乱收费行为不代表 bls 和领事馆的要求。因此我进行询问和投诉。我希望得到合理的、透明的签证申请费用和服务。我相信这也是您所希望看到的结果。因此，我希望您能够采取措施，确保签证中心的收费公正透明，退还快递费用和照相费用（我不需要快递服务，我要求到武汉签证中心自行领取护照）。

感谢您抽出宝贵的时间阅读我的信件。我相信您会采取适当的措施处理这个问题。如果您需要进一步的信息，请随时与我联系。

此致

敬礼
'''

response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "帮我翻译如下文本"
            },
            {
                "role": "user",
                "content": origin_text
            }
        ]
    )
translate = response['choices'][0]['message']['content']
print(translate)