from app.core.config import settings


def path_conversion(path):
    if settings.base_path == "/":
        return path
    else:
        return settings.base_path + path
