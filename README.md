# Gogs Docker Container

Containerized Gogs (self-hosted Git) with browser access and complete state extraction.

## Quick Start

```bash
# Build and run
docker build --platform=linux/amd64 -t engineer-submission .
docker run --platform=linux/amd64 -p 6080:6080 -p 3000:3000 --name engineer-submission engineer-submission

# Access after ~30 seconds:
# http://localhost:3000 - Gogs web interface
# http://localhost:6080 - Browser via noVNC
```

## Assignment Features

```bash
# Mock admin login (browser automation)
docker exec engineer-submission python3 /mock_login.py

# Complete state extraction (users, repos, code)
docker exec engineer-submission /extract_system_state.sh

# Optional: Create API token (runs automatically after login)
docker exec engineer-submission python3 /create_token.py
```

## What It Does

✅ **Core**: Gogs starts automatically in container  
✅ **Core**: Browser access via noVNC  
✅ **Core**: Mock admin login automation  
✅ **Bonus**: Complete backup extraction including actual Git code

## How It Works

The extractor reads SQLite directly (API tokens are per-user limited), archives Git repos as tar.gz, and outputs everything as base64-encoded JSON.

## Key Files

- `mock_login.py` - Browser automation for admin login
- `extract_system_state.sh` - Main extraction script  
- `extract_complete_backup.py` - Extraction engine
- `create_token.py` - API token creation (optional, works after login but extraction doesn't need it)

## Getting the Backup File

After extraction, copy the JSON file to your project folder to read it in VS Code:

```bash
# Copy backup file to current directory
docker cp engineer-submission:/complete_backup.json ./complete_backup.json

# Now you can open it in VS Code to see all the extracted data
```

The JSON contains users, repositories, issues, and base64-encoded Git repository archives.

## Development Journey

Built this on M2 MacBook with Docker, GitHub Copilot, and VS Code over ~18 hours total.

**Docker Setup (5 hours)**: Installing Gogs, noVNC, learning Docker containerization from scratch.

**Mock Login (5 hours)**: First tried cdotool for mouse movements and coordinates in the container - that failed miserably! Then switched to HTML web scraping with Selenium, which actually worked :)

**State Extraction (8 hours)**: This was the real challenge. Tried multiple approaches:

1. **Web scraping**: Visited pages like `/admin/users` after login to scrape HTML content. It worked but was messy - had to parse HTML and extract each piece of info for users, repos, issues, etc.

2. **API approach**: Built a mock login system to create API tokens automatically as admin, then used API commands. Problem was the API only returned data for the current user, not all users. Some endpoints didn't work at all.

3. **Direct database**: Finally went with SQLite database extraction - turned out to be the cleanest approach! Direct access to all data without API limitations.

**Restore attempts**: Tried to write code for uploading and restoring state but couldn't get it reliable. Service restarts were flaky. Need to learn more about that.

Lots of details and challenges (No math tho... honestly, the biggest betrayal 😔), but glad I finished! Thanks god :)
