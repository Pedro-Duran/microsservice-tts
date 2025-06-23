from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import os
from datetime import datetime
from gtts import gTTS
from uuid import uuid4
import tempfile
from dotenv import load_dotenv
import logging
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente do .env
load_dotenv()

app = FastAPI()

# Configuração do cliente S3 com verificação de variáveis de ambiente
def get_s3_client():
    
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )

s3 = get_s3_client()
BUCKET_NAME = "audios-mandarim"

class AudioRequest(BaseModel):
    texto: str

 

@app.post("/gerar-audio", response_class=JSONResponse)
async def gerar_audio(payload: AudioRequest):
    try:
        # Validação adicional do texto
        texto = payload.texto.strip()
        if not texto:
            raise HTTPException(
                status_code=400,
                detail="O texto não pode ser vazio ou conter apenas espaços em branco."
            )
        
        logger.info(f"Processando texto: {texto[:50]}...")  # Log parcial do texto

        # Gera nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        nome_arquivo = f"audio_{timestamp}_{uuid4().hex[:8]}.mp3"

        # Geração do áudio com tratamento de erros específico
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                tts = gTTS(text=texto, lang='zh-cn')
                tts.save(temp_file.name)
                caminho_local = temp_file.name
        except Exception as tts_error:
            raise HTTPException(
                status_code=500,
                detail=f"Falha na geração do áudio: {str(tts_error)}"
            )

        # Upload para S3 com tratamento de erros
        try:
            s3.upload_file(
                Filename=caminho_local,
                Bucket=BUCKET_NAME,
                Key=nome_arquivo,
                ExtraArgs={"ContentType": "audio/mpeg"}
            )
        except Exception as s3_error:
            os.remove(caminho_local)  # Limpeza do arquivo temporário
            raise HTTPException(
                status_code=500,
                detail=f"Falha no upload para S3: {str(s3_error)}"
            )
        finally:
            if os.path.exists(caminho_local):
                os.remove(caminho_local)

        # Gera URL pública
        url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{nome_arquivo}"

        return {
            "mensagem": "Áudio gerado e enviado com sucesso!",
            "caminhoAudio": url
        }

    except HTTPException:
        raise  # Re-lança exceções HTTP já tratadas
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocorreu um erro interno ao processar sua requisição"
        )