import os

def _is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")

def get_files(paths: list[str]) -> list[str]:
    files = []
    for file in paths:
        if os.path.isfile(file):
            files.append(file)
        elif os.path.isdir(file):
            for subfile in os.listdir(file):
                subpath = os.path.join(file, subfile)
                if os.path.isfile(subpath):
                    files.append(os.path.abspath(subpath))
    return files