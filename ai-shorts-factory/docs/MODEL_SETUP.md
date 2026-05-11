# Model setup (ComfyUI / Wan / LTX)

Recommended first setup:

1. Rent RTX 4090 24GB or better.
2. Install NVIDIA driver.
3. Install ComfyUI (`bash scripts/install_comfyui.sh` or follow upstream docs).
4. Start ComfyUI on port 8188 (`bash scripts/start_comfyui.sh`).
5. Install required custom nodes for Wan2.2 or LTX workflow.
6. Download model weights manually according to the official model repository.
7. Test generation inside ComfyUI first.
8. Export API workflow JSON.
9. Put workflow JSON into `workflows/wan_t2v_vertical.json`.
10. Configure node IDs in `config/models.yaml` (`prompt_node_id`, etc.).
11. Restart AI Shorts Factory.
12. Generate a test video.

Important: do not automatically download huge model weights unless you explicitly choose to. Prefer manual downloads with checksum verification.
