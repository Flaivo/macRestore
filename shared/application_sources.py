"""Official download pages for applications commonly found on macOS."""

DOWNLOAD_URLS = {
    "1Password 7": "https://1password.com/downloads/mac/",
    "Alfred 5": "https://www.alfredapp.com/",
    "Android Studio": "https://developer.android.com/studio",
    "AnyDesk": "https://anydesk.com/en/downloads/mac-os",
    "Arc": "https://arc.net/download",
    "Arduino IDE": "https://www.arduino.cc/en/software/",
    "balenaEtcher": "https://etcher.balena.io/",
    "Battle.net": "https://download.battle.net/en-us/desktop",
    "Blackmagic Proxy Generator Lite": "https://www.blackmagicdesign.com/support/",
    "ChatGPT": "https://openai.com/chatgpt/desktop/",
    "ChatGPT (Classic)": "https://openai.com/chatgpt/desktop/",
    "Cursor": "https://www.cursor.com/downloads",
    "Discord": "https://discord.com/download",
    "Expo Orbit": "https://expo.dev/orbit",
    "FileZilla": "https://filezilla-project.org/download.php?platform=osx",
    "Firefox": "https://www.mozilla.org/firefox/new/",
    "Folx": "https://mac.eltima.com/download-manager.html",
    "FortiClient": "https://www.fortinet.com/support/product-downloads",
    "Gemini": "https://macpaw.com/gemini",
    "Ghostty": "https://ghostty.org/download",
    "GIMP-2.10": "https://www.gimp.org/downloads/",
    "GitHub Desktop": "https://desktop.github.com/download/",
    "Google Chrome": "https://www.google.com/chrome/",
    "HP Smart": "https://123.hp.com/",
    "Logi Options": "https://support.logi.com/hc/articles/360025297893",
    "logioptionsplus": "https://www.logitech.com/en-us/software/logi-options-plus.html",
    "Microsoft Excel": "https://www.microsoft.com/microsoft-365/download-office",
    "Microsoft PowerPoint": "https://www.microsoft.com/microsoft-365/download-office",
    "Microsoft Teams": "https://www.microsoft.com/microsoft-teams/download-app",
    "Microsoft Word": "https://www.microsoft.com/microsoft-365/download-office",
    "MotionPro": "https://www.motionpro.com/",
    "MySQLWorkbench": "https://dev.mysql.com/downloads/workbench/",
    "Obsidian": "https://obsidian.md/download",
    "OneDrive": "https://www.microsoft.com/microsoft-365/onedrive/download",
    "OpenCore Configurator": "https://mackie100projects.altervista.org/opencore-configurator/",
    "OpenVPN Connect": "https://openvpn.net/connect-docs/connect-for-macos.html",
    "Pixelmator Pro Creator Studio": "https://www.pixelmator.com/pro/",
    "QMK Toolbox": "https://github.com/qmk/qmk_toolbox/releases",
    "Raspberry Pi Imager": "https://www.raspberrypi.com/software/",
    "Ryujinx fix exp": "https://github.com/Ryujinx/Ryujinx/releases",
    "Safari": "https://support.apple.com/downloads/safari",
    "shadps4": "https://github.com/shadps4-emu/shadPS4/releases",
    "SoapUI-5.9.1": "https://www.soapui.org/downloads/soapui.html",
    "Spotify": "https://www.spotify.com/download/mac/",
    "Steam": "https://store.steampowered.com/about/",
    "Sublime Text": "https://www.sublimetext.com/download",
    "TeamViewer": "https://www.teamviewer.com/en/download/macos/",
    "Telegram": "https://desktop.telegram.org/",
    "Termius": "https://termius.com/download/macos",
    "The Unarchiver": "https://theunarchiver.com/",
    "Trae": "https://www.trae.ai/",
    "Tunnelblick": "https://tunnelblick.net/downloads.html",
    "Visual Studio Code": "https://code.visualstudio.com/download",
    "VLC": "https://www.videolan.org/vlc/download-macosx.html",
    "VMware Fusion": "https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware+Fusion",
    "WhatsApp": "https://www.whatsapp.com/download",
    "Windows App": "https://apps.apple.com/us/app/windows-app/id1295203466",
    "Xcode": "https://developer.apple.com/xcode/resources/",
    "zoom.us": "https://zoom.us/download",
}

SYSTEM_APPLICATIONS = {
    "App Store", "Apps", "Automator", "Books", "Calculator", "Calendar",
    "Chess", "Clock", "Contacts", "Dictionary", "FaceTime", "FindMy",
    "Font Book", "Freeform", "Games", "Home", "Image Capture",
    "Image Playground", "iPhone Mirroring", "Journal", "Mail", "Maps",
    "Messages", "Mission Control", "Music", "News", "Notes", "Passwords",
    "Phone", "Photo Booth", "Photos", "Podcasts", "Preview", "Reminders",
    "Shortcuts", "Siri", "Siri AI", "Stickies", "Stocks", "System Settings",
    "TextEdit", "Time Machine", "Tips", "TV", "VoiceMemos", "Weather",
}


def application_download_url(name: str) -> str | None:
    """Return the curated official download page for an application."""
    return DOWNLOAD_URLS.get(name)


def is_macos_component(name: str) -> bool:
    return name in SYSTEM_APPLICATIONS
