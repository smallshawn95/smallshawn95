#!/usr/bin/env python3
"""Adapt a pinned waka-readme-stats checkout to use Wakapi Basic auth."""
from pathlib import Path
import sys


def replace_once(text, old, new, name):
    if text.count(old) != 1:
        raise ValueError(f"Unexpected upstream {name}; refusing to patch")
    return text.replace(old, new, 1)


def main(root):
    action_path = root / "action.yml"
    manager_path = root / "sources" / "manager_download.py"
    action = action_path.read_text(encoding="utf-8")
    manager = manager_path.read_text(encoding="utf-8")

    action = replace_once(action, "image: 'docker://wakareadmestats/waka-readme-stats:master'", "image: 'Dockerfile'", "image")
    for resource in ("waka_latest", "waka_all"):
        suffix = "last_7_days" if resource == "waka_latest" else "all_time"
        old = f'{resource}=f"{{EM.WAKATIME_API_URL}}users/current/stats/{suffix}?api_key={{EM.WAKATIME_API_KEY}}",'
        new = f'{resource}=f"{{EM.WAKATIME_API_URL}}users/current/stats/{suffix}",'
        manager = replace_once(manager, old, new, resource)

    old = '            DownloadManager._REMOTE_RESOURCES_CACHE[resource] = asyncio.create_task(DownloadManager._client.get(url))'
    new = '''            headers = {}
            if resource in {"waka_latest", "waka_all"}:
                from base64 import b64encode
                token = b64encode(EM.WAKATIME_API_KEY.encode("utf-8")).decode("ascii")
                headers["Authorization"] = "Basic " + token
            DownloadManager._REMOTE_RESOURCES_CACHE[resource] = asyncio.create_task(
                DownloadManager._client.get(url, headers=headers)
            )'''
    manager = replace_once(manager, old, new, "download manager")
    if "?api_key={EM.WAKATIME_API_KEY}" in manager:
        raise ValueError("Unpatched API key in URL")

    action_path.write_text(action, encoding="utf-8")
    manager_path.write_text(manager, encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
