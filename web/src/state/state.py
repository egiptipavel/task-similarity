import os
import shutil
from pathlib import Path

from web.src.models.login_info import LoginInfo
from web.src.utils.fork_utils import parse_url, download_solutions


class State:

    def __init__(self):
        self.folder = "tmp"
        path_to_folder = Path(self.folder)
        if path_to_folder.exists():
            shutil.rmtree(path_to_folder, ignore_errors=True)
        self.path_to_file = ""
        self.solutions = []

        self.logged_in = False

    def login(self, login_info: LoginInfo):
        path_to_folder = Path(self.folder)
        if not path_to_folder.exists():
            path_to_folder.mkdir()
        username, repository_name = parse_url(login_info.url, "https://github.com/")
        solutions = download_solutions(username, repository_name, login_info.branch, state.folder)
        self.path_to_file = login_info.path_to_file
        self.solutions = list(
            filter(
                lambda s: Path(os.path.join(s.folder_with_solution, self.path_to_file)).is_file(),
                solutions
            )
        )
        self.logged_in = True

    def is_authenticated(self):
        return self.logged_in

    def clear(self):
        shutil.rmtree(self.folder, ignore_errors=True)
        self.solutions = []
        self.logged_in = False


state = State()


def get_state():
    return state
