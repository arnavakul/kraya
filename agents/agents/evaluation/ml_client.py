
from typing import Any
import httpx

from schemas.ml_evaluation import (
    FeatureVector,
    EvaluationResponse,
)


class MLEvaluationClient:
    """
    HTTP client for communicating with Kraya's ML Evaluation API.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: float = 30.0,
        app: Any = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.app = app

    def _get_client(self) -> httpx.AsyncClient:
        if self.app is not None:
            return httpx.AsyncClient(
                transport=httpx.ASGITransport(app=self.app),
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return httpx.AsyncClient(timeout=self.timeout)

    async def health_check(self) -> bool:
        """
        Checks whether the ML Evaluation API is reachable.
        """

        try:
            async with self._get_client() as client:

                response = await client.get(
                    f"{self.base_url}/health"
                )

                return response.is_success

        except httpx.RequestError:
            return False

    async def evaluate_supplier(
        self,
        supplier_id: str,
        quote_id: str,
        features: FeatureVector,
    ) -> EvaluationResponse:
        """
        Sends supplier features to FastAPI and retrieves
        the XGBoost score with SHAP explanations.
        """

        endpoint = (
            f"{self.base_url}/evaluations/score-and-explain"
        )

        params = {
            "supplier_id": supplier_id,
            "quote_id": quote_id,
        }

        payload = features.model_dump(mode="json")

        try:
            async with self._get_client() as client:

                response = await client.post(
                    endpoint,
                    params=params,
                    json=payload,
                )

                response.raise_for_status()

                return EvaluationResponse.model_validate(
                    response.json()
                )

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "ML Evaluation API request timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"ML Evaluation API returned HTTP "
                f"{exc.response.status_code}: "
                f"{exc.response.text}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Could not connect to ML Evaluation API: {exc}"
            ) from exc
