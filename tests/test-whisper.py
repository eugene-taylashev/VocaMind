import whisper

WHISPER_MODEL="turbo"

model = whisper.load_model(WHISPER_MODEL)
result = model.transcribe("./21.mp3", task='transcribe', language='es', fp16=False)
print(result["text"])
