# Platform upload modules

This project **does not** ship scraping bots or unofficial upload automation.

The default flow is:

1. Generate `final.mp4`, `publish_package.json`, `title.txt`, `description.txt`, `hashtags.txt`.
2. Upload manually in TikTok / YouTube Shorts / Instagram Reels.

Future optional providers (behind config flags) may include:

- `youtube_official_api`
- `tiktok_official_api`
- `instagram_official_api`

Until then, keep `platform_upload.provider` set to `manual` in `config/default.yaml`.
