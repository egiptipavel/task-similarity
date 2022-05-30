from pydantic import BaseModel


class LoginInfo(BaseModel):
    url: str
    branch: str
    path_to_file: str
