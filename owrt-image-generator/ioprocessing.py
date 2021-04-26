import logging
import os
import subprocess

from typing import List

def pull_repo(build_dir: str, repo: str, branch: str, extra_feeds: List[str]) -> str:
    abs_build_dir: str = os.path.abspath(build_dir)
    os.makedirs(abs_build_dir, exist_ok=True)

    logging.info("Cloning git repo")
    results = subprocess.run(["sh", "-c", "cd {} ; git clone {} base_repo".format(abs_build_dir, repo)], capture_output=True)
    logging.debug(results.stdout.decode())
    logging.debug(results.stderr.decode())
    if results.returncode != 0:
        logging.fatal("Failed to clone openwrt repository from {}.".format(repo))
        exit(1)

    logging.info("checking out branch")
    repo_path: str = os.path.join(abs_build_dir, "base_repo")
    results = subprocess.run(["sh", "-c", "cd {}; git checkout {}".format(repo_path, branch), ], capture_output=True)
    logging.debug(results.stdout.decode())
    logging.debug(results.stderr.decode())
    if results.returncode != 0:
        logging.fatal("Failed to checkout requested branch '{}'. Does it exist?".format(branch))
        exit(1)

    logging.info("Configuring feeds...")
    with open(os.path.join(repo_path, "feeds.conf"), "a") as f:
        for extra_feed in extra_feeds:
            f.write(extra_feed + "\n")
        with open(os.path.join(repo_path, "feeds.conf.default")) as default_file:
            f.write(default_file.read())

    logging.info("Fetching feeds...")
    results = subprocess.run(["sh", "-c", "cd {} ; ./scripts/feeds update -a".format(repo_path)], capture_output=True)
    logging.debug(results.stdout.decode())
    logging.debug(results.stderr.decode())
    if results.returncode != 0:
        logging.fatal("Failed to fetch OpenWRT feeds")
        exit(1)

    logging.info("Fetching feeds...")
    results = subprocess.run(["sh", "-c", "cd {}; ./scripts/feeds install -a".format(repo_path)], capture_output=True)
    logging.debug(results.stdout.decode())
    logging.debug(results.stderr.decode())
    if results.returncode != 0:
        logging.fatal("Failed to install OpenWRT feeds")
        exit(1)

    logging.info("Successfully fetched repo to {}.".format(repo_path))
    return repo_path