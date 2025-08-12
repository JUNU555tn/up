#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K | X-Noid

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import urllib.parse, filetype, shutil, time, tldextract, asyncio, json, math, os, requests
from PIL import Image
# the secret configuration specific things
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

# the Strings used for this "thing"
from translation import Translation

import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from helper_funcs.display_progress import humanbytes
from pyrogram.enums import ParseMode
from helper_funcs.help_uploadbot import DownLoadFile
from helper_funcs.display_progress import progress_for_pyrogram
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant
from pyrogram import Client, enums

@pyrogram.Client.on_message(pyrogram.filters.regex(pattern=".*http.*"))
async def echo(bot: Client, update: Message):
    if update.from_user.id in Config.AUTH_USERS:
        logger.info(update.from_user)
        url = update.text
        youtube_dl_username = None
        youtube_dl_password = None
        file_name = None
        folder = f'./DOWNLOADS/{update.from_user.id}/'
        bypass = ['zippyshare', 'hxfile', 'mediafire', 'anonfiles', 'antfiles']
        ext = tldextract.extract(url)
        if ext.domain in bypass:
            pablo = await update.reply_text('LK21 link detected')
            time.sleep(2.5)
            if os.path.isdir(folder):
                await update.reply_text("Don't spam, wait till your previous task done.")
                await pablo.delete()
                return
            os.makedirs(folder)
            await pablo.edit_text('Downloading...')
            bypasser = lk21.Bypass()
            xurl = bypasser.bypass_url(url)
            if ' | ' in url:
                url_parts = url.split(' | ')
                url = url_parts[0]
                file_name = url_parts[1]
            else:
                if xurl.find('/'):
                    urlname = xurl.rsplit('/', 1)[1]
                file_name = urllib.parse.unquote(urlname)
                if '+' in file_name:
                    file_name = file_name.replace('+', ' ')
            dldir = f'{folder}{file_name}'
            r = requests.get(xurl, allow_redirects=True)
            open(dldir, 'wb').write(r.content)
            try:
                file = filetype.guess(dldir)
                xfiletype = file.mime
            except AttributeError:
                xfiletype = file_name
            if xfiletype in ['video/mp4', 'video/x-matroska', 'video/webm', 'audio/mpeg']:
                metadata = extractMetadata(createParser(dldir))
                if metadata is not None:
                    if metadata.has("duration"):
                        duration = metadata.get('duration').seconds
            await pablo.edit_text('Uploading...')
            start_time = time.time()
            if xfiletype in ['video/mp4', 'video/x-matroska', 'video/webm']:
                await bot.send_video(
                    chat_id=update.chat.id,
                    video=dldir,
                    caption=file_name,
                    duration=duration,
                    reply_to_message_id=update.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        pablo,
                        start_time
                    )
                )
            elif xfiletype == 'audio/mpeg':
                await bot.send_audio(
                    chat_id=update.chat.id,
                    audio=dldir,
                    caption=file_name,
                    duration=duration,
                    reply_to_message_id=update.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        pablo,
                        start_time
                    )
                )
            else:
                await bot.send_document(
                    chat_id=update.chat.id,
                    document=dldir,
                    caption=file_name,
                    reply_to_message_id=update.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        pablo,
                        start_time
                    )
                )
            await pablo.delete()
            shutil.rmtree(folder)
            return
        if "|" in url:
            url_parts = url.split("|")
            if len(url_parts) == 2:
                url = url_parts[0]
                file_name = url_parts[1]
            elif len(url_parts) == 4:
                url = url_parts[0]
                file_name = url_parts[1]
                youtube_dl_username = url_parts[2]
                youtube_dl_password = url_parts[3]
            else:
                for entity in update.entities:
                    if entity.type == "text_link":
                        url = entity.url
                    elif entity.type == "url":
                        o = entity.offset
                        l = entity.length
                        url = url[o:o + l]
            if url is not None:
                url = url.strip()
            if file_name is not None:
                file_name = file_name.strip()
            # https://stackoverflow.com/a/761825/4723940
            if youtube_dl_username is not None:
                youtube_dl_username = youtube_dl_username.strip()
            if youtube_dl_password is not None:
                youtube_dl_password = youtube_dl_password.strip()
            logger.info(url)
            logger.info(file_name)
        else:
            for entity in update.entities:
                if entity.type == "text_link":
                    url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    url = url[o:o + l]
        if Config.HTTP_PROXY != "":
            command_to_exec = [
                "yt-dlp",
                "--no-warnings",
                "--youtube-skip-dash-manifest",
                "-j",
                url,
                "--proxy", Config.HTTP_PROXY
            ]
        else:
            command_to_exec = [
                "yt-dlp",
                "--no-warnings",
                "--youtube-skip-dash-manifest",
                "-j",
                url
            ]
        if youtube_dl_username is not None:
            command_to_exec.append("--username")
            command_to_exec.append(youtube_dl_username)
        if youtube_dl_password is not None:
            command_to_exec.append("--password")
            command_to_exec.append(youtube_dl_password)
        # logger.info(command_to_exec)
        process = await asyncio.create_subprocess_exec(
            *command_to_exec,
            # stdout must a pipe to be accessible as process.stdout
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Wait for the subprocess to finish
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        # logger.info(e_response)
        t_response = stdout.decode().strip()
        # logger.info(t_response)
        
        # Check for geo-restriction and retry with proxy
        if e_response and ("not made this video available in your country" in e_response or 
                           "not available in your country" in e_response or
                           "blocked in your country" in e_response):
            
            # Try with each proxy in the list
            for proxy in Config.AUTO_PROXY_LIST:
                try:
                    logger.info(f"Trying proxy for info extraction: {proxy}")
                    proxy_command = command_to_exec.copy()
                    
                    # Remove existing proxy if any
                    if "--proxy" in proxy_command:
                        proxy_index = proxy_command.index("--proxy")
                        proxy_command.pop(proxy_index)
                        proxy_command.pop(proxy_index)
                    
                    # Add new proxy and socket timeout
                    proxy_command.extend(["--proxy", proxy])
                    proxy_command.extend(["--socket-timeout", "30"])
                    
                    # Retry info extraction with proxy (with timeout)
                    try:
                        proxy_process = await asyncio.wait_for(
                            asyncio.create_subprocess_exec(
                                *proxy_command,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE,
                            ),
                            timeout=60  # 1 minute timeout for info extraction
                        )
                        
                        proxy_stdout, proxy_stderr = await asyncio.wait_for(
                            proxy_process.communicate(),
                            timeout=60
                        )
                        
                        proxy_e_response = proxy_stderr.decode().strip()
                        proxy_t_response = proxy_stdout.decode().strip()
                        
                        # If successful, use proxy results
                        if (proxy_t_response and 
                            not ("not made this video available in your country" in proxy_e_response) and
                            not ("blocked in your country" in proxy_e_response)):
                            logger.info(f"Success with proxy: {proxy}")
                            e_response = proxy_e_response
                            t_response = proxy_t_response
                            break
                            
                    except asyncio.TimeoutError:
                        logger.error(f"Proxy {proxy} timed out during info extraction")
                        continue
                        
                except Exception as proxy_error:
                    logger.error(f"Proxy {proxy} failed: {proxy_error}")
                    continue
        
        # https://github.com/rg3/youtube-dl/issues/2630#issuecomment-38635239
        if e_response and "nonnumeric port" not in e_response:
            # logger.warn("Status : FAIL", exc.returncode, exc.output)
            error_message = e_response.replace("please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output.", "")
            if "This video is only available for registered users." in error_message:
                error_message += Translation.SET_CUSTOM_USERNAME_PASSWORD
            await bot.send_message(
                chat_id=update.chat.id,
                text=Translation.NO_VOID_FORMAT_FOUND.format(str(error_message)),
                reply_to_message_id=update.id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            return False
        if t_response:
            # logger.info(t_response)
            x_reponse = t_response
            if "\n" in x_reponse:
                x_reponse, _ = x_reponse.split("\n")
            response_json = json.loads(x_reponse)
            save_ytdl_json_path = Config.DOWNLOAD_LOCATION + \
                "/" + str(update.from_user.id) + ".json"
            with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
                json.dump(response_json, outfile, ensure_ascii=False)
            # logger.info(response_json)
            inline_keyboard = []
            duration = None
            if "duration" in response_json:
                duration = response_json["duration"]
            if "formats" in response_json:
                for formats in response_json["formats"]:
                    format_id = formats.get("format_id")
                    format_string = formats.get("format_note")
                    if format_string is None:
                        format_string = formats.get("format")
                    format_ext = formats.get("ext")

                    # Skip audio-only formats and non-video formats
                    if "audio only" in format_string or formats.get("vcodec") == "none":
                        continue

                    # Get quality info with None check
                    height = formats.get("height") or 0
                    width = formats.get("width") or 0
                    fps = formats.get("fps") or 0

                    # Determine quality label
                    quality_label = ""
                    if height >= 2160:
                        quality_label = "4K"
                    elif height >= 1440:
                        quality_label = "1440p"
                    elif height >= 1080:
                        quality_label = "1080p"
                    elif height >= 720:
                        quality_label = "720p"
                    elif height >= 480:
                        quality_label = "480p"
                    elif height >= 360:
                        quality_label = "360p"
                    elif height >= 240:
                        quality_label = "240p"
                    else:
                        quality_label = f"{height}p" if height > 0 else "Unknown"

                    # Get file size
                    if "filesize" in formats and formats["filesize"] is not None:
                        approx_file_size = humanbytes(int(formats["filesize"]))
                    elif "filesize_approx" in formats and formats["filesize_approx"] is not None:
                        approx_file_size = f"~{humanbytes(int(formats['filesize_approx']))}"
                    else:
                        # Estimate size based on quality for YouTube videos
                        if height >= 2160:
                            approx_file_size = "~2.5GB"
                        elif height >= 1080:
                            approx_file_size = "~2GB"
                        elif height >= 720:
                            approx_file_size = "~800MB"
                        elif height >= 480:
                            approx_file_size = "~400MB"
                        elif height >= 360:
                            approx_file_size = "~200MB"
                        else:
                            approx_file_size = "~100MB"

                    cb_string_video = "{}|{}|{}".format("video", format_id, format_ext)
                    cb_string_file = "{}|{}|{}".format("file", format_id, format_ext)

                    # Create button text with quality and size
                    button_text_video = f"📹 {quality_label} / {approx_file_size}"
                    button_text_file = f"📄 {quality_label} / {approx_file_size}"
                    if fps and fps > 30:
                        button_text_video += f" ({int(fps)}fps)"
                        button_text_file += f" ({int(fps)}fps)"

                    ikeyboard = [
                        InlineKeyboardButton(
                            button_text_video,
                            callback_data=(cb_string_video).encode("UTF-8")
                        ),
                        InlineKeyboardButton(
                            button_text_file,
                            callback_data=(cb_string_file).encode("UTF-8")
                        )
                    ]

                    inline_keyboard.append(ikeyboard)

                if duration is not None:
                    cb_string_64 = "{}|{}|{}".format("audio", "64k", "mp3")
                    cb_string_128 = "{}|{}|{}".format("audio", "128k", "mp3")
                    cb_string = "{}|{}|{}".format("audio", "320k", "mp3")
                    inline_keyboard.append([
                        InlineKeyboardButton(
                            "MP3 " + "(" + "64 kbps" + ")", callback_data=cb_string_64.encode("UTF-8")),
                        InlineKeyboardButton(
                            "MP3 " + "(" + "128 kbps" + ")", callback_data=cb_string_128.encode("UTF-8"))
                    ])
                    inline_keyboard.append([
                        InlineKeyboardButton(
                            "MP3 " + "(" + "320 kbps" + ")", callback_data=cb_string.encode("UTF-8"))
                    ])
            else:
                format_id = response_json["format_id"]
                format_ext = response_json["ext"]
                cb_string_file = "{}|{}|{}".format(
                    "file", format_id, format_ext)
                cb_string_video = "{}|{}|{}".format(
                    "video", format_id, format_ext)
                inline_keyboard.append([
                    InlineKeyboardButton(
                        "SVideo",
                        callback_data=(cb_string_video).encode("UTF-8")
                    ),
                    InlineKeyboardButton(
                        "DFile",
                        callback_data=(cb_string_file).encode("UTF-8")
                    )
                ])
                cb_string_file = "{}={}={}".format(
                    "file", format_id, format_ext)
                cb_string_video = "{}={}={}".format(
                    "video", format_id, format_ext)
                inline_keyboard.append([
                    InlineKeyboardButton(
                        "video",
                        callback_data=(cb_string_video).encode("UTF-8")
                    ),
                    InlineKeyboardButton(
                        "file",
                        callback_data=(cb_string_file).encode("UTF-8")
                    )
                ])
            reply_markup = InlineKeyboardMarkup(inline_keyboard)
            # logger.info(reply_markup)
            thumbnail = Config.DEF_THUMB_NAIL_VID_S
            thumbnail_image = Config.DEF_THUMB_NAIL_VID_S
            if "thumbnail" in response_json:
                if response_json["thumbnail"] is not None:
                    thumbnail = response_json["thumbnail"]
                    thumbnail_image = response_json["thumbnail"]
            thumb_image_path = DownLoadFile(
                thumbnail_image,
                Config.DOWNLOAD_LOCATION + "/" +
                str(update.from_user.id) + ".webp",
                Config.CHUNK_SIZE,
                None,  # bot,
                Translation.DOWNLOAD_START,
                update.id,
                update.chat.id
            )
            if os.path.exists(thumb_image_path):
                im = Image.open(thumb_image_path).convert("RGB")
                im.save(thumb_image_path.replace(".webp", ".jpg"), "jpeg")
            else:
                thumb_image_path = None
            await bot.send_message(
                chat_id=update.chat.id,
                text=Translation.FORMAT_SELECTION.format(thumbnail) + "\n" + Translation.SET_CUSTOM_USERNAME_PASSWORD,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
                reply_to_message_id=update.id
            )
        else:
            # fallback for nonnumeric port a.k.a seedbox.io
            inline_keyboard = []
            cb_string_file = "{}={}={}".format(
                "file", "LFO", "NONE")
            cb_string_video = "{}={}={}".format(
                "video", "OFL", "ENON")
            inline_keyboard.append([
                InlineKeyboardButton(
                    "SVideo",
                    callback_data=(cb_string_video).encode("UTF-8")
                ),
                InlineKeyboardButton(
                    "DFile",
                    callback_data=(cb_string_file).encode("UTF-8")
                )
            ])
            reply_markup = InlineKeyboardMarkup(inline_keyboard)
            await bot.send_message(
                chat_id=update.chat.id,
                text=Translation.FORMAT_SELECTION.format(""),
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
                reply_to_message_id=update.id
            )