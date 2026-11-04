from fastapi import FastAPI
import uvicorn

# Import your evaluation router (adjust path if needed)
from evaluation.router import router as evaluation_router

app = FastAPI(
    title="Kraya — AI Agent Microservice",
    description="Python AI/ML microservice for quote parsing, XGBoost risk evaluation, and SHAP feature attributions.",
    version="1.0.0"
)

# Register the Evaluation Agent router
app.include_router(evaluation_router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "UP", "service": "kraya-agents"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)