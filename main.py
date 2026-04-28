from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import subprocess, requests, tempfile, json
from typing import List

app = FastAPI()

@app.post("/merge")
async def merge(
    audio: UploadFile = File(...),
    video_urls: str = Form(...)
):
    tmp = tempfile.mkdtemp()
    urls = json.loads(video_urls)[:6]
    
    video_files = []
    for i, url in enumerate(urls):
        path = f"{tmp}/video_{i}.mp4"
        r = requests.get(url, timeout=60, stream=True)
        with open(path, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        video_files.append(path)
    
    audio_path = f"{tmp}/audio.mp3"
    open(audio_path, 'wb').write(await audio.read())
    
    list_file = f"{tmp}/list.txt"
    with open(list_file, 'w') as f:
        for vf in video_files:
            f.write(f"file '{vf}'\n")
    
    output_path = f"{tmp}/output.mp4"
    
    # دمج مباشر بدون loop
    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0', '-i', list_file,
        '-i', audio_path,
        '-map', '0:v:0', '-map', '1:a:0',
        '-vf', 'scale=1280:720',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
        '-c:a', 'aac', '-b:a', '128k',
        '-shortest',
        output_path
    ], check=True, timeout=300)
    
    return FileResponse(output_path, media_type='video/mp4', filename='output.mp4')

@app.get("/")
def root():
    return {"status": "ok"}
