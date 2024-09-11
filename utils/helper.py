import datetime
import os
import builtins

def ls(dir, filetype):
    files = []
    existing_saves = os.listdir(dir)
    for fname in existing_saves:
        if fname.endswith(filetype): files.append(fname)
    return files

def wget_datetime():
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    time_string = now.strftime("%H-%M")
    return date_string, time_string

def wget_timestamp():
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    time_string = now.strftime("%H-%M-%S")
    timestamp = f'{date_string}_{time_string}'
    return timestamp

def get_folders_and_files(dir):
    items = os.listdir(dir)
    folders, files = [], []
    for str in items:
        if os.path.isdir(dir+str):
            folders.append(str)
        else:
            files.append(str)

    return folders, files

def wget_len(obj):
    """
    Returns the length of an obj
    """
    if hasattr(obj, '__len__'):
        return len(obj)
    return 0


def question(prompt):
    blue_text = '\033[94m'
    reset_text = '\033[0m'

    colored_prompt = blue_text + prompt + reset_text

    return builtins.input(colored_prompt)
# builtins.input = question # overwrite the built-in input function

