FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    wget git ca-certificates sqlite3 xvfb firefox-esr \
    python3 python3-pip python3-venv curl unzip x11vnc net-tools \
    libgtk-3-0 libdbus-glib-1-2 libxt6 libxrender1 libxcomposite1 libxdamage1 libxrandr2 \
    && rm -rf /var/lib/apt/lists/*


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

RUN mkdir -p /gogs && \
    cd /gogs && \
    wget https://github.com/gogs/gogs/releases/download/v0.13.0/gogs_0.13.0_linux_amd64.tar.gz && \
    tar -xzf gogs_0.13.0_linux_amd64.tar.gz --strip-components=1 && \
    rm gogs_0.13.0_linux_amd64.tar.gz && \
    chmod +x gogs

COPY gogs/custom /gogs/custom
COPY novnc /novnc


RUN mkdir -p /gogs/custom/conf /gogs/data /gogs-repositories /gogs/log && \
    chown -R git:git /gogs /gogs-repositories

COPY start.sh /start.sh
COPY mock_install.py /mock_install.py
COPY mock_login.py /mock_login.py
COPY create_token.py /create_token.py
COPY extract_complete_backup.py /extract_complete_backup.py
COPY extract_system_state.sh /extract_system_state.sh
COPY requirements.txt /requirements.txt
RUN chmod +x /start.sh /mock_login.py /extract_system_state.sh

WORKDIR /gogs
EXPOSE 6080 3000


HEALTHCHECK --interval=15s --timeout=10s --start-period=60s --retries=5 \
  CMD curl -fs http://localhost:3000/ && \
      test -f /gogs/data/gogs.db && \
      pgrep -f "gogs web" > /dev/null || exit 1

CMD ["/start.sh"]
