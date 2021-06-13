import argparse
import logging
import os
import shutil
import sys

from multiprocessing import Pool

from config import load_config, merge_config
from image_building import build_image
from ioprocessing import pull_repo

def parse_arguments():
    parser = argparse.ArgumentParser(description="An OpenWRT image generator for the lazy ones")
    parser.add_argument("--build-directory", type=str, help="Specify the temporary build directory",
                        default="build")
    parser.add_argument("--output-directory", type=str, help="Specify the image output directory",
                        default="out")
    parser.add_argument("--config-file", type=str, help="Specify the top level configuration file",
                        default="config.yml")
    parser.add_argument("--verbose", "-v", action="count", default=0,
                        help="Specify logger verbosity. Stacking more than"
                             " 5 v's won't make any further difference.")
    return parser.parse_args()


def setup_main_logger(args: argparse.Namespace):
    log_level: int = logging.FATAL
    if args.verbose == 1:
        log_level = logging.CRITICAL
    elif args.verbose == 2:
        log_level = logging.ERROR
    elif args.verbose == 3:
        log_level = logging.WARN
    elif args.verbose == 4:
        log_level = logging.INFO
    elif args.verbose > 4:
        log_level = logging.DEBUG

    # due to , encoding="utf-8" not being added prior to python39 we're obmitting it here
    file_handler = logging.FileHandler("execution.log", "w")
    file_handler.setLevel(log_level)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.WARN if args.verbose < 2 else log_level)

    logging.basicConfig(level=log_level, handlers=[file_handler, console])

def compile_set(config_set, set_id=None):
    repo = "https://github.com/openwrt/openwrt.git"
    if config_set.get("repo"):
        repo = config_set["repo"]
    
    build_directory: str = args.build_directory
    if set_id is not None:
        build_directory = os.path.join(build_directory, str(set_id))
    
    repo_path: str = pull_repo(build_directory, repo, config_set["branch"], config_set["extra_feeds"])

    task_list = []

    for template in config_set["templates"]:
        for device in config_set["devices"]:
            name, device_config = merge_config(template, device)
            logging.info("Creating build environment for {}.".format(name))
            build_path: str = os.path.join(build_directory, name)
            output_directory: str = None
            if set_id is None:
                output_directory = os.path.join(args.output_directory, name)
            else:
                output_directory = os.path.join(args.output_directory, str(set_id), name)
            shutil.copytree(repo_path, build_path)
            device_config.update({"build_dir": build_path, "out_dir": output_directory})
            logging.info("Scheduling {} for built.".format(name))
            task_list.append(device_config)
    
    logging.info("Starting compiling.")
    with Pool() as p:
        for name, success in p.map(build_image, task_list):
            if success:
                logging.info("Successfully compiled image {}.".format(name))
            else:
                logging.info("Failed to compile image {}.".format(name))

args = parse_arguments()
setup_main_logger(args)
config = load_config(args.config_file)

if isinstance(config, list):
    logging.info("Found multiple config sets.")
    i: int = 0
    for c_set in config:
        logging.info("Compiling set for " + str(c_set["branch"]))
        compile_set(c_set, set_id=i)
        i = i + 1
else:
    compile_set(config)

logging.info("Successfully compiled images. Goodbye.")
