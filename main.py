from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess, requests, tempfile, json, os
from typing import List

app = FastAPI()

@app.post("/merge")
async def merge(
    audio: UploadFile = File(...),
    video_urls: str = Form(...)
):
    tmp = tempfile.mkdtemp()
    urls = json.loads(video_urls)
    
    video_files = []
    for i, url in enumerate(urls):
        path = f"{tmp}/video_{i}.mp4"
        r = requests.get(url, timeout=120)
        open(path, 'wb').write(r.content)
        
        # re-encode كل فيديو بنفس الإعدادات
        fixed_path = f"{tmp}/fixed_{i}.mp4"
        subprocess.run([
            'ffmpeg', '-y', '-i', path,
            '-r', '30',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-an',
            fixed_path
        ], check=True)
        video_files.append(fixed_path)
    
    audio_path = f"{tmp}/audio.mp3"
    content = await audio.read()
    open(audio_path, 'wb').write(content)
    
    audio_wav = f"{tmp}/audio.wav"
    subprocess.run([
        'ffmpeg', '-y',
        '-i', audio_path,
        '-ar', '44100',
        '-ac', '2',
        audio_wav
    ], check=True)
    
    list_file = f"{tmp}/list.txt"
    with open(list_file, 'w') as f:
        for vf in video_files:
            f.write(f"file '{vf}'\n")
    
    concat_path = f"{tmp}/concat.mp4"
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', list_file, '-c', 'copy', concat_path
    ], check=True)
    
    output_path = f"{tmp}/output.mp4"
    subprocess.run([
        'ffmpeg', '-y',
        '-i', concat_path,
        '-i', audio_wav,
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        output_path
    ], check=True)
    
    return FileResponse(output_path, media_type='video/mp4', filename='output.mp4')

@app.get("/")
def root():
    return {"status": "ok"}
