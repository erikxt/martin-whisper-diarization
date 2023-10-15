from metrics import get_bleu_score, get_candidate, get_references, get_rouge_score, get_meteor_score, remove_speaker_tag
import hashlib
import json
import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, UploadFile
import uuid
import ffmpy
import moviepy.editor as mp
import subprocess
from fastapi.middleware.cors import CORSMiddleware
import openai
# from martian import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

# define a video upload http interface using fastapi
app = FastAPI()
origins = [
    "http://localhost:3000",
    "http://172.21.225.137:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.mount("/video", StaticFiles(directory="tmp_video"), name="video")
app.mount("/thumbnail", StaticFiles(directory="tmp_thumbnail"), name="thumbnail")
CHUNK_SIZE = 1024*1024


@app.get("/")
def read_root():
    return {"Hello": "World"}

# Accept-Range: bytes


@app.get("/video/{file_name}", description="Get the video file")
async def get_video(file_name: str, req: Request):
    print(req.headers.get("Range"))
    video_path = os.path.join("tmp_video", file_name)
    # check if the video file exists, if not, return 404
    if not os.path.exists(video_path):
        # return http status code 404
        raise HTTPException(status_code=404, detail="Item not found")
    # return the video file stream
    return FileResponse(video_path, media_type="video/mp4", headers={"Accept-Ranges": "bytes"})


@app.get("/srt/{file_name}", description="Get the srt file of the video")
async def get_srt(file_name: str):
    srt_path = os.path.join("tmp_audio", file_name + ".srt")
    # check if the srt file exists, if not, return 404
    if not os.path.exists(srt_path):
        # return http status code 404
        raise HTTPException(status_code=404, detail="Item not found")
    # return the srt file content and convert it to json format
    with open(srt_path, "r", encoding='utf-8-sig') as f:
        srt = f.read()
        # split the srt file content by line
        srt = srt.split("\n")
        # remove the last empty line
        srt = srt[:-1]
        # convert the srt file content to json format
        # split the str[i+1] into start and end, which split by "-->"
        # extract the speaker from the text from the str[i+2] because the speaker is in the text
        # use iterator to iterate the srt list and generate a list of json objects
        # return the list
        srt_json = []
        for i in range(0, len(srt), 4):
            id = srt[i]
            start, end = srt[i+1].split("-->")
            speaker = srt[i+2].split(":")[0]
            text = srt[i+2].split(":")[1]
            srt_json.append({"id": id, "start": start,
                            "end": end, "speaker": speaker, "text": text})
        return srt_json
    
    
@app.get("/nlg/{file_name}", description="summary, metrics action items, potential questions")
async def get_nlp_data(file_name, platform="gpt-4"):
    transcript = get_transcript(file_name)
    transcript = remove_speaker_tag(transcript)
    summary = get_summary_content(file_name, transcript=transcript, platform=platform)
    
    # print(summary)
    references =  get_references(transcript)
    candidate = get_candidate(summary)
    bleu_score = get_bleu_score(references, candidate)
    
    rouge_score = get_rouge_score(transcript, summary)
    meteor_score = get_meteor_score(references, candidate)
    return {"summary": summary, "bleu": bleu_score, "rouge": rouge_score, "meteor": meteor_score}


@app.get("/summary/{file_name}", description="Get the srt file of the video")
async def get_srt(file_name: str):
    summary_path = os.path.join("tmp_summary", file_name + ".txt")
    # check if the srt file exists, if not, return 404
    if not os.path.exists(summary_path):
        # return http status code 404
        raise HTTPException(status_code=404, detail="Item not found")
    # return the srt file content and convert it to json format
    with open(summary_path, "r", encoding='utf-8-sig') as f:
        summary = f.read()
        return {"summary": summary}


@app.post("/uploadfile", description="Upload a video file and generate a thumbnail and audio")
async def create_upload_file(file: UploadFile):
    # generate a random name for the uploaded video
    file_name = str(uuid.uuid4())
    print(file_name)

    video_path = os.path.join("tmp_video", file_name + ".mp4")
    print(video_path)
    # save the video file on the server
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())

    # get the md5 hash of the video
    with open(video_path, 'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        hash = md5obj.hexdigest()
        file_name = hash

    # rename the video file with the md5 hash
    new_video_path = os.path.join("tmp_video", file_name + ".mp4")
    if not os.path.exists(new_video_path):
        os.rename(video_path, new_video_path)
    else:
        os.remove(video_path)
    video_path = new_video_path

    # get thumbnail from the video asynchronously
    get_thumbnail(video_path, file_name)
    # extract audio from the video
    await extract_audio_and_generate_srt(video_path, file_name)
    # return the path of the uploaded video and the thumbnail and audio
    print(file_name)
    return {"fileName": file_name}


# download the video file from url and save it on the server and extract audio from the video
async def download_video_and_extract_audio(url):
    # generate a random name for the uploaded video
    file_name = str(uuid.uuid4())
    # download the video file from url and save it on the server
    video_path = download_video(url, file_name)
    # extract audio from the video
    await extract_audio_and_generate_srt(video_path, file_name)
    # return the path of the uploaded video and the thumbnail and audio
    return {"video_path": video_path, "file_name": file_name}

# download the video file from url and save it on the server


def download_video(url, random_name):
    video_path = os.path.join("tmp_video", random_name + ".mp4")
    # download the video file from url and save it on the server
    ff = ffmpy.FFmpeg(
        inputs={url: None},
        outputs={video_path: None}
    )
    ff.run()
    return video_path


# get the thumbnail from the video asynchronously
def get_thumbnail(video_path, file_name):
    thumbnail_path = os.path.join("tmp_thumbnail", file_name + ".png")
    # check if the thumbnail exists, if not, generate the thumbnail
    if os.path.exists(thumbnail_path):
        return thumbnail_path
    # generate the thumbnail
    ff = ffmpy.FFmpeg(
        inputs={video_path: None},
        outputs={thumbnail_path: ['-ss', '00:00:00.000', '-vframes', '1']}
    )
    ff.run()
    return thumbnail_path

# create a video extractor method using ffmpeg and moviepy which can extract audio file from video


async def extract_audio_and_generate_srt(video_path, file_name):
    audio_path = os.path.join("tmp_audio", file_name + ".wav")
    # check if the audio file exists, if not, generate the audio file
    if os.path.exists(audio_path):
        return
    clip = mp.VideoFileClip(video_path)
    clip.audio.write_audiofile(
        audio_path, codec='pcm_s16le', ffmpeg_params=['-ac', '1'])
    # long time cost
    print("start transcribing")
    # transcribe_to_srt(audio_path)
    subprocess.Popen(["python3", "diarize.py", "-a", audio_path, "--no-stem"])


@app.get("/nlg/summary/{file_name}", description="Get the summary of the transcript")
async def get_summary(file_name, platform="gpt-4"):
    return get_summary_content(file_name, platform=platform)


def get_summary_content(file_name, transcript, platform="gpt-4"):
    summary_path = os.path.join(
        'tmp_summary', file_name + '_' + platform + '.txt')
    # check if the summary file exists, if not, generate the summary file
    if not os.path.exists(summary_path):
        if transcript == "" or transcript is None:
            transcript = get_transcript(file_name)
            transcript = remove_speaker_tag(transcript)
        # generate the summary file
        summary = abstract_summary_extraction(file_name, transcript, platform)
        # write the summary into the file
    else:
        # read the summary from the file
        with open(summary_path, 'r', encoding="utf-8-sig") as f:
            summary = f.read()
    # return the summary
    return summary


def abstract_summary_extraction(file_name, transcript, platform):
    messages = [
        {
            "role": "system",
                    "content": "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following text and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points."
        },
        {
            "role": "user",
                    "content": transcript
        }
    ]
    if platform == "gpt-4":
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
    else:
        response = openai.ChatCompletion.create(
            messages=messages
        )

    summary = response['choices'][0]['message']['content']
    # write summary into the file
    summary_path = os.path.join('tmp_summary', file_name + '_' + platform + '.txt')
    with open(summary_path, 'w') as f:
        f.write(summary)
    return summary

# like get_summary function, but return the action items


def get_action_items(file_name, transcript, platform="gpt-4"):
    action_item_path = os.path.join('tmp_action_item', 
                                    file_name + '_' + platform + '.txt')
    # check if the action item file exists, if not, generate the action item file
    if not os.path.exists(action_item_path):
        # generate the action item file
        action_items = action_item_extraction(file_name, transcript)
        # write the action items into the file
    else:
        # read the action items from the file
        with open(action_item_path, 'r', encoding="utf-8-sig") as f:
            action_items = f.read()
    # return the action items in json format
    # trans action_items to json format
    return {"action_items": json.loads(action_items)}


def get_transcript(file_name):
    srt_path = os.path.join("tmp_audio", file_name + ".srt")
    with open(srt_path, "r", encoding="utf-8-sig") as f:
        transcript = f.read()
        return transcript


def action_item_extraction(file_name, transcript):
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
                "content": transcript
            }
        ]
    )
    action_items = response['choices'][0]['message']['content']
    action_item_path = os.path.join('tmp_action_item', file_name + '.txt')
    with open(action_item_path, 'w') as f:
        f.write(action_items)
    return action_items

# like abstract_summary_extraction function, ask gpt-4 to extract some questions about the transcript


def potential_question_extraction(file_name, transcript):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are an AI expert in analyzing conversations and extracting action items. \
                    Please review the text and ask some possible questions abhout the text. \
                    These could be questions around the text and catch the main points. \
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


if __name__ == "__main__":
    uvicorn.run(app="main:app", port=8000, reload=True)
