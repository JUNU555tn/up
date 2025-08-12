import os

class Config(object):
    # get a token from @BotFather
    TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
    # The Telegram API things
    APP_ID = int(os.environ.get("APP_ID", 0))
    API_HASH = os.environ.get("API_HASH")
    # Get these values from my.telegram.org
    # Array to store users who are authorized to use the bot
    AUTH_USERS = set(int(x) for x in os.environ.get("AUTH_USERS", "6415368038").split())
    # the download location, where the HTTP Server runs
    DOWNLOAD_LOCATION = "./DOWNLOADS"
    # Telegram maximum file upload size
    MAX_FILE_SIZE = 50000000
    TG_MAX_FILE_SIZE = 2097152000
    FREE_USER_MAX_FILE_SIZE = 50000000
    # chunk size that should be used with requests
    CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 128))
    # default thumbnail to be used in the videos
    DEF_THUMB_NAIL_VID_S = os.environ.get("DEF_THUMB_NAIL_VID_S", "https://telegra.ph/file/1efd13f55ef33d64aa2c8.jpg")
    # proxy for accessing youtube-dl in GeoRestricted Areas
    # Get your own proxy from https://github.com/rg3/youtube-dl/issues/1091#issuecomment-230163061
    HTTP_PROXY = os.environ.get("HTTP_PROXY", "")
    
    # Auto proxy list for geo-restricted content
    AUTO_PROXY_LIST = [
        "socks5://198.23.239.134:10300",
        "socks5://72.210.252.137:4145", 
        "socks5://72.195.34.59:4145",
        "socks5://138.68.109.12:40138",
        "socks5://198.8.94.174:39078",
        "http://47.243.95.228:10080",
        "http://103.149.53.120:59166",
        "http://20.111.54.16:80",
        "socks5://103.127.204.109:25327",
        "socks5://72.195.114.184:4145",
        "http://154.236.168.181:1981",
        "socks5://184.178.172.25:15291"
    ]
    # maximum message length in Telegram
    MAX_MESSAGE_LENGTH = 40960
    # set timeout for subprocess
    PROCESS_MAX_TIMEOUT = 3600
    # watermark file
    DEF_WATER_MARK_FILE = ""
    #Admin id is stored in 
    LAZY_DEVELOPER = set(int(x) for x in os.environ.get("LAZY_ADMIN", "6415368038").split())