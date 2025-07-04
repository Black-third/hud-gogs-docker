# HUD Research Engineering Take-Home: Gogs Docker Container

## Overview (From Me, Honestly)

This take-home was a deep dive into Docker, automation, and web scraping using Gogs (a lightweight GitHub alternative). The goal was to build a Docker image that spins up Gogs and a browser-accessible desktop UI via noVNC, auto-configures everything internally, and enables extracting Gogs system state — with no external networking or Docker volumes.

I got the main parts working: the Docker container starts Gogs and noVNC, launches Firefox, creates an admin user, and extracts system state using a combination of browser automation and scraping. I even automated the creation of an API token — but unfortunately, I couldn't make effective use of it.

---

## Platform & Workflow

* **Machine:** M2 MacBook Air
* **Environment:** Windsurf IDE with GitHub Copilot MCP integration
* **Base OS:** Debian bookworm-slim (ARM64 compatible)
* **Total Time:** \~10–15 hours

### My Timeline

* **Step 1 (Base setup + Gogs + noVNC):** 3 hours
* **Step 2 (Automation: browser + admin login):** 2 hours
* **Step 3 (Extraction via scraping + limited API):** 3–5 hours
* **Bonus (Tried restoration via upload + API auth attempts):** \~2–5 hours (eventually removed this part)

---

## Project Breakdown

### ✅ What Works

* Gogs runs inside the container with no volume or external network dependencies
* noVNC provides access to a remote desktop at `http://localhost:6080`
* Firefox browser auto-launches
* `mock_install.py` sets up Gogs automatically (successfully automated full installation)
* `mock_login.py` logs in and generates an API token for the admin user (confirmed creation and saved the token)
* `extract_state.py` scrapes HTML from Gogs admin pages and uses limited API endpoints to extract users, repos, and issues as JSON

### ❌ What Didn’t Work / Was Removed

* I wrote an initial `upload_state.py` as a trial for round-trip restoration, but it never worked as intended. I eventually removed it to focus on the core requirements.
* Gogs API admin endpoints (like `/api/v1`) returned 404s — I couldn’t get them to work and suspect I didn’t fully understand the token-based auth flow.
* Git repo content restoration was not attempted
* Initial automation using `xdotool` and coordinate-based clicking was completely unreliable

---

## Files & Scripts

```
├── Dockerfile              # Defines full build process (multi-platform)
├── start.sh                # Launches Gogs + noVNC
├── mock_install.py         # Automates Gogs setup via Selenium
├── mock_login.py           # Logs in and generates API token
├── extract_state.py        # Extracts users/repos/issues as JSON
├── gogs/                   # Gogs binary (0.13.3)
├── novnc/                  # noVNC web client
└── README.md               # This honest description
```

---

## How to Build & Run

### On M1/M2/M3 Mac (ARM64):

```bash
# Build for AMD64 compatibility
docker build --platform=linux/amd64 -t engineer-submission .

# Clean previous containers
docker rm -f $(docker ps -aq)

# Run the container
docker run --platform=linux/amd64 -p 6080:6080 -p 3000:3000 --name engineer-submission engineer-submission
```

### On AMD64 Machines:

```bash
docker build -t engineer-submission .
docker run -p 6080:6080 --network none --name engineer-submission engineer-submission
```

---

## Access Points

* **noVNC Desktop UI:** [http://localhost:6080](http://localhost:6080)
* **Gogs Web Interface:** [http://localhost:3000](http://localhost:3000) (inside the container)
* **Admin Credentials:** Username: `Tadmin`, Password: `admin123`

---

## Executables & Commands

### 1. Extract Gogs State (Works , kinda? I guess we need gogs API for that as well :()

```bash
docker exec engineer-submission python3 /extract_state.py
docker exec engineer-submission cat /gogs_state.json
docker cp engineer-submission:/gogs_state.json ./extracted_state.json
```

### 2. Re-run Gogs Login Script (it already runs in start.sh)

```bash
docker exec -it engineer-submission sh
python3 /mock_login.py
```

---

## What I Learned & Reflections

I started with the wrong approach — using `xdotool` for simulating mouse movements and clicking. It was completely unreliable in a headless container. Timing was off, elements shifted, and interactions failed randomly.

Switching to Selenium with direct HTML element interaction was the breakthrough. I used explicit waits and interacted with elements via their IDs and classes. This made setup and login much more reliable.

I successfully automated the creation of an API token and saved it as a string. I couldn't hit some basic endpoints like:

* `/api/v1/user`
* `/api/v1/user/repos`
* `/api/v1/repos/{owner}/{repo}/issues`

I believe this was due to not understanding the required authentication flow, not a fault in the API itself.

I initially attempted round-trip restoration by writing an `upload_state.py`, but it never worked properly. Eventually I decided to remove it and focus on delivering the parts I got right.

---

## Final Thoughts

Despite the hurdles, I really enjoyed this challenge. It pushed me to combine Docker, web automation, and creative workarounds when things didn’t work. I now have a deeper appreciation for headless environments, Selenium, and how to debug flaky setups.

There’s room to improve this, but I feel good about what I got done — and learned a lot in the process. Maybe next time I’ll get the full round-trip working. :)