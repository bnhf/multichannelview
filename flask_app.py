from flask import Flask, Response, request, stream_with_context
import subprocess
import os

app = Flask(__name__)

# Configurable constants
CDVR_HOST = os.getenv("CDVR_HOST", "media-server8")
CDVR_PORT = int(os.getenv("CDVR_PORT", "8089"))
TARGET_WIDTH = 1280
TARGET_HEIGHT = 720
TARGET_FPS=29.97
CODEC= os.getenv("CODEC", "h264_qsv") # h264_qsv (hardware), libx264 (software)
BW='5120k'

def build_input_urls(channels):
    return [f"http://{CDVR_HOST}:{CDVR_PORT}/devices/ANY/channels/{ch}/stream.mpg" for ch in channels]

@app.route('/combine')
def combine_streams():
    channels = request.args.getlist('ch')[:4]
    if not channels:
        return "No channels provided", 400

    urls = build_input_urls(channels)
    num_inputs = len(urls)

    ffmpeg_cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error']

    # Add input URLs
    for url in urls:
        ffmpeg_cmd += ['-i', url]

    # Build scaling filters
    filter_parts = [
        f'[{i}:v]fps={TARGET_FPS},scale={TARGET_WIDTH}:{TARGET_HEIGHT}[v{i}]' for i in range(num_inputs)
    ]

    # Build xstack layout
    layout_map = {
        1: "[v0]xstack=inputs=1:layout=0_0[v]",
        2: "[v0][v1]xstack=inputs=2:layout=0_0|w0_0[v]",
        3: "[v0][v1][v2]xstack=inputs=3:layout=0_0|w0_0|0_h0[v]",
        4: "[v0][v1][v2][v3]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v]"
    }
    filter_parts.append(layout_map[num_inputs])

    filter_complex = ';'.join(filter_parts)

    ffmpeg_cmd += ['-filter_complex', filter_complex, '-map', '[v]']

    # Map all audio tracks individually
    for i in range(num_inputs):
        ffmpeg_cmd += ['-map', f'{i}:a']

    # Encoding settings
    ffmpeg_cmd += [
        '-c:v', CODEC,
        '-b:v', BW,
        '-c:a', 'copy',
        '-f', 'mpegts',
        'pipe:1'
    ]

    def generate():
        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
        try:
            while True:
                chunk = process.stdout.read(1024 * 16)
                if not chunk:
                    break
                yield chunk
        finally:
            process.kill()

    return Response(stream_with_context(generate()), mimetype='video/MP2T')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
