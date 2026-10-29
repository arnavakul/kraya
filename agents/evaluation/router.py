from fastapi import APIRouter, HTTPException, status
from pydantic_models.evaluation_schemas import FeatureVector, EvaluationResponse
from evaluation.shap_engine import ShapEvaluationEngine

router = APIRouter(prefix="/evaluations", tags=["Evaluation Agent"])

# Initialize engine instance
try:
    eval_engine = ShapEvaluationEngine()
except Exception as e:
    eval_engine = None

@router.post("/score-and-explain", response_model=EvaluationResponse, status_code=status.HTTP_200_OK)
async def score_and_explain(
    supplier_id: str,
    quote_id: str,
    features: FeatureVector
):
    """
    Evaluates quote risk, scores quality (0-100), and calculates SHAP drivers for complete transparency.
    """
    if eval_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML Evaluation model is not loaded. Ensure evaluation_xgb_v1.bin exists."
        )
    
    try:
        response = eval_engine.evaluate_and_explain(
            supplier_id=supplier_id,
            quote_id=quote_id,
            feature_vector=features
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )