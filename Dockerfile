#docker buildx build --platform linux/amd64 -f Dockerfile -t bnhf/multichannelview:test . --push --no-cache
FROM debian:bookworm-slim

RUN echo "deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 python3-pip curl nano ffmpeg \
    --no-install-recommends && \
    apt-get install -y --no-install-recommends intel-media-va-driver-non-free vainfo || \
    echo "Warning: intel-media-va-driver-non-free or vainfo not found, continuing without them" && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages flask

COPY flask_app.py .

CMD ["python3", "flask_app.py"]
