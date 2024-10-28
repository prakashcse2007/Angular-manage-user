from fastapi import FastAPI, Depends, HTTPException
from schemas import ClaimRequest, ClaimResponse
from services import process_claim

app = FastAPI()

@app.post("/claims", response_model=ClaimResponse)
def handle_claim(claim_data: ClaimRequest):
    try:
        return process_claim(claim_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))