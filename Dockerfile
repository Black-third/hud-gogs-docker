FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    wget git ca-certificates sqlite3 xvfb firefox-esr \
    python3 python3-pip python3-venv curl unzip x11vnc net-tools \
    libgtk-3-0 libdbus-glib-1-2 libxt6 libxrender1 libxcomposite1 libxdamage1 libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

# Create git user and group
RUN groupadd --system git && \
    useradd --system --gid git --shell /bin/bash --home-dir /home/git git && \
    mkdir -p /home/git && \
    chown -R git:git /home/git

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz \
    && tar -xzf geckodriver-v0.36.0-linux64.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.36.0-linux64.tar.gz

RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN pip install --no-cache-dir selenium requests beautifulsoup4

COPY gogs /gogs
COPY novnc /novnc

# Create necessary directories and set permissions
RUN mkdir -p /gogs/custom/conf /gogs/data /gogs-repositories /gogs/log && \
    chown -R git:git /gogs /gogs-repositories

COPY start.sh /start.sh
COPY mock_install.py /mock_install.py
COPY mock_login.py /mock_login.py
COPY extract_state.py /extract_state.py
RUN chmod +x /start.sh /mock_login.py

WORKDIR /gogs
EXPOSE 6080 3000

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fs http://localhost:3000/ || exit 1

CMD ["/start.sh"]