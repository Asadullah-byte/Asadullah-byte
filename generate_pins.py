import os, re, requests
from collections import defaultdict

USER  = os.environ["GH_USER"]
TOKEN = os.environ["GH_TOKEN"]

headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

# Collect push events
counts = defaultdict(int)
for page in range(1, 11):
    r = requests.get(
        f"https://api.github.com/users/{USER}/events",
        headers=headers,
        params={"per_page": 100, "page": page},
    )
    data = r.json()
    if not data or not isinstance(data, list):
        break
    for event in data:
        if event.get("type") == "PushEvent":
            repo = event["repo"]["name"]
            counts[repo] += event["payload"].get("distinct_size", 1)

print("Push event counts:", dict(counts))

# Pick top 2 (skip profile repo)
top = sorted(
    [(repo, c) for repo, c in counts.items() if not repo.endswith(f"/{USER}")],
    key=lambda x: x[1], reverse=True
)[:2]

# Fallback: if no push events found, use most recently pushed public repos
if not top:
    print("No push events found, falling back to recently updated repos...")
    r = requests.get(
        f"https://api.github.com/users/{USER}/repos",
        headers=headers,
        params={"per_page": 10, "sort": "pushed", "type": "all"},
    )
    repos = r.json()
    top = [
        (repo["full_name"], 0)
        for repo in repos
        if not repo["full_name"].endswith(f"/{USER}") and not repo["fork"]
    ][:2]

print("Top repos selected:", [r for r, _ in top])

def pin_badge(repo_full):
    owner, name = repo_full.split("/")
    # Use gh-readme-stats alternative instance
    img = (
        f"https://gh-readme-stats-delta.vercel.app/api/pin/"
        f"?username={owner}&repo={name}"
        f"&border_color=7F3FBF&bg_color=0D1117"
        f"&title_color=C9D1D9&text_color=8B949E&icon_color=7F3FBF"
        f"&show_owner=true"
    )
    url = f"https://github.com/{repo_full}"
    return f'<a href="{url}"><img src="{img}" width="400" /></a>'

# Build the block — cards side by side with a small gap
new_block = "<!-- TOP-REPOS-START -->\n"
new_block += "\n".join(pin_badge(r) for r, _ in top) + "\n"
new_block += "<!-- TOP-REPOS-END -->"

readme = open("README.md").read()
readme = re.sub(
    r"<!-- TOP-REPOS-START -->.*?<!-- TOP-REPOS-END -->",
    new_block,
    readme,
    flags=re.DOTALL,
)
open("README.md", "w").write(readme)
print("Done.")
