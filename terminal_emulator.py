# write a terminal emulator with a command line interface
# and a text editor
# in this terminal emulator, python files are used instead of exes
import os
import sys
import time
import subprocess
import yaml
import requests
import shutil
import json
import stat
from urllib.parse import urlparse
from tqdm import tqdm

build_number = 72
current_prompt = " $ "
installed_packages = []

# function to get the user's command
def get_command():
    # get the input
    command = input(os.getcwd() + current_prompt)
    # return the command
    return command

# get the current directory
terminal_location = os.getcwd()

def current_directory():
    return os.getcwd()

def get_filename(url):
    return os.path.basename(urlparse(url).path)

def online_file_exists(url):
    # check if the file exists
    try:
        r = requests.head(url)
        return r.status_code == requests.codes.ok
    except:
        return False

def download_file(url):
    # download the file from the url with a tqdm progress bar
    response = requests.get(url, stream=True)
    # set the total size of the file
    total_size_in_bytes= int(response.headers.get('content-length', 0))
    # set the block size for 1 kilobyte
    block_size = 1024
    # create a progress bar
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    # create a file to save the downloaded file
    with open(get_filename(url), 'wb') as file:
        # loop through the response
        for data in response.iter_content(block_size):
            # write the data to the file
            progress_bar.update(len(data))
            file.write(data)
    # close the progress bar
    progress_bar.close()

def get_terminal_package(url):
    # download the package
    download_file(url)
    # copy the file to the packages folder
    shutil.copy(get_filename(url), terminal_location + "\\packages\\" + get_filename(url))
    # delete the file from the current directory
    os.remove(get_filename(url))
    # check for a manifest file (without the .py extension)
    if (online_file_exists(url.replace(".py", "") + ".manifest.json")):
        # download the manifest file
        download_file(url + ".manifest.json")
        # copy the file to the packages folder
        shutil.copy(get_filename(url + ".manifest.json"), terminal_location + "\\packages\\" + get_filename(url + ".manifest.json"))
        # delete the file from the current directory
        os.remove(get_filename(url + ".manifest.json"))
        # parse the manifest file
        with open(get_filename(url + ".manifest.json"), "r") as f:
            manifest = f.read()
            # parse the file using the json module
            manifest = json.loads(manifest)
        # check if the package specifies dependencies
        if ("dependencies" in manifest):
            # value of the dependencies in the list is the minimum version
            for dependency in manifest["dependencies"]:
                # check if the dependency is already installed with the required version
                if (dependency in installed_packages):
                    # check if the installed package is the required version
                    if (installed_packages[dependency] < manifest["dependencies"][dependency]):
                        # update the installed package
                        installed_packages[dependency] = manifest["dependencies"][dependency]
        # get the package name
        package_name = manifest["name"]
        # package name with version
        package_name_version = package_name + "@" + manifest["version"]
        # open the config file using pyyaml
        with open(terminal_location + "\\.config\\config.yml", "r") as f:
            config = yaml.safe_load(f)
        # register the package as installed in the config file
        config["installed_packages"].append(package_name_version)
        # write the config file
        with open(terminal_location + "\\.config\\config.yml", "w") as f:
            yaml.safe_dump(config, f)
    else:
        # print that no manifest file was found
        print("[warning]: No manifest file found!")
        # open the config file using pyyaml
        with open(terminal_location + "\\.config\\config.yml", "r") as f:
            config = yaml.safe_load(f)
        # register the package as installed in the config file
        config["installed_packages"].append(get_filename(url).replace(".py", ""))
        # write the config file
        with open(terminal_location + "\\.config\config.yml", "w") as f:
            yaml.safe_dump(config, f)

def packman(args):
    # check if the first argument is "install"
    if (args[0] == "install"):
        # use get_terminal_package to install the package
        get_terminal_package(args[1])
    elif (args[0] == "uninstall"):
        # open the config file using pyyaml
        with open(terminal_location + "\\.config\\config.yml", "r") as f:
            config = yaml.safe_load(f)
        # check if the package is installed
        if (args[1] in config["installed_packages"]):
            # remove the package from the config file
            config["installed_packages"].remove(args[1])
            # write the config file
            with open(terminal_location + "\\.config\\config.yml", "w") as f:
                yaml.safe_dump(config, f)
            # remove file from packages folder
            # check if the py file exists
            if (os.path.isfile(terminal_location + "\\packages\\" + args[1] + ".py")):
                os.remove(terminal_location + "\\packages\\" + args[1] + ".py")
            # remove manifest file from packages folder
            # check if the manifest file exists
            if (os.path.isfile(terminal_location + "\\packages\\" + args[1] + ".manifest.json")):
                os.remove(terminal_location + "\\packages\\" + args[1] + ".manifest.json")
        else:
            print("[error]: Package not installed!")
    elif (args[0] == "list"):
        # list the installed packages
        with open(terminal_location + "\\.config\\config.yml", "r") as f:
            config = yaml.safe_load(f)
        # print the installed packages
        print("Installed packages:")
        for package in config["installed_packages"]:
            print(package)
    elif (args[0] == "update"):
        print("[warning]: Updating packages is not yet implemented!")
    elif (args[0] == "info"):
        # gets info on the package
        # check if the package is installed
        with open(terminal_location + "\\.config\\config.yml", "r") as f:
            config = yaml.safe_load(f)
        if (args[1] in config["installed_packages"]):
            # open the manifest file using json
            with open(terminal_location + "\\packages\\" + args[1] + ".manifest.json", "r") as f:
                manifest = json.load(f)
            # print the package info
            print("Package name: " + manifest["name"])
            print("Package version: " + manifest["version"])
            # check if the manifest specifies a description
            if ("description" in manifest):
                print("Description: " + manifest["description"])
            # check if the manifest specifies an author
            if ("author" in manifest):
                print("Author: " + manifest["author"])
            # check if the manifest specifies a license
            if ("license" in manifest):
                print("License: " + manifest["license"])

def list_files_in_directory(args):
    files = os.listdir()
    # print a header
    print("Files in " + current_directory() + ":")
    # check if the user supplied the -!d flag
    # the -!d flag will exclude directories
    if ("-!d" in args):
        # remove directories from the list
        files = [f for f in files if not os.path.isdir(f)]
    # check if the user supplied the -!f flag
    # the -!f flag will exclude files
    elif ("-!f" in args):
        # remove files from the list
        files = [f for f in files if os.path.isdir(f)]
    # check if the user supplied to only list one file extension
    # the -e flag will only list files with the specified extension
    elif ("-e" in args):
        # the next argument is the extension
        extension = args[args.index("-e") + 1]
        # remove files from the list that don't have the specified extension
        files = [f for f in files if f.endswith(extension)]
    # check if the user supplied to list everything except with the specified extension
    # the -!e flag will list files that don't have the specified extension
    elif ("-!e" in args):
        # the next argument is the extension
        extension = args[args.index("-!e") + 1]
        # remove files from the list that have the specified extension
        files = [f for f in files if not f.endswith(extension)]
    # check if the user supplied the -i flag
    # the -i will display info on each file such as creation date and size
    elif ("-i" in args):
        # add the headings to the list
        print("Format: filename, creation date, size")
        # print the files
        for file in files:
            # get the creation date and size of the file and print it
            print(file + ", " + str(os.path.getmtime(file)) + ", " + str(os.path.getsize(file)))
    # check if the user supplied the -sb:cd flag
    # the -sb:cd flag will sort the files by creation date
    elif ("-sb:cd" in args):
        # sort the files by creation date
        files.sort(key=lambda x: os.path.getmtime(x))
        # print the files
        for file in files:
            print(file)
    # check if the user supplied the -sb:sd flag
    # the -sb:sd flag will sort the files by size
    elif ("-sb:sd" in args):
        # sort the files by size
        files.sort(key=lambda x: os.path.getsize(x))
        # print the files
        for file in files:
            print(file)
    # check if the user supplied the -sb:a flag
    # the -sb:abc flag will sort the files by alphabetical order
    elif ("-sb:abc" in args):
        # sort the files by alphabetical order
        files.sort()
        # print the files
        for file in files:
            print(file)
    # check if the user supplied the -sb:ra flag
    # the -sb:ra flag will sort the files by reverse alphabetical order
    elif ("-sb:ra" in args):
        # sort the files by reverse alphabetical order
        files.sort(reverse=True)
        # print the files
        for file in files:
            print(file)
    # check if the user supplied the -sb:rcd flag
    # the -sb:rd flag will sort the files by reverse creation date
    elif ("-sb:rcd" in args):
        # sort the files by reverse creation date
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        # print the files
        for file in files:
            print(file)
    # check if the user supplied the -sb:rsd flag
    # the -sb:rsd flag will sort the files by reverse size
    elif ("-sb:rsd" in args):
        # sort the files by reverse size
        files.sort(key=lambda x: os.path.getsize(x), reverse=True)
        # print the files
        for file in files:
            print(file)
    # check if the user supplied the -o flag
    # the -o flag will output the files to a file
    elif ("-o" in args):
        # the next argument is the output file
        output_file = args[args.index("-o") + 1]
        # open the output file
        with open(output_file, "w") as f:
            # print the files
            for file in files:
                f.write(file + "\n")
    # check if the user supplied the -ds:hi flag
    # the -ds:hi flag will display hidden files with an asterisk
    elif ("-ds:hi" in args):
        # add the headings to the list
        print("Format: filename, an asterisk is displayed if the file is hidden")
        # print the files
        for file in files:
            # check if the file is hidden
            if (bool(os.stat(file).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)):
                # print the file with an asterisk
                print(file + "*")
            else:
                # print the file without an asterisk
                print(file)
    else:
        # print the files
        for file in files:
        # check if the file is a directory
            if (os.path.isdir(file)):
                # if it is, print a folder icon
                print("\uE5FF " + file)
            else:
                # if it is a file, check the file extension
                if (file.endswith(".txt")):
                    # if it is a text file, print a text file icon
                    print("\uf15c " + file)
                elif (file.endswith(".py")):
                    # if it is a python file, print a python file icon
                    print("\u001b[33m\ue73c " + file + "\u001b[0m")
                elif (file.endswith(".js")):
                    # if it is a javascript file, print a javascript file icon
                    print("\u001b[33m\ue781 " + file + "\u001b[0m")
                elif (file.endswith(".html")):
                    # if it is an html file, print an html file icon
                    print("\u001b[33m\ue736 " + file + "\u001b[0m")
                elif (file.endswith(".css")):
                    # if it is a css file, print a css file icon
                    print("\u001b[34m\ue749 " + file + "\u001b[0m")
                elif (file.endswith(".png")):
                    # if it is a png file, print a png file icon
                    print("\u001b[35m\uf03e " + file + "\u001b[0m")
                elif (file.endswith(".jpg")):
                    # if it is a jpg file, print a jpg file icon
                    print("\u001b[35m\uf03e " + file + "\u001b[0m")
                elif (file.endswith(".jpeg")):
                    # if it is a jpeg file, print a jpeg file icon
                    print("\u001b[35m\uf03e " + file + "\u001b[0m")
                elif (file.endswith(".gif")):
                    # if it is a gif file, print a gif file icon
                    print("\u001b[35m\uf03e " + file + "\u001b[0m")
                elif (file.endswith(".mp3")):
                    # if it is a mp3 file, print a mp3 file icon
                    print("\u001b[35m\uf1c7 " + file + "\u001b[0m")
                elif (file.endswith(".mp4")):
                    # if it is a mp4 file, print a mp4 file icon
                    print("\u001b[35m\uf1c8 " + file + "\u001b[0m")
                elif (file.endswith(".mpg")):
                    # if it is a mpg file, print a mpg file icon
                    print("\u001b[35m\uf1c8 " + file + "\u001b[0m")
                elif (file.endswith(".avi")):
                    # if it is a avi file, print a avi file icon
                    print("\u001b[35m\uf1c8 " + file + "\u001b[0m")
                elif (file.endswith(".mkv")):
                    # if it is a mkv file, print a mkv file icon
                    print("\u001b[35m\uf1c8 " + file + "\u001b[0m")
                elif (file.endswith(".mp2")):
                    # if it is a mp2 file, print a mp2 file icon
                    print("\u001b[35m\uf1c7 " + file + "\u001b[0m")
                elif (file.endswith(".mpa")):
                    # if it is a mpa file, print a mpa file icon
                    print("\u001b[35m\uf1c7 " + file + "\u001b[0m")
                elif (file.endswith(".wav")):
                    # if it is a wav file, print a wav file icon
                    print("\u001b[35m\uf1c7 " + file + "\u001b[0m")
                elif (file.endswith(".m4a")):
                    # if it is a m4a file, print a m4a file icon
                    print("\u001b[35m\uf1c7 " + file + "\u001b[0m")
                elif (file.endswith(".ogg")):
                    # if it is a ogg file, print a ogg file icon
                    print("\u001b[35m\uf1c7 " + file + "\u001b[0m")
                elif (file.endswith(".zip")):
                    # if it is a zip file, print a zip file icon
                    print("\u001b[33m\uf1c6 " + file + "\u001b[0m")
                elif (file.endswith(".rar")):
                    # if it is a rar file, print a rar file icon
                    print("\u001b[33m\uf1c6 " + file + "\u001b[0m")
                elif (file.endswith(".7z")):
                    # if it is a 7z file, print a 7z file icon
                    print("\u001b[33m\uf1c6 " + file + "\u001b[0m")
                elif (file.endswith(".tar")):
                    # if it is a tar file, print a tar file icon
                    print("\u001b[33m\uf1c6 " + file + "\u001b[0m")
                elif (file.endswith(".gz")):
                    # if it is a gz file, print a gz file icon
                    print("\u001b[33m\uf1c6 " + file + "\u001b[0m")
                elif (file.endswith(".bz2")):
                    # if it is a bz2 file, print a bz2 file icon
                    print("\u001b[33m\uf1c6 " + file + "\u001b[0m")
                elif (file.endswith(".iso")):
                    # if it is a iso file, print a iso file icon
                    print("\u001b[0m\ufaed " + file + "\u001b[0m")
                elif (file.endswith(".img")):
                    # if it is a img file, print a img file icon
                    print("\u001b[0m\uf0c7 " + file + "\u001b[0m")
                elif (file.endswith(".bin")):
                    # if it is a bin file, print a bin file icon
                    print("\u001b[32m\uf0c7 " + file + "\u001b[0m")
                elif (file.endswith(".exe")):
                    # if it is a exe file, print a exe file icon
                    print("\u001b[32m\uf0c7 " + file + "\u001b[0m")
                elif (file.endswith(".dll")):
                    # if it is a dll file, print a dll file icon
                    print("\u001b[32m\uf993 " + file + "\u001b[0m")
                elif (file.endswith(".so")):
                    # if it is a so file, print a so file icon
                    print("\u001b[32m\uf993 " + file + "\u001b[0m")
                elif (file.endswith(".deb")):
                    # if it is a deb file, print a deb file icon
                    print("\u001b[32m\uf1c6 " + file + "\u001b[0m")
                elif (file.endswith(".java")):
                    # if it is a java file, print a java file icon
                    print("\u001b[0m\ue738 " + file + "\u001b[0m")
                elif (file.endswith(".class")):
                    # if it is a class file, print a class file icon
                    print("\u001b[0m\ue738 " + file + "\u001b[0m")
                elif (file.endswith(".asm")):
                    # if it is a asm file, print a asm file icon
                    print("\u001b[0m\uf471 " + file + "\u001b[0m")
                elif (file.endswith(".o")):
                    # if it is a o file, print a o file icon
                    print("\u001b[0m\uf471 " + file + "\u001b[0m")
                elif (file.endswith(".cs")):
                    # if it is a cs file, print a cs file icon
                    print("\u001b[0m\uf81a " + file + "\u001b[0m")
                else:
                    # if it is a file, print a file icon
                    print("\u001b[0m\uf15b " + file + "\u001b[0m")

    # print a newline to make the output look nicer
    print()

# function to get the user's operating system
def get_os():
    os = sys.platform
    if os == "win32":
        return "Windows"
    elif os == "linux":
        return "Linux"
    elif os == "darwin":
        return "Mac"
    else:
        return "Unknown"

def exit_terminal_emulator():
    sys.exit()

# run a command
def run_command(command):
    if (command.startswith("cd")):
        # combine all arguments into one string
        dir = " ".join(command.split(" ")[1:])
        # check if the directory exists
        if (os.path.isdir(dir)):
            os.chdir(dir)
        else:
            print("Directory does not exist")
    elif (command.startswith("dir") or command.startswith("ls") or command.startswith("ll")):
        # get the arguments
        args = command.split(" ")
        list_files_in_directory(args)
    elif (command.startswith("cat")):
        file = command.split(" ")[1]
        with open(file) as f:
            print(f.read())
    elif (command.startswith("echo")):
        print(" ".join(command.split(" ")[1:]))
    elif (command.startswith("sleep")):
        time.sleep(float(command.split(" ")[1]))
    elif (command.startswith("clear")):
        if (get_os() == "Windows"):
            os.system("cls")
        else:
            os.system("clear")
    elif (command.startswith("help")):
        print("\ncd [directory] - change the current directory")
        print("ls, dir, ll - list the files in the current directory")
        print("cat [file] - display the contents of a file")
        print("echo [text] - display the text")
        print("sleep [seconds] - sleep for the specified number of seconds")
        print("clear - clear the screen")
        print("help - display this help message")
        print("exit - exit the terminal")
        print("about - display information about the terminal emulator")
        print("exec [command] - run a command outside of the terminal emulator")
        print("python [code] - run python code")
        print("manual [command] - display the manual for a command")
        print("edit [file] - on windows, opens notepad, and on linux & macos, opens vim")
        print("del, rm, delete, remove, rmdir, rf [file/folder] - deletes a file or folder")
        print("If a command is not on this list, it will be interpreted as a python script name\n")
    elif (command.startswith("exit")):
        exit_terminal_emulator()
    elif (command.startswith("about")):
        print("\nGithub Copilot Terminal Emulator v1.0\n")
    elif (command.startswith("exec")):
        # combine all arguments into one string
        command = " ".join(command.split(" ")[1:])
        os.system(command)
    elif (command.startswith("python")):
        # check if the user supplied an argument
        if (len(command.split(" ")) < 2):
            # run python shell
            subprocess.call(["python.exe"])
        else:
            # use the subprocess module to run user-specified code
            command = " ".join(command.split(" ")[1:])
            subprocess.call(["python", "-c", command])
    elif (command.startswith("edit")):
        # text editor
        file = " ".join(command.split(" ")[1:])
        # check the operating system
        if (get_os() == "Windows"):
            # if in windows, open in notepad
            os.system("notepad " + file)
        else:
            # if in mac or linux, clear the screen, and open in vim
            os.system("clear")
            os.system("vim " + file)
    elif (command.startswith("del") or command.startswith("rm") or command.startswith("delete") or command.startswith("remove") or command.startswith("rmdir") or command.startswith("rf")):
        # check if the file exists
        file = " ".join(command.split(" ")[1:])
        if (os.path.isfile(file)):
            # delete the file
            os.remove(file)
        # check if it is a directory
        elif (os.path.isdir(file)):
            # delete the directory
            os.rmdir(file)
        else:
            print("File does not exist")
    elif (command.startswith("packman")):
        # package manager
        # print that package manager is not fully implemented
        print("[error]: Package manager is not fully implemented")
        # packman(command.split(" ")[1:])

    elif (command.startswith("manual")):
        # check what command the user wants to get information on
        command = "".join(command.split(" ")[1:])
        if (command == "ls" or command == "dir" or command == "ll"):
            print("\nList the files in the current directory, displays a folder icon for directories and a file icon for files\n")
        elif (command == "cat"):
            print("\nDisplay the contents of a file\n")
        elif (command == "echo"):
            print("\nDisplay text in the argument\n")
        elif (command == "sleep"):
            print("\nSleep for the specified number of seconds\n")
        elif (command == "clear"):
            print("\nClear the screen\n")
        elif (command == "help"):
            print("\nDisplay a summary of all commands\n")
        elif (command == "exit"):
            print("\nExit the terminal emulator\n")
        elif (command == "about"):
            print("\nDisplay information about the terminal emulator\n")
        elif (command == "exec"):
            print("\nRun a command outside of the terminal emulator\n")
        elif (command == "python"):
            print("\nRun python code outside of the terminal emulator\n")
        elif (command == "manual"):
                print("\nDisplay information about a specific command\n")
        elif (command == "cd"):
            print("\nChange the current directory\n")
        elif (command == "edit"):
            print("\nOn windows, opens notepad, and on linux & macos, opens vim\n")
        elif (command == "del" or command == "rm" or command == "delete" or command == "remove" or command == "rmdir" or command == "rf"):
            print("\nDelete a file or folder\n")
        else:
            print("\nCommand not found\n")


    else:
        # check if the file exists
        if (os.path.isfile(command)):
            # if it does, run the file
            subprocess.call(["python", command])
        elif (os.path.isfile(command + ".py")):
            # if it does, but the user did not specify .py, run the file
            subprocess.call(["python", command + ".py"])
        # check if there was a python script in the terminal emulator directory
        elif (os.path.isfile(terminal_location + "\\packages\\" + command + ".py")):
            # if it does, run the file
            subprocess.call(["python", terminal_location + "\\packages\\" + command + ".py"])
        # case for if the user adds .py to the end of the command
        elif (os.path.isfile(terminal_location + "\\packages\\" + command)):
            subprocess.call(["python", terminal_location + "\\packages\\" + command])

        else:
            print("Unknown command")

# main loop to run the terminal emulator
def main():
    # check if config.yml exists
    if (os.path.isfile(".config\config.yml")):
        # load the file
        with open(".config\config.yml", "r") as f:
            # save it to a string
            config = f.read()
        # use it with pyyaml to load it into a dictionary
        config = yaml.safe_load(config)
        # check if the user has specified a custom prompt
        if ("prompt" in config):
            current_prompt = " " + config["prompt"] + " "
        # check if the user has specified a custom starting location
        if ("start_location" in config):
            os.chdir(config["start_location"])
        # load the installed_packages string array from the file
        if ("installed_packages" in config):
            installed_packages = config["installed_packages"]
    else:
        print("[warning]: YAML not found, creating one!")
        # create config.yml using pyyaml
        config = {}
        config["prompt"] = "$"
        # set the default starting location in the home directory
        config["start_location"] = os.path.expanduser("~")
        # add a list of strings called installed_packages to the config
        config["installed_packages"] = []
        # check if the folder .config exists
        if (os.path.isdir(".config")):
            with open(".config\config.yml", "w") as f:
                f.write(yaml.dump(config))
        else:
            os.mkdir(".config")
            with open(".config\config.yml", "w") as f:
                f.write(yaml.dump(config))
        # close the file
        f.close()
    if (get_os() == "Windows"):
        os.system("cls")
        os.system("title Github Copilot Terminal Emulator")
    else:
        os.system("clear")
    # print the welcome message in yellow (not in bold)
    print("\033[33mWelcome to the Github Copilot Terminal Emulator! [Build " + str(build_number) + "] \033[0m")
    while (True):
        command = get_command()
        run_command(command)

# call main function
if __name__ == "__main__":
    main()
