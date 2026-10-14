"""POST /ai/ask  (optional bonus)."""
import httpx
from fastapi import APIRouter, Depends, HTTPException

from . import ai_service
from .database import get_conn
from .schemas import AIAnswer, AIQuestion

router = APIRouter(prefix="/ai", tags=["AI (optional, Ollama)"])


@router.post("/ask", response_model=AIAnswer)
def ask(body: AIQuestion, conn=Depends(get_conn)):
    facts, rows = ai_service.retrieve(conn, body.question)
    prompt = ai_service.build_prompt(body.question, facts, rows)
    try:
        answer = ai_service.ask_ollama(prompt)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it (ollama serve) and pull the model: "
            f"ollama pull {ai_service.OLLAMA_MODEL()}",
        )
    except (httpx.HTTPError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"Ollama error: {exc}")
    return AIAnswer(
        question=body.question,
        answer=answer,
        model=ai_service.OLLAMA_MODEL(),
        records_used=len(rows),
        facts=facts,
    )
