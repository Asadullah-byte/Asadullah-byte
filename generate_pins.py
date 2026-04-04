import os, re, requests
from collections import defaultdict

USER  = os.environ["GH_USER"]
TOKEN = os.environ["GH_TOKEN"]

headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

# Collect push events across up to 10 pages (GitHub keeps ~90 days)
counts = defaultdict(int)
for page in range(1, 11):
    r = requests.get(
        f"https://api.github.com/users/{USER}/events",
        headers=headers,
        params={"per_page": 100, "page": page},
    )
    data = r.json()
    if not data:
        break
    for event in data:
        if event.get("type") == "PushEvent":
            repo = event["repo"]["name"]          # e.g. "Asadullah-byte/my-repo"
            counts[repo] += event["payload"].get("distinct_size", 1)

# Pick top 2 (skip your profile repo itself)
top = sorted(
    [(repo, c) for repo, c in counts.items() if not repo.endswith(f"/{USER}")],
    key=lambda x: x[1], reverse=True
)[:2]

def pin_badge(repo_full):
    owner, name = repo_full.split("/")
    img = (
        f"https://github-readme-stats.vercel.app/api/pin/"
        f"?username={owner}&repo={name}"
        f"&border_color=7F3FBF&bg_color=0D1117"
        f"&title_color=C9D1D9&text_color=8B949E&icon_color=7F3FBF"
    )
    url = f"https://github.com/{repo_full}"
    return f"[![{name}]({img})]({url})"

new_block = "<!-- TOP-REPOS-START -->\n"
new_block += "  ".join(pin_badge(r) for r, _ in top) + "\n"
new_block += "<!-- TOP-REPOS-END -->"

readme = open("README.md").read()
readme = re.sub(
    r"<!-- TOP-REPOS-START -->.*?<!-- TOP-REPOS-END -->",
    new_block,
    readme,
    flags=re.DOTALL,
)
open("README.md", "w").write(readme)
print("Updated pins:", [r for r, _ in top])
