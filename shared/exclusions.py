COMMON_FILES = {
    ".DS_Store",
    "Thumbs.db"
}


def should_exclude(path):

    return path.name in COMMON_FILES