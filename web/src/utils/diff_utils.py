import os
import re
from difflib import SequenceMatcher
from typing import List

from jellyfish import hamming_distance, match_rating_comparison, jaro_winkler_similarity
from jellyfish import levenshtein_distance, damerau_levenshtein_distance, jaro_similarity
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from web.src.models.solution import Solution

regex_to_remove_comment = r'{-[^}]*-}|[\t\s]*--[^\n]*'
regex_to_remove_unnecessary_spaces = r'[^\S\r\n\t]{2,}'
regex_to_remove_unnecessary_tabs = r'\t+'
regex_to_remove_words_in_quotes = r'"[^"]*"|\'.*\''


def get_file_content(path):
    with open(path, encoding="utf-8") as file:
        return file.readlines()


def to_fixed(numObj, digits=0):
    return f"{numObj:.{digits}f}"


def clean_solution_content(solution_content: str) -> str:
    solution_content = re.sub(pattern=regex_to_remove_comment, repl='', string=solution_content)
    solution_content = re.sub(pattern=regex_to_remove_unnecessary_tabs, repl=' ', string=solution_content)
    solution_content = re.sub(pattern=regex_to_remove_unnecessary_spaces, repl=' ', string=solution_content)
    solution_content = '\n'.join([line.strip() for line in solution_content.split('\n') if line.strip() != ''])
    return solution_content


def python_diff(from_text: str, to_text: str):
    clean_texts = [clean_solution_content(from_text).split('\n'), clean_solution_content(to_text).split('\n')]
    return SequenceMatcher(a=clean_texts[0], b=clean_texts[1]).ratio()


def create_comparison_table(solutions: List[Solution], path_to_file: str, comparison_method):
    table = [[""] + list(map(lambda solution: solution.owner, solutions))]
    for row_num, first_solution in enumerate(solutions):
        row = [first_solution.owner]
        first_path = os.path.join(first_solution.folder_with_solution, path_to_file)
        first_solution_content = clean_solution_content(''.join(get_file_content(first_path)))
        for col_num, second_solution in enumerate(solutions):
            if row_num == col_num:
                row.append("")
                continue
            second_path = os.path.join(second_solution.folder_with_solution, path_to_file)
            second_solution_content = clean_solution_content(''.join(get_file_content(second_path)))
            row.append(to_fixed(comparison_method(first_solution_content, second_solution_content), digits=2))
        table.append(row)
    return table


def create_similarity_table(solutions: List[Solution], path_to_file: str):
    def comparison_method(from_text: str, to_text: str):
        return SequenceMatcher(a=from_text.split('\n'), b=to_text.split('\n')).ratio()

    return create_comparison_table(solutions, path_to_file, comparison_method)


def create_cosine_similarity_table(solutions: List[Solution], path_to_file: str):
    def cosine_sim(from_text: str, to_text: str):
        clean_texts = [clean_solution_content(from_text), clean_solution_content(to_text)]
        vectorizer = CountVectorizer().fit_transform(clean_texts)
        vectors = vectorizer.toarray()
        return cosine_similarity(vectors)[0][1]

    return create_comparison_table(solutions, path_to_file, cosine_sim)


def create_levenshtein_dist_table(solutions: List[Solution], path_to_file: str):
    return create_comparison_table(solutions, path_to_file, levenshtein_distance)


def create_damerau_levenshtein_dist_table(solutions: List[Solution], path_to_file: str):
    return create_comparison_table(solutions, path_to_file, damerau_levenshtein_distance)


def create_jaro_sim_table(solutions: List[Solution], path_to_file: str):
    return create_comparison_table(solutions, path_to_file, jaro_similarity)


def create_jaro_winkler_sim_table(solutions: List[Solution], path_to_file: str):
    return create_comparison_table(solutions, path_to_file, jaro_winkler_similarity)


def create_match_rating_cmp_table(solutions: List[Solution], path_to_file: str):
    return create_comparison_table(solutions, path_to_file, match_rating_comparison)


def create_hamming_dist_table(solutions: List[Solution], path_to_file: str):
    return create_comparison_table(solutions, path_to_file, hamming_distance)
