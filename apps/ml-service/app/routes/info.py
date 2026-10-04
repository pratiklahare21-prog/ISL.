from pathlib import Path

from fastapi import APIRouter

from app.core.labels import ALL_SIGN_LABELS, STATIC_SIGNS, DYNAMIC_SIGNS
from app.core.inference import ModelRegistry, DEFAULT_CHECKPOINT

router = APIRouter()


@router.get("/health")
def health():
    model_loaded = ModelRegistry.get_model() is not None
    return {
        "status": "ok",
        "modelLoaded": model_loaded,
        "checkpointPath": str(DEFAULT_CHECKPOINT),
        "checkpointExists": Path(DEFAULT_CHECKPOINT).exists(),
    }


@router.get("/labels")
def labels():
    return {
        "all": ALL_SIGN_LABELS,
        "static": sorted(STATIC_SIGNS),
        "dynamic": sorted(DYNAMIC_SIGNS),
        "count": len(ALL_SIGN_LABELS),
    }
