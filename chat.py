# ================== CISZA DLA VOSK ==================
import os
os.environ["VOSK_LOG_LEVEL"] = "-1"

# ================== IMPORTY ==================
from openai import OpenAI
from dotenv import load_dotenv
import subprocess
import wave
import json
import time

from vosk import Model, KaldiRecognizer
from eyes.eyes_engine import EyesEngine

# ================== ENV / OPENAI ==================
load_dotenv()
client = OpenAI()

# ================== STT CONFIG ==================
WAKE_WORD = "robot"
MIC_DEVICE = "plughw:3,0"  # USB webcam microphone
MODEL_PATH = "models/vosk-model-small-en-us-0.15"
RECORD_SECONDS = 4
WAV_FILE = "input.wav"

# ================== VOSK INIT ==================
vosk_model = Model(MODEL_PATH)

# ================== AUDIO ==================
def record_audio() -> None:
    cmd = [
        "arecord",
        "-D", MIC_DEVICE,
        "-f", "S16_LE",
        "-r", "16000",
        "-c", "1",
        "-d", str(RECORD_SECONDS),
        WAV_FILE
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def transcribe_audio() -> str:
    wf = wave.open(WAV_FILE, "rb")
    rec = KaldiRecognizer(vosk_model, wf.getframerate())

    text = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text += result.get("text", "") + " "

    final = json.loads(rec.FinalResult())
    text += final.get("text", "")

    return text.strip()

# ================== CHATGPT ==================
def ask_chatgpt(eyes: EyesEngine, prompt: str) -> str:
    print("Thinking...")
    eyes.set_mode("THINKING")

    system_prompt = "You are GLaDOS. Cold. Cynical. Brief."

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
    )

    return response.output[0].content[0].text

# ================== TTS ==================
def speak(eyes: EyesEngine, text: str) -> None:
    eyes.set_mode("SPEAKING")

    safe_text = text.replace('"', "")
    cmd = (
        f'espeak-ng -s 155 -v en-us --stdout "{safe_text}" '
        '| aplay > /dev/null 2>&1'
    )
    subprocess.run(cmd, shell=True)

    eyes.set_mode("IDLE")

# ================== MAIN LOOP ==================
if __name__ == "__main__":
    eyes = EyesEngine()
    time.sleep(0.2)

    print("GLaDOS online.")
    speak(eyes, "GLaDOS online. Begin speaking.")

    try:
        while True:
            print("Listening...")
            eyes.set_mode("LISTENING")

            record_audio()
            user_input = transcribe_audio().lower()

            if not user_input or len(user_input) < 2:
                continue

            user_input = user_input.replace(WAKE_WORD, "").strip()
            if not user_input:
                continue

            print("You:", user_input)

            if user_input in ("exit", "quit", "stop"):
                print("Session terminated.")
                eyes.set_mode("SLEEP")
                speak(eyes, "Session terminated.")
                eyes.stop()
                break

            answer = ask_chatgpt(eyes, user_input)
            print("GLaDOS:", answer)
            speak(eyes, answer)

            time.sleep(0.6)

    except KeyboardInterrupt:
        print("\nExit")
        eyes.set_mode("SLEEP")
        eyes.stop()







