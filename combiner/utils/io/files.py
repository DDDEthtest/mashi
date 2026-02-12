import shutil


def read_file(file_path):
    with open(file_path, "rb") as f:
        return f.read()


def save_file(file_path, content):
    with open(file_path, "wb") as f:
        f.write(content)


def rm_dir(dir_path):
    if dir_path.exists():
        for item in dir_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
