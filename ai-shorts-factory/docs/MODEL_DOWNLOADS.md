# Model downloads (ComfyUI)

## Principles

- Model files are **large** (multi‑GB). They must **not** live in Git.
- Store weights under `/workspace/ComfyUI/models/...` on the Vast instance (or your local ComfyUI tree).
- The app repository only ships **code**, small workflow JSON placeholders, and a **manifest template**.

## Recommended ComfyUI folders

```text
/workspace/ComfyUI/models/diffusion_models
/workspace/ComfyUI/models/text_encoders
/workspace/ComfyUI/models/vae
/workspace/ComfyUI/models/checkpoints
/workspace/ComfyUI/models/loras
```

## Automatic downloads (optional)

1. Edit `config/model_manifest.yaml`.
2. Set `enabled: true` only for entries you trust.
3. Fill `url` with an **official** or license‑compliant direct download.
4. Optionally set `sha256` for integrity verification.
5. On the server: `DOWNLOAD_MODELS=true bash scripts/setup_vast.sh`  
   or run `bash scripts/download_models.sh`.

If `url` is empty, the downloader **skips** the entry and prints a message — the whole setup must **not** fail because of empty URLs.

## Hugging Face and licenses

- If a model requires a Hugging Face token, set it in the environment (e.g. `HF_TOKEN`) before running downloads — wire your own policy; do not commit tokens.
- If a license requires explicit acceptance, accept it on the provider’s site before mirroring weights.

## Disk sizing

Plan for **200 GB+** if you will keep multiple video checkpoints and encoders on the same volume.
