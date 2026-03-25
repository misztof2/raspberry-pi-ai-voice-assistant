import json
import subprocess
from vosk import Model, KaldiRecognizer
import wave
import os

MODEL_PATH = "models/vosk-model-small-en-us-0.15"
WAV_FILE = "input.wav"

def record_audio():
    # nagrywa 4 sekundy z kamerki USB (card 3)
    cmd = [
        "arecord",
        "-D", "plughw:3,0",
        "-f", "S16_LE",
        "-r", "16000",
        "-c", "1",
        "-d", "4",
        WAV_FILE
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def transcribe():
    wf = wave.open(WAV_FILE, "rb")
    rec = KaldiRecognizer(Model(MODEL_PATH), wf.getframerate())

    result_text = ""

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            result_text += result.get("text", "") + " "

    final = json.loads(rec.FinalResult())
    result_text += final.get("text", "")

    return result_text.strip()

if __name__ == "__main__":
    print("🎤 Recording...")
    record_audio()
    print("🧠 Transcribing...")
    text = transcribe()
    print("TEXT:", text)
