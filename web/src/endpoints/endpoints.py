import os.path
from typing import List, Tuple

import fastapi
import starlette
from fastapi import APIRouter, Depends, Query, Body
from fastapi.responses import HTMLResponse
from requests.exceptions import RequestException
from starlette import status
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from web.src.models.login_info import LoginInfo
from web.src.models.solution import Solution
from web.src.state.state import get_state, State
from web.src.utils.diff2HtmlCompare.diff2HtmlCompare import compare
from web.src.utils.diff_utils import create_jaro_sim_table
from web.src.utils.diff_utils import create_similarity_table, create_cosine_similarity_table
from web.src.utils.fork_utils import ParseException

router = APIRouter(prefix="")

templates = Jinja2Templates(directory="web/resources/templates")


@router.get("/")
async def root(state: State = Depends(get_state)):
    if state.is_authenticated():
        return fastapi.responses.RedirectResponse("/solutions", status_code=starlette.status.HTTP_302_FOUND)
    return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)


@router.get("/login")
async def get_login_page(request: Request, state: State = Depends(get_state)):
    if state.is_authenticated():
        return fastapi.responses.RedirectResponse("/solutions", status_code=starlette.status.HTTP_302_FOUND)
    return templates.TemplateResponse("index.html", {"request": request, "title": "Вход", "body": "login"})


@router.post("/login")
async def login(request: Request, login_info: LoginInfo, state: State = Depends(get_state)):
    try:
        state.login(login_info)
    except (ParseException or RequestException):
        return templates.TemplateResponse("index.html", {"request": request, "title": "Вход", "body": "login"})
    return fastapi.responses.JSONResponse(content="")


@router.get("/exit")
async def get_exit_page(request: Request, state: State = Depends(get_state)):
    if not state.is_authenticated():
        return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)
    return templates.TemplateResponse("index.html", {"request": request, "title": "Вход", "body": "exit"})


@router.post("/exit")
async def exit(choice: bool = Body(False, embed=True), state: State = Depends(get_state)):
    if not state.is_authenticated():
        return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)
    if choice:
        state.clear()
        return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)
    return fastapi.responses.RedirectResponse("/solutions", status_code=starlette.status.HTTP_302_FOUND)


@router.get("/solutions")
async def get_solutions(request: Request,
                        solution_numbers: list[int] = Query(default=None, alias="checkbox"),
                        state: State = Depends(get_state)):
    if not state.is_authenticated():
        return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)
    if solution_numbers and -1 in solution_numbers:
        solution_numbers.remove(-1)
    if solution_numbers and len(solution_numbers) == 2:
        solutions: List[Solution] = [state.solutions[i] for i in solution_numbers]
        first_solution = os.path.join(solutions[0].folder_with_solution, state.path_to_file)
        second_solution = os.path.join(solutions[1].folder_with_solution, state.path_to_file)
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


@router.get("/table/similarity")
async def get_similarity_table(request: Request, state: State = Depends(get_state)):
    if not state.is_authenticated():
        return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)
    if not state.similarity_table:
        state.similarity_table = create_similarity_table(state.solutions, state.path_to_file)
    similarity_table = state.similarity_table
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Вход", "body": "table", "table": similarity_table}
    )


@router.get("/table/cosine_similarity")
async def get_cosine_semantic_similarity_table(request: Request, state: State = Depends(get_state)):
    if not state.is_authenticated():
        return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)
    if not state.cosine_similarity_table:
        state.cosine_similarity_table = create_cosine_similarity_table(state.solutions, state.path_to_file)
    cosine_similarity_table = state.cosine_similarity_table
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Вход",
            "body": "table",
            "table": cosine_similarity_table
        }
    )


@router.get("/table/jaro_similatiry")
async def get_jaro_sim_table(request: Request, state: State = Depends(get_state)):
    if not state.is_authenticated():
        return fastapi.responses.RedirectResponse("/login", status_code=starlette.status.HTTP_302_FOUND)
    if not state.jaro_sim_table:
        state.jaro_sim_table = create_jaro_sim_table(state.solutions, state.path_to_file)
    jaro_sim_table = state.jaro_sim_table
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Вход",
            "body": "table",
            "table": jaro_sim_table
        }
    )
