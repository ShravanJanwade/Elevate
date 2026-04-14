"""
Elevate v3 – Model Manager
==============================
Smart model lifecycle management for 2GB GPU constraint.

Loads models on-demand, releases VRAM when switching between
heavy models (bi-encoder, cross-encoder, impact classifier, judge).

Automatically uses fine-tuned models when available,
falls back to base pretrained models otherwise.
"""

import gc
import os
from typing import Optional

import torch


class ModelManager:
    """
    Singleton model manager for GPU-constrained inference.
    
    Ensures that no more than ~800MB of VRAM is used at once
    by loading and releasing models as needed.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
            cls._instance._device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
            cls._instance._backend_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        return cls._instance

    @property
    def device(self):
        return self._device

    # ----- Public API -----

    def get_bi_encoder(self):
        """Get the (optionally fine-tuned) bi-encoder."""
        return self._load("bi_encoder", self._loader_bi_encoder)

    def get_cross_encoder(self):
        """Get the (optionally fine-tuned) cross-encoder."""
        return self._load("cross_encoder", self._loader_cross_encoder)

    def get_impact_classifier(self):
        """Get the impact classifier (releases encoders first)."""
        return self._load("impact_classifier", self._loader_impact_classifier)

    def get_judge(self):
        """Get the T5 judge model (releases other models first)."""
        self._release("impact_classifier")
        return self._load("judge", self._loader_judge)

    def release_all(self):
        """Release all loaded models."""
        for name in list(self._cache.keys()):
            self._release(name)

    # ----- Internal -----

    def _load(self, name: str, loader_fn):
        if name not in self._cache:
            self._cache[name] = loader_fn()
        return self._cache[name]

    def _release(self, name: str):
        if name in self._cache:
            del self._cache[name]
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def _model_path(self, subdir: str) -> Optional[str]:
        """Check if a fine-tuned model directory exists."""
        path = os.path.join(self._backend_dir, "models", subdir)
        if os.path.exists(path) and any(
            f.endswith((".bin", ".safetensors", ".json"))
            for f in os.listdir(path)
        ):
            return path
        return None

    # ----- Loaders -----

    def _loader_bi_encoder(self):
        from sentence_transformers import SentenceTransformer

        custom = self._model_path("elevate-bi-encoder-v1")
        if custom:
            return SentenceTransformer(custom)
        return SentenceTransformer("all-MiniLM-L6-v2")

    def _loader_cross_encoder(self):
        from sentence_transformers import CrossEncoder

        custom = self._model_path("elevate-cross-encoder-v1")
        if custom:
            return CrossEncoder(custom)
        return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def _loader_impact_classifier(self):
        from models.recruiter.impact_classifier import ImpactClassifier

        custom = self._model_path("impact-classifier-v1")
        return ImpactClassifier(model_path=custom)

    def _loader_judge(self):
        from models.recruiter.judge_model import JudgeModel

        custom = self._model_path("elevate-judge-v1")
        return JudgeModel(model_path=custom)


# Convenience function
def get_model_manager() -> ModelManager:
    """Get the global ModelManager singleton."""
    return ModelManager()
# caching added
