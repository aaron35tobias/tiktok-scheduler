import os
import subprocess
import logging

import imageio_ffmpeg

logger = logging.getLogger(__name__)

# Target resolution for each aspect ratio.
_RATIO_DIMS = {
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "16:9": (1920, 1080),
}


def transform_aspect_ratio(input_path: str, ratio: str) -> str:
    """Re-encode a video to the given aspect ratio (letterboxed, no content lost).

    Returns the path to the converted file, or the original path if the ratio
    is unknown / "original". TikTok reads the video's real dimensions, so this
    is what makes the chosen aspect ratio show up on the actual post.
    """
    if ratio not in _RATIO_DIMS:
        return input_path

    w, h = _RATIO_DIMS[ratio]
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    base, _ = os.path.splitext(input_path)
    out_path = f"{base}_{ratio.replace(':', 'x')}.mp4"

    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"
    )
    cmd = [
        exe, "-y", "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        out_path,
    ]
    logger.info(f"Converting video to {ratio} ({w}x{h}): {input_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"ffmpeg failed: {result.stderr[-500:]}")
        raise Exception(f"Video aspect-ratio conversion to {ratio} failed.")
    return out_path
