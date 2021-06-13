import logging
import os
import subprocess

from jinja2 import Template

def render_file(content: str, name: str) -> str:
    template = Template(str(content))
    context = {
        "environment": os.environ,
        "image_name": name
    }
    return template.render(context)


def search_and_copy_binaries(search_dir: str, copy_to: str):
    def find_correct_subfolder(current_path: str):
        dir_content = os.listdir(current_path)
        further_directories = []
        for f in dir_content:
            if os.path.isdir(f):
                further_directories.append(f)
            else:
                # Check if we've got the correct directory
                if f == "config.buildinfo":
                    return True, current_path
        for d in further_directories:
            success, directory = find_correct_subfolder(os.path.join(current_path, d))
            if success:
                return True, directory
        return False, None
    
    success, directory = find_correct_subfolder(search_dir)
    if success:
        results = subprocess.run(["sh", "-c", "cp", "-r", "{}/*".format(os.path.abspath(directory)),
                                  "{}".format(os.path.abspath(copy_to))], capture_output=False)
        return results.returncode == 0
    return False


def build_image(config_dict):
    name: str = config_dict["name"]
    files = config_dict["files"]
    settings = config_dict["settings"]
    build_dir: str = os.path.abspath(config_dict["build_dir"])
    output_directory: str = os.path.abspath(config_dict["out_dir"])

    os.makedirs(output_directory, exist_ok=True)

    logging.info("Setting up files for {}.".format(name))
    files_path: str = os.path.join(build_dir, "files")
    os.makedirs(files_path, exist_ok=True)
    for f in files:
        try:
            proto_path = f["path"]
            if proto_path.startswith("/"):
                proto_path = proto_path[1:]
            f_path = os.path.join(files_path, proto_path)
            os.makedirs(os.path.dirname(f_path), exist_ok=True)
            with open(f_path, "w") as file:
                file.write(render_file(f["content"], name))
        except Exception as e:
            logging.error("Failed to setup file {} due to {}.".format(str(f), str(e)))
            return name, False

    logging.info("Creating device configuration data for {}.".format(name))
    with open(os.path.join(build_dir, ".config"), "w") as config_file:
        for setting in settings:
            config_file.write(render_file(setting, name) + "\n")

    logging.info("Unfolding device configuration")
    results = subprocess.run(["sh", "-c", "cd {} ; make defconfig >> {}/{}_build.log"
                             .format(build_dir, output_directory, name)], capture_output=True)
    if results.returncode != 0:
        logging.fatal("Failed to unfold device configuration. See errors below and within {}_build.log".format(name))
        logging.debug(results.stderr.decode())
        return name, False
    
    logging.info("Cleaning build directory")
    results = subprocess.run(["sh", "-c", "cd {} ; make clean >> {}/{}_build.log"
                             .format(build_dir, output_directory, name)], capture_output=True)
    if results.returncode != 0:
        logging.fatal("Failed to clean build directory. See errors below and within {}_build.log".format(name))
        logging.debug(results.stderr.decode())
        return name, False

    logging.info("Building device image")
    results = subprocess.run(["sh", "-c", "cd {} ; make -j1 V=s >> {}/{}_build.log"
                             .format(build_dir, output_directory, name)], capture_output=True)
    if results.returncode != 0:
        logging.fatal("Failed to build device image. See errors below and within {}_build.log".format(name))
        logging.debug(results.stderr.decode())
        return name, False
    else:
        if not search_and_copy_binaries(os.path.join(build_dir, "bin", "targets"), output_directory):
            logging.fatal("Failed to copy generated binaries. They've been build properly dough.")

    return name, True
