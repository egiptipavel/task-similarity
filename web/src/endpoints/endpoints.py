import os.path
from difflib import SequenceMatcher
from typing import List, Tuple

import fastapi
import starlette
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from requests.exceptions import RequestException
from starlette import status
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from web.src.models.solution import Solution
from web.src.state.state import get_state, State
from web.src.utils.diff2HtmlCompare.diff2HtmlCompare import compare
from web.src.utils.diff_utils import get_file_content
from web.src.utils.fork_utils import download_solutions, parse_url, ParseException

router = APIRouter(prefix="")

templates = Jinja2Templates(directory="web/resources/templates")


@router.get("/")
async def root(state: State = Depends(get_state)):
    if state.logged_in():
        return fastapi.responses.RedirectResponse("/solutions", status_code=starlette.status.HTTP_302_FOUND)
    return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)


@router.get("/login")
async def login(request: Request, url: str = None, branch: str = None, state: State = Depends(get_state)):
    if state.logged_in():
        return fastapi.responses.RedirectResponse("/solutions", status_code=starlette.status.HTTP_302_FOUND)
    if url and branch:
        try:
            username, repository_name = parse_url(url, "https://github.com/")
            state.solutions = download_solutions(username, repository_name, branch, state.folder)
        except (ParseException or RequestException):
            return templates.TemplateResponse("index.html", {"request": request, "title": "Вход", "body": "login"})
        return fastapi.responses.RedirectResponse("/solutions", status_code=starlette.status.HTTP_302_FOUND)
    return templates.TemplateResponse("index.html", {"request": request, "title": "Вход", "body": "login"})


@router.get("/exit")
async def exit(request: Request, choice: str = None, state: State = Depends(get_state)):
    if not state.logged_in():
        return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)
    if choice and choice == "Да":
        state.clear()
        return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)
    if choice:
        return fastapi.responses.RedirectResponse("/solutions", status_code=starlette.status.HTTP_302_FOUND)
    return templates.TemplateResponse("index.html", {"request": request, "title": "Вход", "body": "exit"})


@router.get("/solutions")
async def get_solutions(request: Request,
                        solution_numbers: list[int] = Query(default=None, alias="checkbox"),
                        state: State = Depends(get_state)):
    if not state.logged_in():
        return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)
    if solution_numbers and -1 in solution_numbers:
        solution_numbers.remove(-1)
    if solution_numbers and len(solution_numbers) == 2:
        solutions: List[Solution] = [state.solutions[i] for i in solution_numbers]
        first_solution = os.path.join(solutions[0].folder_with_solution, "task06-fp-yat", "Yat.hs")
        second_solution = os.path.join(solutions[1].folder_with_solution, "task06-fp-yat", "Yat.hs")
        diff_html = compare(
            first_solution,
            second_solution,
            solutions[0].owner,
            solutions[1].owner
        )
        return HTMLResponse(diff_html)
    solutions: List[Tuple[int, Solution]] = [(i, solution) for i, solution in enumerate(state.solutions)]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Решения студентов", "body": "solutions", "solutions": solutions}
    )


@router.get("/web/resources/css/{path}")
async def get_css_file(path: str):
    full_path = os.path.join("web", "resources", "css", path)
    return fastapi.responses.FileResponse(full_path)


@router.get("/web/resources/js/{path}")
async def get_js_file(path: str):
    full_path = os.path.join("web", "resources", "js", path)
    return fastapi.responses.FileResponse(full_path)


@router.get("/web/resources/css/codeformats/{path}")
async def get_css_codeformats_file(path: str):
    full_path = os.path.join("web", "resources", "css", "codeformats", path)
    return fastapi.responses.FileResponse(full_path)


def to_fixed(numObj, digits=0):
    return f"{numObj:.{digits}f}"


@router.get("/table")
async def get_comparison_table(request: Request, state: State = Depends(get_state)):
    if not state.logged_in():
        return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)
    comparison_table = [[""] + list(map(lambda solution: solution.owner, state.solutions))]
    sequence_matcher = SequenceMatcher()
    for row_num, first_solution in enumerate(state.solutions):
        row = [first_solution.owner]
        first_path = os.path.join(first_solution.folder_with_solution, "task06-fp-yat", "Yat.hs")
        first_solution_content = get_file_content(first_path)
        sequence_matcher.set_seq1(first_solution_content)
        for col_num, second_solution in enumerate(state.solutions):
            if row_num == col_num:
                row.append("")
                continue
            second_path = os.path.join(second_solution.folder_with_solution, "task06-fp-yat", "Yat.hs")
            second_solution_content = get_file_content(second_path)
            sequence_matcher.set_seq2(second_solution_content)
            row.append(to_fixed(sequence_matcher.ratio(), digits=2))
        comparison_table.append(row)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Вход", "body": "table", "comparison_table": comparison_table}
    )
