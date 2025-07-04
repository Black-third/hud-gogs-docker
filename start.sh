#!/bin/bash

# Start Xvfb for virtual display
Xvfb :99 -screen 0 1024x768x16 &

set -e

# Create Gogs directories if they don't exist and set permissions
mkdir -p /gogs/custom/conf
mkdir -p /gogs/data
mkdir -p /gogs-repositories
mkdir -p /gogs/log
chown -R git:git /gogs /gogs-repositories

# Start Gogs as git user
cd /gogs
su -c "./gogs web" git &

echo "Waiting for Gogs to start..."
for i in {1..120}; do
  if netstat -tln | grep -E '(:|\.|::)3000' > /dev/null; then
    echo "✅ Gogs is up!"
    break
  fi
  sleep 0.5
done
if ! netstat -tln | grep -E '(:|\.|::)3000' > /dev/null; then
  echo "❌ Gogs did not start within the expected time."
  exit 1
fi

export DISPLAY=:99

firefox http://localhost:3000 &
sleep 2

x11vnc -display :99 -nopw -forever -shared &

cd /novnc || { echo "/novnc not found"; exit 1; }
./utils/novnc_proxy --vnc localhost:5900 --listen 6080 &

# Run initial setup
python3 /mock_install.py
python3 /mock_login.py

echo "✅ Setup complete! You can now:"
echo "   - Access Gogs at http://localhost:6080"
echo "   - Run 'python3 /extract_state.py' to extract current state"

wait

