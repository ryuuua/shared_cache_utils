import os
from pathlib import Path

from omegaconf import OmegaConf

__all__ = [
    "resolve_embedding_cache_dir",
    "build_embedding_cache_filename",
    "get_embedding_cache_path",
]


def resolve_embedding_cache_dir(cfg, *, env_var: str = "CEBRA_EMBEDDING_CACHE_DIR") -> Path:
    """Resolve the shared embedding cache directory, honoring env override."""
    env_dir = os.getenv(env_var)
    base_dir = env_dir or OmegaConf.select(
        cfg, "paths.embedding_cache_dir", default="embedding_cache"
    )
    return Path(base_dir).expanduser()


def build_embedding_cache_filename(cfg) -> str:
    """Build a stable cache filename from dataset + embedding model identifiers."""
    dataset_name = cfg.dataset.name
    model_name = getattr(cfg.embedding, "model_name", None) or cfg.embedding.name
    safe_model_name = model_name.replace("/", "__")

    filename = f"{dataset_name}__{safe_model_name}"
    if getattr(cfg.dataset, "shuffle", False):
        seed = getattr(cfg.dataset, "shuffle_seed", None)
        if seed is not None:
            filename += f"__seed{seed}"
        else:
            filename += "__shuffle"

    return f"{filename}.npz"


def get_embedding_cache_path(cfg) -> Path:
    """Generate a unique path for a cached text embedding file."""
    return resolve_embedding_cache_dir(cfg) / build_embedding_cache_filename(cfg)
