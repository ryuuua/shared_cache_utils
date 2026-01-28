# emca

Shared utility package for building deterministic embedding cache paths
across multiple projects (Hydra/OmegaConf-friendly).

## Install (local)

```bash
pip install -e ./shared_cache_utils
```

## Usage (Hydra/OmegaConf AppConfig)

```python
from emca import get_embedding_cache_path

path = get_embedding_cache_path(cfg)
print(path)
```

Expected config fields (minimal):
- `cfg.dataset.name`
- `cfg.embedding.name`
- `cfg.embedding.model_name` (optional; falls back to `embedding.name`)
- `cfg.dataset.shuffle` (optional)
- `cfg.dataset.shuffle_seed` (optional)
- `cfg.paths.embedding_cache_dir` (optional)

Environment override:

```bash
export CEBRA_EMBEDDING_CACHE_DIR=/path/to/shared/embedding_cache
```

## Example filename format

```
{dataset}__{model}__seed{N}.npz
{dataset}__{model}__shuffle.npz
{dataset}__{model}.npz
```
