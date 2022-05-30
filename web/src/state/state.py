import os
from pathlib import Path

from web.src.models.solution import Solution


class State:

    def __init__(self):
        self.folder = "tmp"
        self.solutions = []

        # TODO delete (its only for tests)
        path_to_folder = Path(self.folder)
        if Path(self.folder).is_dir():
            self.solutions = [Solution(str(i), os.path.join(self.folder, str(i))) for i in os.listdir(path_to_folder)]

    def logged_in(self):
        return len(self.solutions) != 0

    def clear(self):
        # TODO delete self.folder contents
        self.solutions = []


state = State()


def get_state():
    return state
