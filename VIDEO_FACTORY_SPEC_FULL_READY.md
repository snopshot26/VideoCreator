# AI Shorts Factory — Full Cursor Build Specification

## 0. Goal

Build a self-hosted AI video generation system for a rented GPU server.

The final system must allow me to open a web UI on the server, enter a short idea/prompt, choose style/settings, and generate a ready-to-upload vertical video for TikTok, YouTube Shorts, Instagram Reels, etc.

Target output:

- Format: vertical 9:16
- Resolution: preferably 1080x1920 final export
- Duration: 8–30 seconds
- Output file: `.mp4`
- Includes:
  - generated video
  - generated voiceover or dialogue
  - optional background music
  - subtitles/captions
  - final FFmpeg export
  - logs
  - saved prompt/script metadata

The system should be modular. If one model fails, the rest of the pipeline should still work.

---

## 1. Important Principle

Do not try to build one giant AI model.

Build a pipeline:

```text
User prompt
→ script generation
→ scene planning
→ voice/dialogue generation
→ video generation through ComfyUI/Wan/LTX workflow
→ optional lip-sync
→ background music/SFX
→ subtitles
→ final FFmpeg render
→ exported MP4
```

---

## 2. Main Use Case

I want to create social media videos quickly.

Example user input:

```text
Create a 15-second funny vertical video where Trump is a taxi driver arguing with a passenger about oil prices. Make it cinematic, realistic, with dialogue, subtitles, and background city sounds.
```

The system should create:

```text
outputs/
  2026-xx-xx_trump_taxi_driver/
    script.json
    prompt.txt
    voice.wav
    music.wav
    raw_video.mp4
    subtitles.srt
    final.mp4
    metadata.json
    logs.txt
```

---

## 3. Tech Stack

Use Python.

Required tools:

- Python 3.10+
- FastAPI for backend API
- Gradio or simple HTML frontend for web UI
- FFmpeg for final video assembly
- MoviePy only if needed, but prefer FFmpeg subprocess calls
- Pydantic for config validation
- Loguru or Python logging for logs
- SQLite or JSONL for generation history
- ComfyUI API integration for video generation
- Optional local LLM or external LLM for script generation
- TTS model integration
- Optional music generation
- Optional lip-sync module

---

## 4. Project Name

Use this project name:

```text
ai-shorts-factory
```

---

## 5. Repository Structure

Create this exact structure:

```text
ai-shorts-factory/
  README.md
  .env.example
  requirements.txt
  config/
    default.yaml
    models.yaml
  app/
    main.py
    webui.py
    api.py
    config.py
    logger.py
  pipeline/
    orchestrator.py
    script_generator.py
    prompt_builder.py
    video_generator.py
    comfy_client.py
    tts_generator.py
    music_generator.py
    subtitles.py
    renderer.py
    thumbnail.py
    publish_packager.py
    metadata.py
    safety.py
  platforms/
    youtube_uploader.py
    tiktok_uploader.py
    instagram_uploader.py
    README.md
  workflows/
    wan_t2v_vertical.json
    wan_i2v_vertical.json
    ltx_video_audio.json
    README.md
  scripts/
    install_server.sh
    install_comfyui.sh
    start_app.sh
    start_comfyui.sh
    test_ffmpeg.sh
    check_gpu.py
  outputs/
    .gitkeep
  logs/
    .gitkeep
  docs/
    SERVER_SETUP.md
    USAGE.md
    TROUBLESHOOTING.md
    MODEL_SETUP.md
```

---

## 6. Modes

The app must support these modes:

### Mode A — Full Local Mode

Everything runs locally on rented GPU server:

- script generation can use local LLM or simple template
- video generation through ComfyUI
- TTS local
- music local or placeholder
- final render local

### Mode B — Hybrid Mode

Video generation local, but script/voice/music can use external APIs if user adds API keys.

### Mode C — Manual Workflow Mode

If automatic video generation fails, the app still prepares:

- script
- video prompt
- voiceover
- subtitles
- FFmpeg command
- folder structure

This is important. The project should not crash just because ComfyUI is not configured yet.

---

## 7. Configuration

Create `config/default.yaml`.

It should include:

```yaml
server:
  host: "0.0.0.0"
  port: 7860

paths:
  outputs_dir: "outputs"
  logs_dir: "logs"
  workflows_dir: "workflows"

video:
  default_duration_seconds: 15
  default_aspect_ratio: "9:16"
  final_width: 1080
  final_height: 1920
  fps: 24

comfyui:
  enabled: true
  url: "http://127.0.0.1:8188"
  default_workflow: "workflows/wan_t2v_vertical.json"
  timeout_seconds: 3600

script:
  provider: "template"
  language: "en"
  style: "shorts"

tts:
  provider: "placeholder"
  voice: "default"
  speed: 1.0

music:
  enabled: true
  provider: "placeholder"
  volume: 0.15

subtitles:
  enabled: true
  font_size: 64
  position: "bottom"

render:
  codec: "libx264"
  crf: 18
  preset: "medium"
  audio_bitrate: "192k"

safety:
  add_ai_disclaimer_metadata: true
  block_illegal_content: true
```

---

## 8. Environment Variables

Create `.env.example`:

```env
# Optional external LLM
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Optional TTS APIs
ELEVENLABS_API_KEY=

# Optional video APIs if used later
RUNWAY_API_KEY=
KLING_API_KEY=
LUMA_API_KEY=

# ComfyUI
COMFYUI_URL=http://127.0.0.1:8188
```

Do not hardcode any API keys.

---

## 9. Web UI Requirements

Create a web UI with Gradio or simple FastAPI HTML.

Fields:

1. Main idea / prompt textarea
2. Video duration selector:
   - 8 sec
   - 15 sec
   - 30 sec
3. Style selector:
   - realistic cinematic
   - funny meme
   - documentary
   - dramatic
   - podcast clip
   - fake commercial
4. Language selector:
   - English
   - Russian
   - Turkish
5. Voice mode:
   - narrator
   - dialogue
   - no voice
6. Music:
   - none
   - light background
   - dramatic
   - funny
   - city ambience
7. Generate button
8. Progress display
9. Final download link
10. Show generated script
11. Show generated video prompt
12. Show logs

The app should run with:

```bash
python app/webui.py
```

or:

```bash
bash scripts/start_app.sh
```

---

## 10. API Endpoints

Create FastAPI endpoints:

```text
GET  /health
POST /generate
GET  /jobs/{job_id}
GET  /outputs/{job_id}/final
GET  /outputs/{job_id}/metadata
```

Example POST body:

```json
{
  "idea": "A funny vertical video about Trump as a taxi driver arguing about oil prices",
  "duration_seconds": 15,
  "style": "realistic cinematic",
  "language": "en",
  "voice_mode": "dialogue",
  "music": "city ambience"
}
```

Example response:

```json
{
  "job_id": "2026-05-11_153000_trump_taxi",
  "status": "started",
  "output_dir": "outputs/2026-05-11_153000_trump_taxi"
}
```

---

## 11. Pipeline Logic

Implement `pipeline/orchestrator.py`.

The orchestrator should run these steps:

```text
1. Validate user input
2. Create output folder
3. Generate script
4. Build video prompt
5. Generate voice/dialogue audio
6. Generate or select background music
7. Generate raw video using ComfyUI
8. Generate subtitles
9. Render final MP4 with FFmpeg
10. Save metadata
11. Return final video path
```

Every step must be logged.

If a step fails:

- write error to `logs.txt`
- save partial outputs
- continue if possible
- show useful error in UI

---

## 12. Script Generator

Create `pipeline/script_generator.py`.

It should output JSON like this:

```json
{
  "title": "Trump Taxi Driver",
  "duration_seconds": 15,
  "language": "en",
  "characters": [
    {
      "name": "Taxi Driver",
      "description": "A fictional orange-haired political parody character, not a real endorsement"
    },
    {
      "name": "Passenger",
      "description": "Confused passenger"
    }
  ],
  "dialogue": [
    {
      "speaker": "Taxi Driver",
      "text": "Gas prices? I drive the best taxi. Tremendous mileage."
    },
    {
      "speaker": "Passenger",
      "text": "Sir, we have been parked for ten minutes."
    }
  ],
  "visual_scenes": [
    {
      "scene": 1,
      "duration": 5,
      "description": "Vertical cinematic shot inside a yellow taxi at night, neon city lights outside."
    },
    {
      "scene": 2,
      "duration": 5,
      "description": "Passenger looks confused while the driver gestures dramatically."
    },
    {
      "scene": 3,
      "duration": 5,
      "description": "Taxi meter spins comically fast, dramatic zoom, meme ending."
    }
  ],
  "voiceover_text": "Taxi Driver: Gas prices? I drive the best taxi. Tremendous mileage. Passenger: Sir, we have been parked for ten minutes.",
  "caption_text": "When your taxi driver starts explaining global oil prices..."
}
```

Important:

- Keep scripts short.
- Make them suitable for 8–30 second videos.
- For dialogue, keep each line short.
- Avoid copyrighted song lyrics.
- Avoid explicit instructions to impersonate a real person's actual voice.
- If user asks for real politician/public figure, generate parody text but do not clone their voice.

---

## 13. Prompt Builder

Create `pipeline/prompt_builder.py`.

It should convert script JSON into video generation prompts.

For each scene, build a prompt like:

```text
Vertical 9:16 cinematic realistic video, inside a yellow taxi at night, neon city lights, expressive fictional political parody taxi driver, confused passenger in the back seat, dramatic hand gestures, shallow depth of field, high detail, social media short, 15 seconds, smooth camera motion.
```

Also create a negative prompt:

```text
blurry, low quality, distorted face, extra fingers, unreadable text, watermark, logo, broken anatomy, duplicated people, flickering, bad lighting
```

The prompt builder should save:

```text
prompt.txt
negative_prompt.txt
scene_prompts.json
```

---

## 14. Video Generation

Create `pipeline/video_generator.py`.

It should support multiple backends:

```python
class VideoBackend:
    COMFYUI = "comfyui"
    PLACEHOLDER = "placeholder"
```

If ComfyUI is enabled:

- send workflow JSON to ComfyUI API
- inject prompt into workflow
- wait for result
- download/copy generated video into output folder as `raw_video.mp4`

If ComfyUI is not available:

- create a placeholder video with FFmpeg:
  - black background
  - text overlay: "Video generation placeholder"
  - duration equal to selected duration
  - resolution 1080x1920

This allows the rest of the app to work even before models are configured.

---

## 15. ComfyUI Client

Create `pipeline/comfy_client.py`.

Implement:

```python
class ComfyUIClient:
    def __init__(self, base_url: str):
        ...

    def health_check(self) -> bool:
        ...

    def queue_prompt(self, workflow: dict) -> str:
        ...

    def wait_for_completion(self, prompt_id: str, timeout_seconds: int) -> dict:
        ...

    def download_outputs(self, result: dict, output_dir: str) -> list[str]:
        ...
```

Use ComfyUI HTTP API.

The code must be defensive:

- handle connection refused
- handle timeout
- handle missing output
- log full errors
- return useful error messages

---

## 16. Workflow Files

Create placeholder workflow files:

```text
workflows/wan_t2v_vertical.json
workflows/wan_i2v_vertical.json
workflows/ltx_video_audio.json
```

Since exact ComfyUI workflow node IDs depend on installed custom nodes and downloaded models, create valid placeholder JSON and document that the user must replace them with real exported ComfyUI workflows.

In `workflows/README.md`, explain:

```text
1. Open ComfyUI.
2. Build or load Wan2.2/LTX workflow.
3. Set aspect ratio to vertical 9:16.
4. Export workflow API JSON.
5. Replace workflows/wan_t2v_vertical.json.
6. Make sure the prompt node field is named clearly or configure node mapping in config/models.yaml.
```

Also create `config/models.yaml`:

```yaml
video_backend: "comfyui"

workflows:
  wan_t2v:
    file: "workflows/wan_t2v_vertical.json"
    prompt_node_id: null
    negative_prompt_node_id: null
    width_node_id: null
    height_node_id: null
    duration_node_id: null

  wan_i2v:
    file: "workflows/wan_i2v_vertical.json"
    prompt_node_id: null
    negative_prompt_node_id: null

  ltx_video_audio:
    file: "workflows/ltx_video_audio.json"
    prompt_node_id: null
```

The code should detect if node IDs are null and show a clear setup error.

---

## 17. TTS Generation

Create `pipeline/tts_generator.py`.

Support providers:

```text
placeholder
kokoro
external_api
```

For MVP:

- implement `placeholder` TTS by creating silent audio with FFmpeg
- optionally use `pyttsx3` if easy
- design interface so Kokoro/CosyVoice can be added later

Interface:

```python
class TTSGenerator:
    def generate(self, text: str, output_path: str, voice: str = "default") -> str:
        ...
```

Requirements:

- output WAV file
- match approximate duration
- if no TTS is configured, create silent audio so rendering still works
- save dialogue text to `voiceover.txt`

Important safety:

- Do not implement real-person voice cloning by default.
- Do not clone political figures' voices.
- If user requests public figure parody, use a generic narrator or fictional voice.

---

## 18. Music Generator

Create `pipeline/music_generator.py`.

Support providers:

```text
placeholder
local_audio_folder
stable_audio_later
```

For MVP:

- if music is enabled, generate quiet synthetic background tone or use silent audio
- allow user to place files in:

```text
assets/music/
```

If local files exist, randomly select one matching style.

Music should be mixed at low volume, default 0.15.

---

## 19. Subtitles

Create `pipeline/subtitles.py`.

Generate `.srt` subtitles from dialogue or voiceover text.

For MVP, split text into short chunks and distribute them across duration.

Example:

```srt
1
00:00:00,000 --> 00:00:03,000
Gas prices? I drive the best taxi.

2
00:00:03,000 --> 00:00:06,000
Tremendous mileage.

3
00:00:06,000 --> 00:00:09,000
Sir, we have been parked for ten minutes.
```

Also create optional burned-in captions through FFmpeg.

---

## 20. Renderer

Create `pipeline/renderer.py`.

Use FFmpeg to create final video.

Input:

- `raw_video.mp4`
- `voice.wav`
- `music.wav`
- `subtitles.srt`

Output:

- `final.mp4`

Requirements:

- final resolution 1080x1920
- H.264 MP4
- AAC audio
- combine voice and music
- burn subtitles if enabled
- normalize audio lightly
- ensure TikTok/Shorts compatible output

Example FFmpeg logic:

```bash
ffmpeg \
  -i raw_video.mp4 \
  -i voice.wav \
  -i music.wav \
  -filter_complex "[1:a]volume=1.0[a1];[2:a]volume=0.15[a2];[a1][a2]amix=inputs=2:duration=longest[aout]" \
  -map 0:v \
  -map "[aout]" \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,subtitles=subtitles.srt" \
  -c:v libx264 \
  -crf 18 \
  -preset medium \
  -c:a aac \
  -b:a 192k \
  -shortest \
  final.mp4
```

The actual Python code should build this command safely.

---

## 21. Metadata

Create `pipeline/metadata.py`.

Save `metadata.json`:

```json
{
  "job_id": "string",
  "created_at": "ISO datetime",
  "input": {
    "idea": "string",
    "duration_seconds": 15,
    "style": "realistic cinematic",
    "language": "en",
    "voice_mode": "dialogue",
    "music": "city ambience"
  },
  "models": {
    "video_backend": "comfyui",
    "tts_provider": "placeholder",
    "music_provider": "placeholder"
  },
  "outputs": {
    "script": "script.json",
    "prompt": "prompt.txt",
    "voice": "voice.wav",
    "music": "music.wav",
    "raw_video": "raw_video.mp4",
    "subtitles": "subtitles.srt",
    "final": "final.mp4"
  },
  "ai_generated": true
}
```

---

## 22. Safety Module

Create `pipeline/safety.py`.

Basic rules:

- block requests for illegal content
- block sexual content involving minors
- block instructions for violence, fraud, malware, etc.
- warn if user generates realistic public figure content
- do not clone real voices by default
- add metadata that the output is AI-generated

For public figure parody:

Allow fictional parody, but avoid:

- fake confession
- fake endorsement
- fake emergency announcement
- fake election instruction
- direct voice cloning

---

## 23. Logging

Every generation should write:

```text
outputs/{job_id}/logs.txt
logs/app.log
```

Log:

- input prompt
- config used
- each pipeline step start/end
- errors
- FFmpeg commands
- ComfyUI job id
- output file paths

Use readable logs.

---

## 24. Installation Scripts

Create `scripts/install_server.sh`.

It should:

```bash
#!/usr/bin/env bash
set -e

sudo apt update
sudo apt install -y python3 python3-venv python3-pip git ffmpeg curl wget

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "Installation complete."
echo "Run: bash scripts/start_app.sh"
```

Create `scripts/check_gpu.py`:

```python
import subprocess

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True)
    except Exception as e:
        return str(e)

print("NVIDIA SMI:")
print(run("nvidia-smi"))

print("Python:")
print(run("python --version"))

print("FFmpeg:")
print(run("ffmpeg -version | head -n 3"))
```

Create `scripts/start_app.sh`:

```bash
#!/usr/bin/env bash
set -e
source .venv/bin/activate
python app/webui.py
```

Create `scripts/start_comfyui.sh`:

```bash
#!/usr/bin/env bash
set -e
cd ComfyUI
source venv/bin/activate || source .venv/bin/activate || true
python main.py --listen 0.0.0.0 --port 8188
```

---

## 25. ComfyUI Setup Documentation

Create `docs/MODEL_SETUP.md`.

Explain:

```text
Recommended first setup:

1. Rent RTX 4090 24GB or better.
2. Install NVIDIA driver.
3. Install ComfyUI.
4. Start ComfyUI on port 8188.
5. Install required custom nodes for Wan2.2 or LTX workflow.
6. Download model weights manually according to the official model repository.
7. Test generation inside ComfyUI first.
8. Export API workflow JSON.
9. Put workflow JSON into workflows/wan_t2v_vertical.json.
10. Configure node IDs in config/models.yaml.
11. Restart AI Shorts Factory.
12. Generate test video.
```

Important:

Do not automatically download huge model weights unless explicitly configured. Instead, print clear instructions.

---

## 26. README Requirements

Create a strong `README.md`.

It must include:

- what the project does
- what it does not do yet
- installation
- server setup
- how to run
- how to connect ComfyUI
- how to generate first placeholder video
- how to generate real AI video after workflow setup
- troubleshooting
- example prompts

Example prompts:

```text
A 15-second vertical realistic cinematic video of a fictional politician-style taxi driver arguing with a passenger about oil prices, neon city at night, funny dialogue, subtitles, meme ending.
```

```text
A 12-second TikTok-style fake commercial for an energy drink for programmers, fast cuts, dramatic voiceover, glowing laptop, cyberpunk office, bold captions.
```

```text
A 20-second documentary-style short about why people procrastinate, cinematic b-roll, narrator voice, subtitles, calm background music.
```

---

## 27. Requirements.txt

Create a reasonable `requirements.txt`:

```txt
fastapi
uvicorn
gradio
pydantic
pyyaml
python-dotenv
requests
loguru
moviepy
Pillow
numpy
```

Only add heavy libraries if necessary.

Do not add PyTorch unless the project directly needs it outside ComfyUI.

---

## 28. Placeholder Video Requirement

Before real ComfyUI works, the app must still generate a test video.

For placeholder mode:

- create 1080x1920 black or gradient video
- overlay title
- overlay generated script lines
- add silent or placeholder audio
- export final MP4

This is required so I can test the full app without waiting for model setup.

---

## 29. Error Handling

The app must never fail silently.

Common errors and messages:

### ComfyUI not running

Show:

```text
ComfyUI is not reachable at http://127.0.0.1:8188.
Start it with: bash scripts/start_comfyui.sh
Or switch video backend to placeholder in config/default.yaml.
```

### Workflow missing

Show:

```text
Workflow file not found. Add your exported ComfyUI API workflow to workflows/wan_t2v_vertical.json.
```

### Node ID missing

Show:

```text
Prompt node ID is not configured. Open config/models.yaml and set prompt_node_id for your workflow.
```

### FFmpeg missing

Show:

```text
FFmpeg is not installed. Run: sudo apt install ffmpeg
```

---

## 30. Generation History

Create simple generation history.

Use:

```text
outputs/history.jsonl
```

Each line:

```json
{"job_id":"...","created_at":"...","idea":"...","final_path":"...","status":"success"}
```

The web UI should show recent generations.

---

## 31. Final Output Naming

Use safe filenames.

Example:

```text
outputs/2026-05-11_153000_trump_taxi_driver/final.mp4
```

Also create a copy:

```text
outputs/latest/final.mp4
```

---

## 32. Testing

Create basic tests or at least a test script.

Create:

```text
scripts/test_placeholder_generation.sh
```

It should run one full generation in placeholder mode.

Example:

```bash
curl -X POST http://127.0.0.1:7860/generate \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "A 15-second fake commercial for a programmer energy drink",
    "duration_seconds": 15,
    "style": "funny meme",
    "language": "en",
    "voice_mode": "narrator",
    "music": "light background"
  }'
```

---

## 33. Acceptance Criteria

The project is finished when:

1. `bash scripts/install_server.sh` works on Ubuntu.
2. `bash scripts/start_app.sh` starts the web UI.
3. User can enter a prompt and generate a placeholder final MP4.
4. Output folder contains:
   - script.json
   - prompt.txt
   - voice.wav or silent audio
   - music.wav or silent audio
   - subtitles.srt
   - raw_video.mp4
   - final.mp4
   - metadata.json
   - logs.txt
5. App can connect to ComfyUI if available.
6. App gives clear error if ComfyUI is not configured.
7. README explains how to replace placeholder workflow with real Wan/LTX workflow.
8. Final video is vertical 9:16.
9. Final MP4 is playable.
10. Logs are clear.

---

## 34. Development Order

Build in this exact order:

### Step 1

Create project structure, config loader, logging.

### Step 2

Create placeholder pipeline that generates final MP4 without AI models.

### Step 3

Create web UI.

### Step 4

Create FastAPI endpoints.

### Step 5

Create script generator and prompt builder.

### Step 6

Create subtitles generator.

### Step 7

Create FFmpeg renderer.

### Step 8

Create ComfyUI client.

### Step 9

Add workflow injection logic.

### Step 10

Improve README and docs.

Do not start with ComfyUI complexity. First make full placeholder pipeline work end-to-end.

---

## 35. Coding Style

Use clean, modular Python.

Rules:

- typed functions where possible
- no giant files
- clear class names
- clear error messages
- comments only where useful
- no hardcoded absolute paths
- use pathlib
- avoid global mutable state
- save every intermediate artifact

---

## 36. Final Message After Building

When implementation is complete, print:

```text
AI Shorts Factory is ready.

Run:

bash scripts/install_server.sh
bash scripts/start_app.sh

Then open:

http://SERVER_IP:7860

First test placeholder mode.
After that configure ComfyUI workflow in workflows/ and config/models.yaml.
```

---

## 37. Extra Feature If There Is Time

Add a batch mode.

Input file:

```text
batch_prompts.txt
```

Each line is one video idea.

Command:

```bash
python app/main.py --batch batch_prompts.txt
```

It should generate multiple output folders.

---

## 38. Production-Ready Requirement

This project must not stay as a placeholder-only MVP.

The final target is:

```text
User opens the web UI
→ writes one prompt
→ clicks Generate
→ receives a ready-to-publish vertical MP4
→ uploads it manually or through an official platform/API workflow if configured
```

The system must generate a complete publishing package for every video.

Each completed job must include:

```text
outputs/{job_id}/
  final.mp4
  title.txt
  description.txt
  hashtags.txt
  captions.srt
  captions_burned_in.mp4
  thumbnail.png
  publish_package.json
  metadata.json
  logs.txt
```

The generated video must be usable immediately for:

- TikTok
- YouTube Shorts
- Instagram Reels

The final video should include:

- vertical 9:16 video
- voiceover or dialogue
- background music or ambience
- burned-in subtitles
- title/caption idea
- hashtags
- thumbnail frame
- AI-generated disclosure metadata
- all source prompts and generation settings saved

---

## 39. Full Auto-Generation Requirement

The user should not need to manually write a script, subtitle file, title, description, or hashtags.

The user only provides:

```text
Main idea / prompt
```

The app must automatically generate:

1. Short script
2. Dialogue or narrator voiceover
3. Scene plan
4. Video generation prompt
5. Negative prompt
6. Voice audio
7. Background music/ambience
8. Subtitles
9. Final video
10. Thumbnail
11. Title
12. Description
13. Hashtags
14. Publish-ready package

Example input:

```text
Make a 15-second funny realistic vertical video where a fictional politician-style taxi driver argues with a passenger about oil prices.
```

Expected generated outputs:

```text
final.mp4
title.txt
description.txt
hashtags.txt
thumbnail.png
publish_package.json
```

---

## 40. Publish Package

Create `pipeline/publish_packager.py`.

It should generate:

### `title.txt`

A short viral title.

Example:

```text
When Your Taxi Driver Starts Explaining Oil Prices
```

### `description.txt`

A ready-to-copy description.

Example:

```text
A fictional AI-generated comedy short about a dramatic taxi ride and oil prices. Made for entertainment/parody.
```

### `hashtags.txt`

Example:

```text
#shorts #tiktok #reels #aivideo #parody #comedy #taxi #oilprices
```

### `publish_package.json`

Example:

```json
{
  "title": "When Your Taxi Driver Starts Explaining Oil Prices",
  "description": "A fictional AI-generated comedy short about a dramatic taxi ride and oil prices. Made for entertainment/parody.",
  "hashtags": ["shorts", "tiktok", "reels", "aivideo", "parody", "comedy"],
  "platforms": {
    "youtube_shorts": {
      "recommended_title": "When Your Taxi Driver Starts Explaining Oil Prices",
      "recommended_description": "AI-generated parody comedy short. #shorts #aivideo #parody",
      "status": "ready_for_manual_upload"
    },
    "tiktok": {
      "recommended_caption": "When the taxi driver starts explaining oil prices 😂 #aivideo #parody #comedy",
      "status": "ready_for_manual_upload"
    },
    "instagram_reels": {
      "recommended_caption": "AI-generated parody comedy short. #reels #aivideo #comedy",
      "status": "ready_for_manual_upload"
    }
  },
  "ai_generated": true,
  "requires_manual_platform_review": true
}
```

---

## 41. Optional Official Upload Integrations

Do not implement scraping-based upload bots.

However, design the project so that future official upload integrations can be added safely.

Create:

```text
platforms/
  youtube_uploader.py
  tiktok_uploader.py
  instagram_uploader.py
  README.md
```

For the first full version:

- generate the publishing package
- show upload instructions
- do not depend on platform APIs
- do not require paid APIs
- do not scrape websites
- do not automate login with browser hacks

Optional future mode:

```yaml
platform_upload:
  enabled: false
  provider: "manual"
```

Allowed future providers:

```text
manual
youtube_official_api
tiktok_official_api
instagram_official_api
```

If upload is not configured, the UI must show:

```text
Your video is ready. Download final.mp4 and upload it manually.
```

---

## 42. Real Model Setup Must Be Included

The project should include real model setup documentation and optional install scripts.

It must support this staged behavior:

### Stage 1 — Placeholder Mode

Works immediately after install.

### Stage 2 — Local Generation Mode

Works after the user installs ComfyUI and model workflows.

### Stage 3 — Production Mode

Generates complete publish-ready videos with:

- real generated video
- generated voice
- generated/subselected music
- subtitles
- thumbnail
- metadata
- publish package

The app should clearly show which stage is active.

---

## 43. Local TTS Requirement

Do not leave TTS as placeholder only.

Implement at least one practical local TTS backend.

Preferred order:

1. Kokoro TTS if feasible
2. Piper TTS if Kokoro is too complex
3. pyttsx3 fallback
4. silent placeholder only as emergency fallback

The TTS module must support:

- narrator mode
- dialogue mode
- separate speaker labels in the script
- one final mixed voice audio file
- saving the generated text to `voiceover.txt`

Do not implement real-person voice cloning by default.

For public figure parody, use generic fictional voices.

---

## 44. Music and Ambience Requirement

Do not depend on copyrighted music.

Implement:

1. local generated tone/ambience fallback
2. local `assets/music/` folder support
3. optional open-source music/SFX backend if configured later

The app must be able to produce a final video even if no music model is installed.

The music should be low volume by default and mixed under the voice.

---

## 45. Thumbnail Requirement

Create `pipeline/thumbnail.py`.

Generate a thumbnail from the final video.

Required behavior:

- extract a frame around 40–60% of the video duration
- save as `thumbnail.png`
- optionally add title text overlay
- resolution should be vertical or square-friendly
- keep original clean frame as `thumbnail_clean.png`

---

## 46. Batch Mode Requirement

Batch mode is required, not optional.

Input:

```text
batch_prompts.txt
```

Each line is one video idea.

Command:

```bash
python app/main.py --batch batch_prompts.txt
```

The system should generate one full publish package per line.

Output:

```text
outputs/batch_{timestamp}/
  job_001/
  job_002/
  job_003/
  batch_summary.csv
  batch_summary.json
```

---

## 47. Final Web UI Must Be Practical

The UI must show:

- video preview
- download final video button
- download publish package button
- generated title
- generated description
- hashtags
- thumbnail preview
- logs
- stage/status: Placeholder / Local ComfyUI / Production
- ComfyUI connection status
- GPU status if available

---

## 48. Do Not Implement These Unsafe/Unstable Features

Do not implement payment systems.

Do not scrape TikTok, YouTube, Instagram, or other platforms.

Do not automate account login with browser hacks.

Do not download copyrighted music.

Do not implement real-person voice cloning.

Do not make the core project depend on paid APIs.

Do not create fake official statements, fake emergency announcements, fake endorsements, or fake election instructions using public figures.

Instead:

- generate ready-to-upload MP4 files
- generate titles/descriptions/hashtags
- generate thumbnails
- use manual upload by default
- allow only official API upload integrations later
- keep the core system local-first and stable

---

## 49. Updated Acceptance Criteria

The project is finished only when:

1. `bash scripts/install_server.sh` works on Ubuntu.
2. `bash scripts/start_app.sh` starts the web UI.
3. User enters one prompt and receives a completed output folder.
4. Placeholder mode creates a real playable vertical MP4.
5. Production mode can connect to ComfyUI workflow when configured.
6. Final output includes:
   - final.mp4
   - captions_burned_in.mp4 or final.mp4 with burned subtitles
   - voice.wav
   - music.wav or ambience.wav
   - subtitles.srt
   - thumbnail.png
   - title.txt
   - description.txt
   - hashtags.txt
   - publish_package.json
   - metadata.json
   - logs.txt
7. Web UI displays video preview and download links.
8. Batch mode works.
9. Errors are clear and logged.
10. The README explains exactly how to go from server setup to first publish-ready video.

---

# End of Specification
