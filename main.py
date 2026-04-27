from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess, requests, tempfile, os, uuid
from typing import List

app = FastAPI()

class VideoRequest(BaseModel):
    video_urls: List[str]
    audio_url: str

@app.post("/merge")
async def merge(req: VideoRequest):
    tmp = tempfile.mkdtemp()
    
    video_files = []
    for i, url in enumerate(req.video_urls):
        path = f"{tmp}/video_{i}.mp4"
        r = requests.get(url, timeout=60)
        open(path, 'wb').write(r.content)
        video_files.append(path)
    
    audio_path = f"{tmp}/audio.mp3"
    r = requests.get(req.audio_url, timeout=60)
    open(audio_path, 'wb').write(r.content)
    
    list_file = f"{tmp}/list.txt"
    with open(list_file, 'w') as f:
        for vf in video_files:
            f.write(f"file '{vf}'\n")
    
    concat_path = f"{tmp}/concat.mp4"
    subprocess.run([
        'ffmpeg', '-f', 'concat', '-safe', '0',
        '-i', list_file, '-c', 'copy', concat_path
    ], check=True)
    
    output_path = f"{tmp}/output.mp4"
    subprocess.run([
        'ffmpeg', '-i', concat_path, '-i', audio_path,
        '-map', '0:v', '-map', '1:a',
        '-c:v', 'copy', '-shortest', output_path
    ], check=True)
    
    from fastapi.responses import FileResponse
    return FileResponse(output_path, media_type='video/mp4',
                       filename='output.mp4')

@app.get("/")
def root():
    return {"status": "ok"}
