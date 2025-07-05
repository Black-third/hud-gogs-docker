# HUD Engineering Take-Home Submission

## Code Description (3-5 sentences)

This project containerizes Gogs (self-hosted Git service) with noVNC browser access and implements complete state extraction capabilities. The solution uses Selenium for browser automation to perform mock admin login, then extracts comprehensive backup data including users, repositories, issues, and actual Git repository contents via direct SQLite database access. The extractor archives Git repositories as base64-encoded tar.gz files within a structured JSON output, providing a complete backup solution. After trying multiple approaches (web scraping, API calls), direct database access proved most reliable since Gogs API tokens are scoped per user and don't provide admin-level access to all data.

## Workflow Description

I developed this on my M2 MacBook using VS Code with GitHub Copilot over approximately 14 hours total. **Step 1 (Docker setup, 3 hours)**: Installing and configuring Gogs, noVNC, and learning Docker containerization from scratch. **Step 2 (Mock login, 3 hours)**: Initially attempted cdotool for mouse automation which failed completely, then successfully implemented Selenium-based browser automation for form submission. **Step 3 (State extraction, 8 hours)**: Started with HTML web scraping approach, then tried API-based extraction with automated token creation, but ultimately settled on direct SQLite database access as the most robust solution. I attempted but wasn't able to finish a reliable restore mechanism due to service restart complexities.

## How to Run

```bash
# Build and run the container
docker build --platform=linux/amd64 -t engineer-submission .
docker run --platform=linux/amd64 -p 6080:6080 -p 3000:3000 --name engineer-submission engineer-submission

# Wait ~60 seconds for services to start, then access:
# - Gogs: http://localhost:3000
# - Browser: http://localhost:6080

# Test assignment requirements:
docker exec engineer-submission python3 /mock_login.py
docker exec engineer-submission /extract_system_state.sh

# Copy backup file to local machine:
docker cp engineer-submission:/complete_backup.json ./complete_backup.json
```

## Deliverables

1. **Docker Image**: Built as `engineer-submission` tag, also available on GitHub repository
2. **GitHub Repository**: [https://github.com/Black-third/hud-gogs-docker] - contains all source code and documentation
3. **Code Description**: See above - Selenium automation + SQLite extraction approach
4. **Workflow Description**: See above - 18 hours on M2 MacBook with VS Code/Copilot
5. **Run Instructions**: See above - simple docker build/run commands

## Assignment Requirements Met

✅ **Core Requirement**: Gogs runs automatically in container  
✅ **Core Requirement**: Browser access via noVNC at localhost:6080  
✅ **Core Requirement**: Mock admin login automation script  
✅ **Bonus Requirement**: Complete state extraction including actual Git repository code  
✅ **Technical Requirements**: Debian-based, no external dependencies during setup, healthcheck included

## Architecture

- **Base**: Debian 12 slim
- **Services**: Gogs, noVNC, Xvfb, Firefox ESR
- **Automation**: Selenium WebDriver for browser interactions
- **Extraction**: Direct SQLite database access + Git repository archival
- **Output**: Structured JSON with base64-encoded repository archives
