#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import asyncio
import glob
import json
import math
import os
import shutil
import time
from datetime import datetime

# the secret configuration specific things
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

# the Strings used for this "thing"
from translation import Translation

import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)

from pyrogram import enums
from pyrogram.enums import ParseMode
from pyrogram.types import InputMediaPhoto
from helper_funcs.display_progress import progress_for_pyrogram, humanbytes
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
# https://stackoverflow.com/a/37631799/4723940
from PIL import Image
from helper_funcs.help_Nekmo_ffmpeg import generate_screen_shots


async def youtube_dl_call_back(bot, update):
    cb_data = update.data
    # youtube_dl extractors
    tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("|")
    thumb_image_path = Config.DOWNLOAD_LOCATION + \
        "/" + str(update.from_user.id) + ".jpg"
    save_ytdl_json_path = Config.DOWNLOAD_LOCATION + \
        "/" + str(update.from_user.id) + ".json"
    try:
        with open(save_ytdl_json_path, "r", encoding="utf8") as f:
            response_json = json.load(f)
    except (FileNotFoundError) as e:
        await bot.delete_messages(
            chat_id=update.message.chat.id,
            message_ids=update.message.id,
            revoke=True
        )
        return False
    youtube_dl_url = update.message.reply_to_message.text
    custom_file_name = str(response_json.get("title")) + \
        "_" + youtube_dl_format + "." + youtube_dl_ext
    youtube_dl_username = None
    youtube_dl_password = None
    if "|" in youtube_dl_url:
        url_parts = youtube_dl_url.split("|")
        if len(url_parts) == 2:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
        elif len(url_parts) == 4:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
            youtube_dl_username = url_parts[2]
            youtube_dl_password = url_parts[3]
        else:
            for entity in update.message.reply_to_message.entities:
                if entity.type == "text_link":
                    youtube_dl_url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    youtube_dl_url = youtube_dl_url[o:o + l]
        if youtube_dl_url is not None:
            youtube_dl_url = youtube_dl_url.strip()
        if custom_file_name is not None:
            custom_file_name = custom_file_name.strip()
        # https://stackoverflow.com/a/761825/4723940
        if youtube_dl_username is not None:
            youtube_dl_username = youtube_dl_username.strip()
        if youtube_dl_password is not None:
            youtube_dl_password = youtube_dl_password.strip()
        logger.info(youtube_dl_url)
        logger.info(custom_file_name)
    else:
        for entity in update.message.reply_to_message.entities:
            if entity.type == "text_link":
                youtube_dl_url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                youtube_dl_url = youtube_dl_url[o:o + l]
    await bot.edit_message_text(
        text=Translation.DOWNLOAD_START,
        chat_id=update.message.chat.id,
        message_id=update.message.id
    )
    user = await bot.get_me()
    mention = f"@{user.username}" if user.username else user.first_name
    description = Translation.CUSTOM_CAPTION_UL_FILE.format(mention)
    if "fulltitle" in response_json:
        description = response_json["fulltitle"][0:1021]
        # escape Markdown and special characters
    tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id)
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)
    download_directory = tmp_directory_for_each_user + "/" + custom_file_name
    command_to_exec = []
    if tg_send_type == "audio":
        command_to_exec = [
            "yt-dlp",
            "-c",
            "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
            "--prefer-ffmpeg",
            "--extract-audio",
            "--audio-format", youtube_dl_ext,
            "--audio-quality", youtube_dl_format,
            youtube_dl_url,
            "-o", download_directory
        ]
    else:
        # command_to_exec = ["youtube-dl", "-f", youtube_dl_format, "--hls-prefer-ffmpeg", "--recode-video", "mp4", "-k", youtube_dl_url, "-o", download_directory]
        minus_f_format = youtube_dl_format
        if "youtu" in youtube_dl_url:
            minus_f_format = youtube_dl_format + "+bestaudio"
        command_to_exec = [
            "yt-dlp",
            "-c",
            "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
            "--embed-subs",
            "-f", minus_f_format,
            "--hls-prefer-ffmpeg",
            "--merge-output-format", "webm",
            youtube_dl_url,
            "-o", download_directory
        ]
    if Config.HTTP_PROXY != "":
        command_to_exec.append("--proxy")
        command_to_exec.append(Config.HTTP_PROXY)
    if youtube_dl_username is not None:
        command_to_exec.append("--username")
        command_to_exec.append(youtube_dl_username)
    if youtube_dl_password is not None:
        command_to_exec.append("--password")
        command_to_exec.append(youtube_dl_password)
    command_to_exec.append("--no-warnings")
    # command_to_exec.append("--quiet")
    logger.info(command_to_exec)
    start = datetime.now()
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    logger.info(e_response)
    logger.info(t_response)
    
    # Enhanced geo-restriction bypass for downloads
    if e_response and ("not made this video available in your country" in e_response or 
                       "not available in your country" in e_response or
                       "blocked in your country" in e_response or
                       "geo blocked" in e_response.lower() or
                       "geo-blocked" in e_response.lower()):
        
        await bot.edit_message_text(
            text="🌍 Video is geo-restricted. Attempting location bypass...",
            chat_id=update.message.chat.id,
            message_id=update.message.id
        )
        
        # Method 1: Try geo-bypass options first
        bypass_success = False
        
        try:
            logger.info("Attempting geo-bypass method")
            bypass_command = command_to_exec.copy()
            bypass_command.extend([
                "--geo-bypass",
                "--geo-bypass-country", "US", 
                "--user-agent", Config.BYPASS_HEADERS['User-Agent'],
                "--referer", "https://www.youtube.com/",
                "--add-header", "Accept-Language:en-US,en;q=0.9"
            ])
            
            bypass_process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *bypass_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=90
            )
            
            bypass_stdout, bypass_stderr = await asyncio.wait_for(
                bypass_process.communicate(),
                timeout=90
            )
            
            bypass_e_response = bypass_stderr.decode().strip()
            bypass_t_response = bypass_stdout.decode().strip()
            
            if (bypass_t_response and 
                not ("not made this video available in your country" in bypass_e_response) and
                not ("geo" in bypass_e_response.lower() and "block" in bypass_e_response.lower())):
                logger.info("Success with geo-bypass method")
                e_response = bypass_e_response
                t_response = bypass_t_response
                bypass_success = True
                
        except Exception as bypass_error:
            logger.error(f"Geo-bypass method failed: {bypass_error}")
        
        # Method 2: If geo-bypass fails, try proxy servers
        if not bypass_success:
            await bot.edit_message_text(
                text="🔄 Geo-bypass failed. Trying proxy servers...",
                chat_id=update.message.chat.id,
                message_id=update.message.id
            )
            
            proxy_success = False
            for i, proxy in enumerate(Config.AUTO_PROXY_LIST[:6]):  # Try first 6 proxies
                try:
                    logger.info(f"Trying proxy {i+1}/6: {proxy}")
                    
                    await bot.edit_message_text(
                        text=f"🌐 Trying proxy server {i+1}/6...",
                        chat_id=update.message.chat.id,
                        message_id=update.message.id
                    )
                    
                    proxy_command = command_to_exec.copy()
                    
                    # Remove existing proxy if any
                    if "--proxy" in proxy_command:
                        proxy_index = proxy_command.index("--proxy")
                        proxy_command.pop(proxy_index)
                        proxy_command.pop(proxy_index)
                    
                    # Add proxy and enhanced bypass options
                    proxy_command.extend([
                        "--proxy", proxy,
                        "--socket-timeout", "30",
                        "--geo-bypass",
                        "--user-agent", Config.BYPASS_HEADERS['User-Agent'],
                        "--add-header", "Accept-Language:en-US,en;q=0.9"
                    ])
                    
                    # Retry download with proxy
                    try:
                        proxy_process = await asyncio.wait_for(
                            asyncio.create_subprocess_exec(
                                *proxy_command,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE,
                            ),
                            timeout=120
                        )
                        
                        proxy_stdout, proxy_stderr = await asyncio.wait_for(
                            proxy_process.communicate(),
                            timeout=120
                        )
                        
                        proxy_e_response = proxy_stderr.decode().strip()
                        proxy_t_response = proxy_stdout.decode().strip()
                        
                        # Check if proxy worked
                        if (proxy_t_response and 
                            not ("not made this video available in your country" in proxy_e_response) and
                            not ("blocked in your country" in proxy_e_response) and
                            not ("geo" in proxy_e_response.lower() and "block" in proxy_e_response.lower())):
                            
                            logger.info(f"Success with proxy: {proxy}")
                            e_response = proxy_e_response
                            t_response = proxy_t_response
                            proxy_success = True
                            
                            await bot.edit_message_text(
                                text="✅ Successfully bypassed geo-restriction! Downloading...",
                                chat_id=update.message.chat.id,
                                message_id=update.message.id
                            )
                            break
                        else:
                            logger.info(f"Proxy {proxy} still geo-blocked or failed")
                            
                    except asyncio.TimeoutError:
                        logger.error(f"Proxy {proxy} timed out")
                        continue
                        
                except Exception as proxy_error:
                    logger.error(f"Proxy {proxy} failed: {proxy_error}")
                    continue
            
            if not proxy_success and not t_response:
                await bot.edit_message_text(
                    chat_id=update.message.chat.id,
                    message_id=update.message.id,
                    text="❌ **Location Bypass Failed**\n\n"
                         "The video is heavily geo-restricted and all bypass methods failed:\n"
                         "• Geo-bypass attempts: Failed\n"
                         "• Proxy servers tested: Failed\n\n"
                         "**Suggestions:**\n"
                         "• Try again in a few minutes (servers may be busy)\n" 
                         "• Check if the video is available in your region later\n"
                         "• Try a different video link\n\n"
                         "This video appears to be strictly region-locked."
                )
                return False
    
    ad_string_to_replace = "please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output."
    if e_response and ad_string_to_replace in e_response:
        error_message = e_response.replace(ad_string_to_replace, "")
        await bot.edit_message_text(
            chat_id=update.message.chat.id,
            message_id=update.message.id,
            text=error_message
        )
        return False
    if t_response:
        # logger.info(t_response)
        os.remove(save_ytdl_json_path)
        end_one = datetime.now()
        time_taken_for_download = (end_one -start).seconds
        # Handle multiple possible output formats from yt-dlp
        possible_extensions = [".webm", ".mp4", ".mkv", ".m4a", ".opus"]
        base_name = os.path.splitext(download_directory)[0]

        actual_file = None
        file_size = 0

        try:
            file_size = os.stat(download_directory).st_size
            actual_file = download_directory
        except FileNotFoundError:
            # Check for files with different extensions
            for ext in possible_extensions:
                test_file = base_name + ext
                if os.path.exists(test_file):
                    actual_file = test_file
                    file_size = os.stat(test_file).st_size
                    download_directory = test_file
                    break

            # If still no file found, check for partial files that might need renaming
            if not actual_file:
                import glob
                pattern = base_name + "*"
                matching_files = glob.glob(pattern)
                if matching_files:
                    # Use the largest file (likely the merged result)
                    actual_file = max(matching_files, key=os.path.getsize)
                    file_size = os.stat(actual_file).st_size
                    download_directory = actual_file

        if file_size > Config.TG_MAX_FILE_SIZE:
            await bot.edit_message_text(
                chat_id=update.message.chat.id,
                text=Translation.RCHD_TG_API_LIMIT.format(time_taken_for_download, humanbytes(file_size)),
                message_id=update.message.id
            )
        else:
            is_w_f = False
            images = await generate_screen_shots(
                download_directory,
                tmp_directory_for_each_user,
                is_w_f,
                Config.DEF_WATER_MARK_FILE,
                300,
                9
            )
            logger.info(images)
            await bot.edit_message_text(
                text=Translation.UPLOAD_START,
                chat_id=update.message.chat.id,
                message_id=update.message.id
            )
            # get the correct width, height, and duration for videos greater than 10MB
            # ref: message from @BotSupport
            width = 0
            height = 0
            duration = 0
            if tg_send_type != "file":
                metadata = extractMetadata(createParser(download_directory))
                if metadata is not None:
                    if metadata.has("duration"):
                        duration = metadata.get('duration').seconds
            # get the correct width, height, and duration for videos greater than 10MB
            if os.path.exists(thumb_image_path):
                width = 0
                height = 0
                metadata = extractMetadata(createParser(thumb_image_path))
                if metadata.has("width"):
                    width = metadata.get("width")
                if metadata.has("height"):
                    height = metadata.get("height")
                if tg_send_type == "vm":
                    height = width
                # resize image
                # ref: https://t.me/PyrogramChat/44663
                # https://stackoverflow.com/a/21669827/4723940
                Image.open(thumb_image_path).convert(
                    "RGB").save(thumb_image_path)
                img = Image.open(thumb_image_path)
                # https://stackoverflow.com/a/37631799/4723940
                # img.thumbnail((90, 90))
                if tg_send_type == "file":
                    img.resize((320, height))
                else:
                    img.resize((90, height))
                img.save(thumb_image_path, "JPEG")
                # https://pillow.readthedocs.io/en/3.1.x/reference/Image.html#create-thumbnails

            else:
                thumb_image_path = None
            start_time = time.time()
            # try to upload file
            if tg_send_type == "audio":
                await bot.send_audio(
                    chat_id=update.message.chat.id,
                    audio=download_directory,
                    caption=description,
                    parse_mode=ParseMode.HTML,
                    duration=duration,
                    # performer=response_json["uploader"],
                    # title=response_json["title"],
                    # reply_markup=reply_markup,
                    thumb=thumb_image_path,
                    reply_to_message_id=update.message.reply_to_message.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time
                    )
                )
            elif tg_send_type == "file":
                await bot.send_document(
                    chat_id=update.message.chat.id,
                    document=download_directory,
                    thumb=thumb_image_path,
                    caption=description,
                    parse_mode=ParseMode.HTML,
                    # reply_markup=reply_markup,
                    reply_to_message_id=update.message.reply_to_message.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time
                    )
                )
            elif tg_send_type == "vm":
                await bot.send_video_note(
                    chat_id=update.message.chat.id,
                    video_note=download_directory,
                    duration=duration,
                    length=width,
                    thumb=thumb_image_path,
                    reply_to_message_id=update.message.reply_to_message.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time
                    )
                )
            elif tg_send_type == "video":
                await bot.send_video(
                    chat_id=update.message.chat.id,
                    video=download_directory,
                    caption=description,
                    parse_mode=ParseMode.HTML,
                    duration=duration,
                    width=width,
                    height=height,
                    supports_streaming=True,
                    # reply_markup=reply_markup,
                    thumb=thumb_image_path,
                    reply_to_message_id=update.message.reply_to_message.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time
                    )
                )
            else:
                logger.info("Did this happen? :\\")
            end_two = datetime.now()
            time_taken_for_upload = (end_two - end_one).seconds
            #
            media_album_p = []
            if images is not None:
                i = 0
                caption = "© @LazyDeveloperr"
                if is_w_f:
                    caption = "@LazyDeveloperr"
                for image in images:
                    if os.path.exists(str(image)):
                        if i == 0:
                            media_album_p.append(
                                InputMediaPhoto(
                                    media=image,
                                    caption=caption,
                                    parse_mode=ParseMode.HTML
                                )
                            )
                        else:
                            media_album_p.append(
                                InputMediaPhoto(
                                    media=image
                                )
                            )
                        i = i + 1
            await bot.send_media_group(
                chat_id=update.message.chat.id,
                disable_notification=True,
                reply_to_message_id=update.message.id,
                media=media_album_p
            )
            #
            try:
                shutil.rmtree(tmp_directory_for_each_user)
                os.remove(thumb_image_path)
            except:
                pass
            await bot.edit_message_text(
                text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(time_taken_for_download, time_taken_for_upload),
                chat_id=update.message.chat.id,
                message_id=update.message.id,
                disable_web_page_preview=True
            )