from openai.lib import streaming
import requests
from pathlib import Path
import os, sys
from rich import print as rprint
from moviepy.editor import AudioFileClip
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from core.config_utils import load_key
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, conint
import ormsgpack

from fish_audio_sdk.schemas import ReferenceAudio, TTSRequest

def read_ref_text(ref_text):
    path = Path(ref_text)
    if path.exists() and path.is_file():
        with path.open("r", encoding="utf-8") as file:
            return file.read()
    return ref_text

def audio_to_bytes(file_path):
    with open(file_path, "rb") as wav_file:
            wav = wav_file.read()
    return wav

def fish_tts(text,save_path,number,task_df):
    fish_set = load_key("fish_tts")
    url = fish_set['base_url']
    current_dir = Path.cwd()

    ref_audio_path = current_dir.as_posix()+  f"/output/audio/refers/{number}.wav"
    reference_text = task_df.loc[task_df['number'] == number, 'origin'].values[0]

    byte_audio = audio_to_bytes(ref_audio_path)
    ref_text = read_ref_text(reference_text)
    data = {
        "text": text,
        "format": "mp3",
        "mp3_bitrate": 128,
        "normalize": True,
        "references": [
            ReferenceAudio(audio=byte_audio, text=ref_text)
        ],
    }
    pydantic_data = TTSRequest(**data)
    max_retries = 2
    for attempt in range(max_retries):
        response = requests.post(
            url,
            data=ormsgpack.packb(pydantic_data, option=ormsgpack.OPT_SERIALIZE_PYDANTIC),
            stream=True,
            headers={
                "authorization": f"Bearer {fish_set['api_key']}",
                "content-type": "application/msgpack",
            },
        )
        print("resonse: ",response)
        if response.status_code == 200:
            wav_file_path = Path(save_path).with_suffix('.wav')
            wav_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save the MP3 content to a temporary file
            temp_mp3_path = wav_file_path.with_suffix('.mp3')
            with open(temp_mp3_path, 'wb') as temp_file:
                temp_file.write(response.content)

            # Convert mp3 to wav using moviepy
            audio_clip = AudioFileClip(str(temp_mp3_path))
            audio_clip.write_audiofile(str(wav_file_path))
            audio_clip.close()

            # Remove the temporary MP3 file
            os.remove(temp_mp3_path)

            rprint(f"[bold green]Converted audio saved to {wav_file_path}[/bold green]")
            break
        else:
            rprint(f"[bold red]Request failed, status code: {response.status_code}, retry attempt: {attempt + 1}/{max_retries}[/bold red]")
            if attempt == max_retries - 1:
                rprint("[bold red]Max retry attempts reached, operation failed.[/bold red]")

if __name__ == '__main__':
    fish_tts("今天是个好日子！", "fish_tts.wav")
