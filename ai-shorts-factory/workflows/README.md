# ComfyUI workflows

1. Open ComfyUI.
2. Build or load Wan2.2/LTX workflow.
3. Set aspect ratio to vertical 9:16.
4. Export workflow API JSON (Save (API Format) from the menu or equivalent).
5. Replace `workflows/wan_t2v_vertical.json` (or the file referenced in `config/default.yaml`).
6. Make sure the prompt node field is named clearly or configure node mapping in `config/models.yaml`:
   - `prompt_node_id` — node id (string) for positive prompt text
   - `negative_prompt_node_id` — optional
   - `width_node_id`, `height_node_id`, `duration_node_id` — optional, depends on your graph

Until node IDs are set and the workflow is valid for your install, the app will fall back to **placeholder video** so the rest of the pipeline still runs.
