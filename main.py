from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import boto3, os
from datetime import datetime
from gtts import gTTS
from uuid import uuid4
import tempfile  
from dotenv import load_dotenv
from fastapi import Body
from typing import Dict
import json
from fastapi import Request
# Carrega variáveis de ambiente do .env
load_dotenv()

app = FastAPI()

# Inicializa o cliente S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

BUCKET_NAME = "audios-mandarim"  # Definido diretamente como seu bucket

class TextoRequest(BaseModel):
    texto: str

@app.post("/gerar-audio")
async def gerar_audio(payload: TextoRequest):
    try:
        texto = payload.texto
        print("Texto recebido:", texto)

        if not texto.strip():
            raise HTTPException(status_code=400, detail="Texto não pode ser vazio.")

        # Gera nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"audio_{timestamp}_{uuid4().hex[:8]}.mp3"

        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts = gTTS(text=texto, lang='zh-cn')
            tts.save(temp_file.name)
            caminho_local = temp_file.name

        # Faz upload para S3
        s3.upload_file(
            Filename=caminho_local,
            Bucket=BUCKET_NAME,
            Key=nome_arquivo,
            ExtraArgs={ "ContentType": "audio/mpeg"}
        )

        # Remove o arquivo local temporário
        os.remove(caminho_local)

        # Gera URL pública
        url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{nome_arquivo}"

        return {
            "mensagem": "Áudio gerado e enviado com sucesso!",
            "caminhoAudio": url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar áudio: {str(e)}")