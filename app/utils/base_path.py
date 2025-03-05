from app.core.config import settings

'''
=====================================================
# Convert a path to include the base path if set.
=====================================================
'''
def path_conversion(path):
    if settings.base_path == "/":
        return path
    else:
        return settings.base_path + path
