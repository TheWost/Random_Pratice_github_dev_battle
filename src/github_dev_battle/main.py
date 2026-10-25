import asyncio

import httpx
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="src/github_dev_battle/templates")

app.mount(
    path="/static",
    app=StaticFiles(directory="src/github_dev_battle/static"),
    name="static",
)

battles = []


@app.get("/clear")
def clear():
    battles.clear()


@app.get("/history")
def history(request: Request):
    return templates.TemplateResponse(
        request=request, name="history.html", context={"battles": battles}
    )


@app.get("/")
def recent_battle(request: Request, error: str | None = None):
    battle = battles[-1] if battles else None
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"battle": battle, "error_msg": error},
    )


async def fetch_data(url, client):
    response = await client.get(url)
    response.raise_for_status()
    return response.json()


def get_github_repo_api_url(user: str, per_page: int = 100):
    return f"https://api.github.com/users/{user}/repos?per_page={per_page}"


def get_github_user_api_url(user: str):
    return f"https://api.github.com/users/{user}"


def calculate_user_stats(profile: dict, repos: list) -> dict:
    stargaze_count = 0

    lang_count = {}

    for repo in repos:
        stargaze_count += repo["stargazers_count"]

        lang = repo["language"]
        if lang:
            lang_count[lang] = lang_count.get(repo["language"], 0) + 1

    if lang_count:
        top_lang = max(lang_count, key=lang_count.get)
    else:
        top_lang = None

    score = (stargaze_count * 3) + (profile["followers"] * 2) + profile["public_repos"]

    return {
        "username": profile["login"],
        "followers": profile["followers"],
        "repos": profile["public_repos"],
        "stars": stargaze_count,
        "top_lang": top_lang,
        "score": score,
    }


def _build_battle_result(winner, loser, user1, user2):
    return {
        "winner": winner,
        "loser": loser,
        "winner_score": winner["score"],
        "loser_score": loser["score"],
        "user1": user1,
        "user2": user2,
        "tie": False,
    }


def get_battle_results(user1, user2):
    if user1["score"] > user2["score"]:
        return _build_battle_result(winner=user1, loser=user2, user1=user1, user2=user2)

    elif user1["score"] < user2["score"]:
        return _build_battle_result(winner=user2, loser=user1, user1=user1, user2=user2)

    else:
        return {
            "winner": None,
            "loser": None,
            "winner_score": user1["score"],
            "loser_score": user2["score"],
            "user1": user1,
            "user2": user2,
            "tie": True,
        }


@app.post("/battle")
async def battle(user1: str = Form(...), user2: str = Form(...)):
    urls = [
        get_github_user_api_url(user1),
        get_github_repo_api_url(user1),
        get_github_user_api_url(user2),
        get_github_repo_api_url(user2),
    ]

    async with httpx.AsyncClient() as client:
        try:
            u1_profile, u1_repos, u2_profile, u2_repos = await asyncio.gather(
                *[fetch_data(url, client) for url in urls]
            )

        except httpx.HTTPStatusError:
            print("nya")
            return RedirectResponse(url="/?error=User+not+found", status_code=303)

        u1_stats, u2_stats = (
            calculate_user_stats(u1_profile, u1_repos),
            calculate_user_stats(u2_profile, u2_repos),
        )

        battles.append(get_battle_results(u1_stats, u2_stats))
        print(battles[-1])

        return RedirectResponse(url="/", status_code=303)
