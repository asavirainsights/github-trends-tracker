import os, json, csv, gzip, time, requests
from datetime import date, timedelta
from pathlib import Path

TOKEN = os.environ["GITHUB_TOKEN"]
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}
URL = "https://api.github.com/search/repositories"

today = date.today().isoformat()
since = (date.today() - timedelta(days=30)).isoformat()

LANGUAGES = ["Python", "JavaScript", "TypeScript", "Java", "Go",
             "Rust", "PHP", "Kotlin", "Swift", "Ruby"]
TOPICS = ["llm", "react", "rust"]

QUERIES = {"top_overall": "stars:>1000"}
for lang in LANGUAGES:
    QUERIES[f"top_{lang}"] = f"language:{lang} stars:>500"
QUERIES["new_30d"] = f"created:>{since} stars:>50"
for t in TOPICS:
    QUERIES[f"topic_{t}"] = f"topic:{t} stars:>100"

out_dir = Path("data/raw") / today
out_dir.mkdir(parents=True, exist_ok=True)

rows = {}
for name, q in QUERIES.items():
    params = {"q": q, "sort": "stars", "order": "desc", "per_page": 100}
    r = requests.get(URL, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    with gzip.open(out_dir / f"{name}.json.gz", "wt", encoding="utf-8") as f:
        json.dump(data, f)

    for it in data["items"]:
        rows[it["id"]] = {
            "snapshot_date": today,
            "repo_id": it["id"],
            "full_name": it["full_name"],
            "language": it["language"],
            "topics": "|".join(it.get("topics", [])),
            "stars": it["stargazers_count"],
            "forks": it["forks_count"],
            "open_issues": it["open_issues_count"],
            "created_at": it["created_at"],
        }
    print(f"{name}: {len(data['items'])} repos")
    time.sleep(3)

with open(out_dir / "repos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(next(iter(rows.values())).keys()))
    w.writeheader()
    w.writerows(rows.values())

print(f"Saved {len(rows)} unique repos for {today}")