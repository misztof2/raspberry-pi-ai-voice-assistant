import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer

DEVICE_INDEX = 3  # WEBCAM mic (card 3)

model = Model("models/vosk-model-small-en-us-0.15")
rec = KaldiRecognizer(model, 16000)

q = queue.Queue()

def callback(indata, frames, time, status):
    q.put(bytes(indata))

with sd.RawInputStream(
    samplerate=16000,
    blocksize=8000,
    dtype='int16',
    channels=1,
    device=DEVICE_INDEX,
    callback=callback
):
    print("🎤 Speak now (Ctrl+C to stop)")
    while True:
        data = q.get()
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "")
            if text:
                print("TEXT:", text)
