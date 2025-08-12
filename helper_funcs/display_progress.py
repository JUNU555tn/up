#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Thank you LazyDeveloperr for helping us in this journey.

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import math
import os
import time

# the secret configuration specific things
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

# the Strings used for this "thing"
from translation import Translation


async def progress_for_pyrogram(
    current,
    total,
    ud_type,
    message,
    start
):
    now = time.time()
    diff = now - start
    if round(diff % 3.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000 if speed > 0 else 0
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time_str = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time_str = TimeFormatter(milliseconds=estimated_total_time)

        # Enhanced progress bar with blocks
        filled_length = int(round(20 * current / total))
        bar = '█' * filled_length + '░' * (20 - filled_length)

        # Status indicator
        status_emoji = "📥" if "Download" in ud_type else "📤"

        progress_text = f"""
{status_emoji} **{ud_type} Status**

{bar} {round(percentage, 1)}%

📊 **Statistics:**
• **Size:** {humanbytes(current)} / {humanbytes(total)}
• **Speed:** {humanbytes(speed)}/s
• **Elapsed:** {elapsed_time_str if elapsed_time_str else "0s"}
• **ETA:** {estimated_total_time_str if estimated_total_time_str and speed > 0 else "Calculating..."}

🔥 **Progress:** {percentage:.1f}% Complete"""

        try:
            await message.edit(text=progress_text)
        except:
            pass


def humanbytes(size):
    """
    https://stackoverflow.com/a/49361727/4723940
    """
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def detect_video_quality_from_size(file_size):
    """Estimate video quality based on file size"""
    if not file_size:
        return "Unknown Quality"

    size_gb = file_size / (1024**3)  # Convert to GB
    size_mb = file_size / (1024**2)  # Convert to MB

    if size_gb >= 2.5:
        return "4K Quality"
    elif size_gb >= 1.5:
        return "1080p Quality"
    elif size_mb >= 600:
        return "720p Quality"
    elif size_mb >= 300:
        return "480p Quality"
    elif size_mb >= 150:
        return "360p Quality"
    else:
        return "Low Quality"


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]