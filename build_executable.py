import os
import sys
import shutil
import subprocess


def path_join(list_of_names):
    path = ''
    for name in list_of_names:
        path = os.path.join(path, name)
    return path

def remove_file(file):
    try:
        os.remove(file)
    except:
        pass

def remove_dir(dir):
    try:
        shutil.rmtree(dir)
    except:
        pass

def clean_up():
    remove_file('anime_watch_list.spec')

    dirs = ['build', 'dist']
    for dir_ in dirs:
        remove_dir(dir_)

def call_process(root_path):
    site_packages = path_join([root_path, 'env', 'Lib', 'site-packages'])
    params = ['pyinstaller',
              '--onefile',
              '--noconsole',
              '--paths', site_packages,
              '--add-data', 'images/image-not-found.png;images',
              'anime_watch_list.py']
    subprocess.call(params)

def add_files(root_path):
    shutil.copyfile('config.txt', path_join([root_path, 'dist', 'config.txt']))


if __name__ == '__main__':
    root_path = os.path.dirname(os.path.realpath(__file__))
    print('Cleaning up old files...\n')
    clean_up()
    print('\nCreating the exe...\n')
    call_process(root_path)
    print('\nAdding missing files...\n')
    add_files(root_path)
    print('\nDone.')
