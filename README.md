# LLM Ranking Data Repo

This repository is a pure data source for leaderboard JSON files used by another frontend project.

## Files kept in this repo

- `data/leaderboard-text.json`
- `data/leaderboard-text-style-control.json`
- `data/leaderboard-vision.json`
- `data/leaderboard-vision-style-control.json`
- `data/leaderboard-image.json`
- `update_leaderboard_data.py`

## Manual update

Windows PowerShell:

```powershell
python .\update_leaderboard_data.py
```

The script scrapes latest `arena.ai` leaderboard pages and rewrites files in `data/`.

## Auto update

GitHub Actions workflow:

- `.github/workflows/update-data.yml`

It runs on schedule and on manual trigger, updates `data/*.json`, then commits and pushes changes automatically.

## JSON URL (GitHub Pages)

After enabling GitHub Pages for this repo, JSON files can be accessed as:

- `https://<your-user>.github.io/<repo-name>/data/leaderboard-text.json`
- `https://<your-user>.github.io/<repo-name>/data/leaderboard-text-style-control.json`
- `https://<your-user>.github.io/<repo-name>/data/leaderboard-vision.json`
- `https://<your-user>.github.io/<repo-name>/data/leaderboard-vision-style-control.json`
- `https://<your-user>.github.io/<repo-name>/data/leaderboard-image.json`
