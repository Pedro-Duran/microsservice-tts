from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse
from gtts import gTTS
import os
from datetime import datetime
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/audios", StaticFiles(directory="audios_gerados"), name="audios")

@app.post("/gerar-audio/")
async def gerar_audio(texto: str = Form(...)):
    """
    Recebe um texto em mandarim e gera um arquivo MP3 usando TTS (em memória).
    """
    # 1. Converte texto em áudio usando gTTS
    tts = gTTS(text=texto, lang='zh-cn')

    caminho_pasta = "audios_gerados"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"audio_{timestamp}.mp3"
    caminho_completo = os.path.join(caminho_pasta, nome_arquivo)

    tts.save(caminho_completo)

    url_audio = f"/audios/{nome_arquivo}"

    return {
        "mensagem": "Áudio salvo com sucesso!",
        "url": url_audio
    }
