import os
import re
from difflib import SequenceMatcher
from typing import List

from web.src.models.solution import Solution


def get_file_content(path):
    with open(path, encoding="utf-8") as file:
        return file.readlines()


def to_fixed(numObj, digits=0):
    return f"{numObj:.{digits}f}"


def create_comparison_table(solutions: List[Solution], path_to_file: str):
    comparison_table = [[""] + list(map(lambda solution: solution.owner, solutions))]
    sequence_matcher = SequenceMatcher()
    regex_to_remove_comments = r'[\t\s]*--.*\n'
    for row_num, first_solution in enumerate(solutions):
        row = [first_solution.owner]
        first_path = os.path.join(first_solution.folder_with_solution, path_to_file)
        first_solution_content = get_file_content(first_path)
        first_solution_content = [re.sub(regex_to_remove_comments, '\n', line) for line in first_solution_content]
        sequence_matcher.set_seq1(first_solution_content)
        for col_num, second_solution in enumerate(solutions):
            if row_num == col_num:
                row.append("")
                continue
            second_path = os.path.join(second_solution.folder_with_solution, path_to_file)
            second_solution_content = get_file_content(second_path)
            second_solution_content = [re.sub(regex_to_remove_comments, '\n', line) for line in second_solution_content]
            sequence_matcher.set_seq2(second_solution_content)
            row.append(to_fixed(sequence_matcher.ratio(), digits=2))
        comparison_table.append(row)
    return comparison_table
