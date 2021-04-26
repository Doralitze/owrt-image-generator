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

def build_image(config_dict):
    name: str = config_dict["name"]
    files = config_dict["files"]
    settings = config_dict["settings"]
    build_dir: str = config_dict["build_dir"]
    output_directory: str = config_dict["out_dir"]

    os.makedirs(output_directory, exist_ok=True)

    logging.info("Setting up files for {}.".format(name))
    files_path: str = os.path.join(build_dir, "files")
    os.makedirs(files_path, exist_ok=True)
    for f in files:
        try:
            f_path = os.path.join(files_path, f["path"])
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

    logging.info("Building device image")
    results = subprocess.run(["sh", "-c", "cd {} ; make -j1 V=s >> {}/{}_build.log"
                             .format(build_dir, output_directory, name)], capture_output=True)
    if results.returncode != 0:
        logging.fatal("Failed to build device image. See errors below and within {}_build.log".format(name))
        logging.debug(results.stderr.decode())
        return name, False

    return name, True