import openai
import os

openai.api_key = os.environ.get("OPENAI_API_KEY")


def gen_summary(file_name):
    # open the srt file
    srt_path = os.join("tmp_srt", file_name + ".srt")
    with open(srt_path, "r") as f:
        srt = f.read()
        response = openai.Completion.create(
            engine="davinci",
            prompt=srt,
            temperature=0.9,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n"]
        )
    
openai.api_key = os.environ.get("OPENAI_API_KEY")
print(openai.api_key)   
# print(openai.Model.list())   
# print(openai.Engine.list())

file_name = "default"
audio_file = open(os.path.join("tmp_audio", file_name + ".wav"), "rb")
response = openai.Audio.transcribe(file=audio_file, model="whisper-1")
print(response)