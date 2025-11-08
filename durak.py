from flask import Flask, render_template, request, redirect, jsonify
import requests, os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

BASE_URL = "https://api.poiskkino.dev/v1.4"
API_TOKEN = os.getenv("API_TOKEN")

movies = {
    "to_watch": [],
    "watched": []
}


def search_movie(title, limit=5):
    """Поиск фильмов через API PoiskKino"""
    url = f"{BASE_URL}/movie/search"
    params = {"query": title, "page": 1}
    headers = {"X-API-KEY": API_TOKEN}
    r = requests.get(url, params=params, headers=headers)
    if r.status_code != 200:
        print("Ошибка API:", r.text)
        return []
    data = r.json().get("docs", [])
    results = []
    for m in data[:limit]:
        results.append({
            "id": m.get("id"),
            "title": m.get("name") or "Без названия",
            "year": m.get("year") or "—",
            "poster": m.get("poster", {}).get("url"),
        })
    return results


@app.route("/")
def index():
    watched_sorted = sorted(movies["watched"], key=lambda m: m.get("rating", 0), reverse=True)
    return render_template("index.html", movies=movies, watched_sorted=watched_sorted)


@app.route("/suggest")
def suggest():
    query = request.args.get("query", "")
    if not query.strip():
        return jsonify([])
    return jsonify(search_movie(query, limit=8))


@app.route("/add_movie", methods=["POST"])
def add_movie():
    """Добавляет фильм в список 'хочу посмотреть', если его там ещё нет"""
    data = request.json
    title = data.get("title")
    year = data.get("year")
    poster = data.get("poster")

    # Проверяем, есть ли фильм в списках
    if any(m["title"] == title for m in movies["to_watch"]):
        return jsonify({"status": "exists", "message": "Фильм уже в списке желаний"})
    if any(m["title"] == title for m in movies["watched"]):
        return jsonify({"status": "watched", "message": "Фильм уже просмотрен"})

    movies["to_watch"].append({
        "title": title,
        "year": year,
        "poster": poster
    })

    return jsonify({"status": "ok"})


@app.route("/remove_movie/<title>", methods=["POST"])
def remove_movie(title):
    movies["to_watch"] = [m for m in movies["to_watch"] if m["title"] != title]
    return jsonify({"status": "removed"})


@app.route("/watch/<title>", methods=["POST"])
def watch(title):
    rating = float(request.form.get("rating", 0))
    for m in movies["to_watch"]:
        if m["title"] == title:
            movies["to_watch"].remove(m)
            m["rating"] = rating
            movies["watched"].append(m)
            break
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
