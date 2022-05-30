import concurrent.futures
import os
import subprocess
from typing import Tuple, List

import requests

from web.src.models.solution import Solution


class ParseException(Exception):
    pass


def parse_url(url: str, prefix: str | None):
    if prefix and not url.startswith(prefix):
        raise ParseException(f"URL must start with '{prefix}'")
    url_without_prefix = url.replace(prefix, "", 1)
    splitted = url_without_prefix.split("/")
    if len(splitted) != 2:
        raise ParseException("Invalid URL")
    return splitted


def check_user_found(username: str) -> bool:
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url=url)
    return response.status_code == 200


def check_repository_found(username: str, repository_name: str) -> bool:
    url = f"https://api.github.com/repos/{username}/{repository_name}"
    response = requests.get(url=url)
    return response.status_code == 200


def get_forks_information(username: str, repository_name: str) -> requests.Response:
    url = f"https://api.github.com/repos/{username}/{repository_name}/forks"
    response = requests.get(url=url)
    if response.status_code != 200:
        raise requests.exceptions.RequestException("Error getting information about forks")
    return response


def download_repository(owner: str, fork_url: str, branch: str, folder: str) -> Tuple[int, str, str]:
    path = os.path.join(folder, owner)

    env = os.environ.copy()
    proc = subprocess.run(
        f"git clone {fork_url} {path} -b {branch}", shell=True, text=True,
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

    return proc.returncode, owner, path


def download_solutions(username: str,
                       repository_name: str,
                       branch: str = "master",
                       folder: str = "tmp") -> List[Solution]:
    try:
        response = get_forks_information(username, repository_name)
    except requests.exceptions.RequestException as exception:
        if not check_user_found(username):
            raise requests.exceptions.RequestException("User with such username does not found")

        if not check_repository_found(username, repository_name):
            raise requests.exceptions.RequestException("Repository with such name does not found")

        raise exception

    try:
        json_response = response.json()
        if not isinstance(json_response, list):
            raise requests.exceptions.RequestException(f"Expected type 'List', got {type(json_response)}")

        forks = []
        for fork in json_response:
            try:
                forks.append([fork['owner']['login'], fork["clone_url"]])
            except KeyError:
                pass  # TODO подумать как обрабатывать такой случай

        with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(download_repository, owner, fork_url, branch, folder)
                for owner, fork_url in forks
            ]

            solutions = []
            for future in concurrent.futures.as_completed(futures):
                returncode, owner, path_to_fork = future.result()
                if returncode == 0:
                    solutions.append(Solution(owner, path_to_fork))
            return solutions
    except requests.exceptions.JSONDecodeError:
        raise requests.exceptions.RequestException("JSON decoding error")
