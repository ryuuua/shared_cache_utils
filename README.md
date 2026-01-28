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
export CEBRA_EMBEDDING_CACHE_LAYOUT=flat  # or hierarchical
```

## Example filename format

```
{dataset}__{model}__seed{N}.npz
{dataset}__{model}__shuffle.npz
{dataset}__{model}.npz
```

## Cache layout

The cache layout is controlled via `CEBRA_EMBEDDING_CACHE_LAYOUT`:

- `flat` (default): all files live directly under the base cache directory.
- `hierarchical`: files are organized as:
  `{base_dir}/{embedding_family}/{model_name}/{filename}`

Where:
- `embedding_family` = `"lm"` for `hf_transformer` or `sentence_transformer`,
  otherwise `embedding.type` (or `"unknown"` if unset).
- `model_name` = `embedding.model_name` if present, else `embedding.name`.
- `filename` keeps the same format as the flat layout.

### Example directory structures

Flat layout (default):

```
embedding_cache/
  imagenet__sentence-transformers__all-MiniLM-L6-v2.npz
  imagenet__sentence-transformers__all-MiniLM-L6-v2__seed42.npz
```

Hierarchical layout:

```
embedding_cache/
  lm/
    sentence-transformers/all-MiniLM-L6-v2/
      imagenet__sentence-transformers__all-MiniLM-L6-v2.npz
      imagenet__sentence-transformers__all-MiniLM-L6-v2__seed42.npz
  clip/
    ViT-B-32/
      imagenet__ViT-B-32.npz
```
