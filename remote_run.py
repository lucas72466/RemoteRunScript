# encoding: utf-8

"""
@author : lucas
@contact : lucas72466@gmail.com
"""

import os
from collections import deque
from os.path import join
from paramiko import SSHClient
from paramiko import AutoAddPolicy
import threading

# Settings
py_files = []
enter_file = ''  # the file to execute
py_folders = [(current_root_folder := './')]  # Recursively push the current folder to the remote server by default
exclude = {''}  # like .gitignore
exclude_file_trie = {}  # Trie for excluding specified files
remote_python_interpreter = '/usr/bin/python3'
remote_username = ''
remote_password = ''
remote_current_working_directory = f'/home/{remote_username}/workplace'
remote_ip = ''


def run():
    traverse_folder()

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    try:
        ssh.connect(remote_ip, username=remote_username, password=remote_password, port=22, timeout=5)
        ssh.exec_command(f'echo "hello!"')
        # mount /mnt/sda1 to home folder as "workplace"
        ssh.exec_command(
            f'if [ ! -d "workplace" ]; then\nmkdir -p workplace\necho {remote_password} | sudo mount /mnt/sda1 ~/workplace\nfi')
        # change the ownership of workplace folder
        ssh.exec_command(f'echo {remote_password} | sudo chown -R lucas /home/lucas')
        # make the CWD
        ssh.exec_command(f'mkdir -p {remote_current_working_directory}')
        ssh.exec_command(f'sudo chmod -R 777 {remote_current_working_directory}')
        sftp = ssh.open_sftp()
        for f in py_files:
            components = f.split('/')
            if len(components) > 1:  # Files in folders
                target_dir = join(remote_current_working_directory, '/'.join(components[:-1])).replace('\\', '/')
                ssh.exec_command(f'mkdir -p {target_dir}')
            else:  # Files in CWD
                target_dir = remote_current_working_directory.replace('\\', '/')
            print(f'Send {components[-1]} to {remote_ip}:{target_dir}')
            sftp.put(f, join(target_dir, components[-1]).replace('\\', '/'))

        if len(py_files) > 0:
            # the enter file will be the main file
            main_py = join(remote_current_working_directory, enter_file).replace('\\', '/')
            print(f'###################### RUN {enter_file} ######################')
            # execute the code

            stdin, stdout, stderr = ssh.exec_command(
                f'cd {remote_current_working_directory}; {remote_python_interpreter} {main_py} '
                f'--ip 192.168.56.107,192.168.56.105', bufsize=1, get_pty=True)

            stdout_iter = iter(stdout.readline, '')
            stderr_iter = iter(stderr.readline, '')

            def print_line(it):
                for out in it:
                    if out:
                        print(out.strip())

            # multi threads to print output and error
            th_out = threading.Thread(target=print_line, args=(stdout_iter,))
            th_err = threading.Thread(target=print_line, args=(stderr_iter,))

            th_out.start()
            th_err.start()
            th_out.join()
            th_err.join()

            exit_code = stderr.channel.recv_exit_status()
            print(f'###################### EXIT Code {exit_code} ######################')
        else:
            print('No py files.')

    except Exception as ex:
        print("--------------------Local Exception-------------------------")
        print(ex)
        sftp.close()
        ssh.close()
        return -1

    sftp.close()
    ssh.close()


def generate_exclude_trie():
    trie = {}
    for name in exclude:
        if not isinstance(name, str):
            raise TypeError
        node = trie
        for char in name:
            node = node.setdefault(char, {})
        node['FLAG'] = True
    return trie


def is_in_exclude(file_name: str):
    global exclude_file_trie
    node = exclude_file_trie
    if not node:
        raise ValueError("Please initialize the trie")
    if not isinstance(file_name, str):
        raise TypeError
    for char in file_name:
        if 'FLAG' in node:
            return True
        if char not in node:
            return False
        node = node[char]
    return bool('FLAG' in node)


def traverse_folder():
    """
        travese specified folder and add all files(exclude the file in exclude list)
        to the py_files
    """
    global exclude_file_trie
    exclude_file_trie = generate_exclude_trie()
    q = deque(py_folders)
    temp = set()
    while q:
        cur_folder = q.popleft()
        content = os.walk(cur_folder)

        for prefix, _, files in content:
            if prefix == current_root_folder:
                temp |= set(files)
                continue
            prefix = prefix.replace("\\", r"/")
            folder_name = prefix.split(current_root_folder)[-1]
            if is_in_exclude(folder_name):
                continue

            for file in files:
                if is_in_exclude((file_path := folder_name + '/' + file)):
                    continue
                temp.add(file_path)
    py_files.extend(list(temp))


if __name__ == '__main__':
    run()
