from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess, requests, tempfile, os
from typing import List

app = FastAPI()

class VideoRequest(BaseModel):
    video_urls: List[str]
    audio_url: str

def download_file(url, path):
    session = requests.Session()
    r = session.get(url, stream=True, timeout=120)
    if 'drive.google.com' in url:
        for key, value in r.cookies.items():
            if 'download_warning' in key:
                r = session.get(url + '&confirm=' + value, stream=True, timeout=120)
    with open(path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

@app.post("/merge")
async def merge(req: VideoRequest):
    tmp = tempfile.mkdtemp()
    video_files = []
    for i, url in enumerate(req.video_urls):
        path = f"{tmp}/video_{i}.mp4"
        download_file(url, path)
        video_files.append(path)

    audio_path = f"{tmp}/audio.mp3"
    download_file(req.audio_url, audio_path)

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
        'ffmpeg', '-i', concat_path,
        '-i', audio_path,
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        '-y', output_path
    ], check=True)

    return FileResponse(output_path, media_type='video/mp4', filename='output.mp4')

@app.get("/")
def root():
    return {"status": "ok"}
