import asyncio
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

PACKAGE_FILE = Path("package.json").resolve()
QUARANTINE_DAYS = 7
CONCURRENCY = 3

GIT_URL_PATTERN = re.compile(r"^git\+https://github\.com/([^/]+)/([^/#]+?)(?:\.git)?(?:#(.*))?$")
HEX_HASH_PATTERN = re.compile(r"^[0-9a-fA-F]{7,40}$")


def fetch_json(url):
    """
    Fetches JSON from the GitHub API.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Tree-Sitter-Wasm-Updater"
    }
    
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ.get('GITHUB_TOKEN')}"

    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):
            return None  
        raise RuntimeError(f"HTTP {e.code} for {url}")


async def check_quarantined_update(pkg_name, url, semaphore):
    """
    Checks a specific dependency for a newer commit that has passed the quarantine period.
    """
    async with semaphore:
        match = GIT_URL_PATTERN.match(url)
        if not match:
            return

        owner, repo, current_hash = match.groups()

        if not current_hash or not HEX_HASH_PATTERN.match(current_hash):
            return

        cutoff = datetime.now(timezone.utc) - timedelta(days=QUARANTINE_DAYS)
        cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?until={cutoff_str}&per_page=1"

        try:
            commits = await asyncio.to_thread(fetch_json, commits_url)
            if not commits or not isinstance(commits, list) or len(commits) == 0:
                return

            q_head_sha = commits[0]["sha"]

            if q_head_sha.lower().startswith(current_hash.lower()):
                return

            compare_url = f"https://api.github.com/repos/{owner}/{repo}/compare/{current_hash}...{q_head_sha}"
            compare_data = await asyncio.to_thread(fetch_json, compare_url)

            if compare_data and compare_data.get("status") == "ahead":
                new_url = f"git+https://github.com/{owner}/{repo}.git#{q_head_sha}"
                
                print(f"[{pkg_name}] Quarantined update available!")
                print(f"  Current:     {current_hash[:7]}")
                print(f"  Quarantined: {q_head_sha[:7]}")
                print(f"  Target URL:  {new_url}\n")

        except Exception as error:
            print(f"[{pkg_name}] Failed to check updates: {error}")


async def main():
    """
    Main application entry point.
    """
    try:
        with open(PACKAGE_FILE, "r", encoding="utf-8") as f:
            pkg = json.load(f)
    except Exception as error:
        print(f"Could not read or parse package.json: {error}")
        sys.exit(1)

    dev_deps = pkg.get("devDependencies", {})
    
    git_deps = [
        (pkg_name, version) for pkg_name, version in dev_deps.items()
        if "git+https://" in version
    ]

    if not git_deps:
        print("No git+https dependencies found in package.json.")
        return

    print(f"Checking {len(git_deps)} dependencies for updates older than {QUARANTINE_DAYS} days...\n")

    semaphore = asyncio.Semaphore(CONCURRENCY)
    
    tasks = [
        check_quarantined_update(pkg_name, version, semaphore)
        for pkg_name, version in git_deps
    ]

    await asyncio.gather(*tasks)
    
    print("Finished checking for updates.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nApplication crash: {e}")
        sys.exit(1)
