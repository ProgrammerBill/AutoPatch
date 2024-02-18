#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
This script is used to generate patches based on Android/Linux SDK.
It relys on python version more than 3.6 and fzf for fast select.
"""
__author__ = "Bill Cong"
__license__ = "MIT"
__email__ = "cjcbill@gmail.com"

import json
import sys
import os
import subprocess
import re

import os
import configparser

from datetime import datetime
import time
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

welcome_str="Thanks to use"
str_auto_patch = '''
 █████╗ ██╗   ██╗████████╗ ██████╗     ██████╗  █████╗ ████████╗ ██████╗██╗  ██╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗    ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██║  ██║
███████║██║   ██║   ██║   ██║   ██║    ██████╔╝███████║   ██║   ██║     ███████║
██╔══██║██║   ██║   ██║   ██║   ██║    ██╔═══╝ ██╔══██║   ██║   ██║     ██╔══██║
██║  ██║╚██████╔╝   ██║   ╚██████╔╝    ██║     ██║  ██║   ██║   ╚██████╗██║  ██║
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚═╝     ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝
'''

def find_git_repos(root_dir):
    git_dirs = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '.repo' in dirpath:
            continue
        if '.git' in dirnames:
            git_dirs.append(dirpath)
            dirnames.remove('.git')
    return git_dirs

def save_to_config(config_file, git_dirs):
    config = configparser.ConfigParser()
    config['Git Repositories'] = {}
    i = 1
    for path_list in git_dirs:  # git_dirs现在是包含路径列表的列表
       for path in path_list:  # 遍历每个子列表中的路径
           config['Git Repositories'][f'{i}'] = str(path)  # 确保是字符串
           i += 1

    with open(config_file, 'w') as configfile:
        config.write(configfile)

def read_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)

    print('Available sections:', config.sections())
    git_list=''
    if 'Git Repositories' in config:
        for repo in config['Git Repositories']:
            path = config['Git Repositories'][repo]
            git_list += '{:s}\n'.format(path)
    return git_list

def select_commits_with_fzf(repo_path):
    original_cwd = os.getcwd()

    try:
        os.chdir(repo_path)

        git_log_command = ['git', 'log', '--oneline']
        git_log_output = subprocess.check_output(git_log_command).decode('utf-8')

        fzf_command = ['fzf', '--prompt', 'plz choosed the beginning commit> ', '--height', '40%']
        start_commit_process = subprocess.Popen(fzf_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        start_commit, _ = start_commit_process.communicate(input=git_log_output.encode('utf-8'))
        start_commit_hash = start_commit.decode('utf-8').split()[0]

        if start_commit_hash:
            git_log_command = ['git', 'log', f'{start_commit_hash}..HEAD', '--oneline']
            git_log_output_after_start = subprocess.check_output(git_log_command).decode('utf-8')

            fzf_command[2] = 'plz select the ended commit> '
            end_commit_process = subprocess.Popen(fzf_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            end_commit, _ = end_commit_process.communicate(input=git_log_output_after_start.encode('utf-8'))
            end_commit_hash = end_commit.decode('utf-8').split()[0] if end_commit else None
        else:
            end_commit_hash = None

        return start_commit_hash, end_commit_hash
    finally:
        os.chdir(original_cwd)

def save_repos_info_to_json(repos_info, filename):
    with open(filename, 'w') as file:
        json.dump(repos_info, file, indent=4)


def generate_patches_and_copy_sources(repo_info, target_path, patch_filename):
    repo_path = repo_info['name']
    repo_type = repo_info['type']

    original_cwd = os.getcwd()
    final_patch_path = os.path.join(original_cwd, target_path, repo_path.strip("./"), patch_filename.upper())
    os.makedirs(os.path.dirname(final_patch_path), exist_ok=True)

    os.chdir(repo_path)

    sourcefiles_target_dir = os.path.join(original_cwd, target_path, "sources", repo_path.strip("./"))
    try:
        source_dir = os.path.join(original_cwd, repo_path)
        if repo_type == 'history':
            start_commit = repo_info['start_commit']
            end_commit = repo_info['end_commit']
            git_command = ['git', 'diff', f'{start_commit}..{end_commit}', '--binary']
            copy_changed_files(source_dir, sourcefiles_target_dir, repo_type, start_commit, end_commit)
        elif repo_type == 'diff' or repo_type == 'cache':
            git_command = ['git', 'diff'] if repo_type == 'diff' else ['git', 'diff', '--cached']
            copy_changed_files(source_dir, sourcefiles_target_dir, repo_type)
        with open(final_patch_path, 'w') as f:
            subprocess.run(git_command, stdout=f, check=True)
    finally:
        os.chdir(original_cwd)

def copy_changed_files(repo_path, target_path, diff_type='diff', start_commit=None, end_commit=None):
    try:
        if diff_type == 'diff':
            git_command = ['git', 'diff', '--name-only']
        elif diff_type == 'cached':
            git_command = ['git', 'diff', '--cached', '--name-only']
        elif diff_type == 'history' and start_commit and end_commit:
            git_command = ['git', 'diff', f'{start_commit}..{end_commit}', '--name-only']
        else:
            raise ValueError("Invalid diff type or missing commits for history type.")

        changed_files = subprocess.check_output(git_command).decode('utf-8').splitlines()

        for file in changed_files:
            source_file = os.path.join(repo_path, file)
            target_file = os.path.join(target_path, file)

            os.makedirs(os.path.dirname(target_file), exist_ok=True)

            shutil.copy2(source_file, target_file)

    finally:
        pass

def main():
    # 1. show logo.
    os.system("clear")
    print(welcome_str)
    print(bcolors.HEADER + str_auto_patch + bcolors.ENDC)

    # 2. parse and save config file for the first time.
    #todo: select from args
    root_dir = './android'
    config_file = '.git_repos.ini'

    if os.path.exists(config_file):
        print(f"{config_file} exits, skip searching .git dirs。")
    else:
        print("wait for first searching git respository...")
        # 使用线程池
        start_time = time.time()  # 记录开始时间
        with ThreadPoolExecutor() as executor:
            # 提交目录遍历任务
            futures = [executor.submit(find_git_repos, os.path.join(root_dir, name)) for name in os.listdir(root_dir)]
        # 收集结果
        git_dirs = []
        for future in as_completed(futures):
            result = future.result()
            if result:
                git_dirs.append(result)
        git_dirs = sorted(git_dirs);
        save_to_config(config_file, git_dirs)
        print(f"infos for all .git directroies in {root_dir} has saved to {config_file}.")
        end_time = time.time()  # 记录结束时间
        print(f"Execution time: {end_time - start_time} seconds")  # 计算并打印执行时间

    # 3. read config_file.
    sdk_infos=read_config(config_file)

    # 4. please enter your patch name
    patch_subject = input("Please input the patch's name: ")

    repos_info = []
    loop_exit = False
    while not loop_exit:
        # 4. show git respository
        fzf_command = ['fzf', '--ansi', '--prompt', '1. plz choose the git repository you want to patch> ', '--height', '40%']
        process = subprocess.Popen(fzf_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = process.communicate(input=sdk_infos.encode('utf-8'))
        git_dir_name = stdout.decode('utf-8').strip()
        if git_dir_name:
            print(bcolors.OKCYAN + 'patch location: ' + git_dir_name + bcolors.ENDC)
        else:
            print("No selection made.")
            sys.exit(0)
        # 5. show patch type
        fzf_command[3] = '2. please chose the diff type> '
        process = subprocess.Popen(fzf_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        patch_infos = " 1. diff\n 2. cache\n 3. history\n"
        stdout, stderr = process.communicate(input=patch_infos.encode('utf-8'))
        patch_type = stdout.decode('utf-8').strip()
        patch_type = re.sub(r'^\d+\.\s+', '', patch_type)
        if patch_type:
            print(bcolors.OKCYAN + 'type: ' + patch_type + bcolors.ENDC)
        else:
            print("No selection made.")
            sys.exit(0)
        git_info = {
                'name': git_dir_name,
                'type': patch_type
                }
        if patch_type == 'history':
            start_commit, end_commit = select_commits_with_fzf(git_dir_name)
            git_info['start_commit'] = start_commit
            git_info['end_commit'] = end_commit
        repos_info.append(git_info)

        fzf_command[3] = '3. continue to patch?> '
        process = subprocess.Popen(fzf_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        select_infos = " 1. yes\n 2. no\n"
        stdout, stderr = process.communicate(input=select_infos.encode('utf-8'))
        ans = stdout.decode('utf-8').strip()
        ans = re.sub(r'^\d+\.\s+', '', ans)
        if ans == 'no':
            loop_exit = True

    save_repos_info_to_json(repos_info, '.repos_info.json')
    with open('.repos_info.json') as f:
        repos_info = json.load(f)
    target_path = './auto_create_patch'
    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d')

    target_patch_dir = os.path.join(target_path.strip("./"), formatted_date)
    if os.path.exists(target_patch_dir):
        shutil.rmtree(target_patch_dir)
    os.makedirs(os.path.dirname(target_patch_dir), exist_ok=True)

    patch_filename = f"{patch_subject.replace(' ', '_')}.patch"

    for repo_info in repos_info:
        generate_patches_and_copy_sources(repo_info, target_patch_dir, patch_filename)

if __name__ == '__main__':
    main()
