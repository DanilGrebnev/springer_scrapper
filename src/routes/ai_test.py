from fastapi import APIRouter, HTTPException
from src.agent.openai import OpenAIClient

router = APIRouter(prefix="/api", tags=["ai-test"])


@router.get("/ai-test")
def ai_test():
    client = OpenAIClient()
    try:
        client.create_agent()
        response = client.test_connection()
        return {"status": "ok", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()
