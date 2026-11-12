import hashlib
import json
import os
import re
import sys
import time
from getpass import getpass
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

BASE = "https://api.supadata.ai/v1"
CACHE = Path(".transcript_cache")
TTL = 30 * 24 * 60 * 60


def api_get(key, path, params=None):
    url = BASE + path + ("?" + urlencode(params) if params else "")
    request = Request(url, headers={"x-api-key": key})
    try:
        with urlopen(request, timeout=30) as response:
            status, body = response.status, json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"Supadata returned HTTP {error.code}.") from error
    if status not in (200, 202) or body.get("error"):
        raise RuntimeError(body.get("message", f"HTTP {status}"))
    return body


def validate(body):
    segments = body.get("content")
    if not isinstance(segments, list) or not segments:
        raise ValueError("No timestamped transcript was returned.")
    for segment in segments:
        if not isinstance(segment.get("text"), str):
            raise ValueError("A transcript segment has no text.")
        if not isinstance(segment.get("offset"), (int, float)):
            raise ValueError("A transcript segment has no numeric timestamp.")
        if segment["offset"] < 0:
            raise ValueError("A transcript timestamp is negative.")
    return body


def get_transcript(key, video_url):
    parsed = urlsplit(video_url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"
    }:
        raise ValueError("Please enter a public HTTPS YouTube URL.")
    params = {"url": video_url, "lang": "en",
              "mode": "native", "text": "false"}
    digest = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
    cache_file = CACHE / f"{digest}.json"
    if cache_file.exists() and time.time() - cache_file.stat().st_mtime < TTL:
        try:
            return validate(json.loads(cache_file.read_text(encoding="utf-8")))
        except (ValueError, TypeError, AttributeError):
            pass
    body = api_get(key, "/transcript", params)
    if body.get("jobId"):
        path = "/transcript/" + quote(str(body["jobId"]), safe="")
        for _ in range(30):
            time.sleep(2)
            body = api_get(key, path)
            if body.get("status") == "completed":
                break
            if body.get("status") == "failed":
                raise RuntimeError("The transcript job failed.")
        else:
            raise RuntimeError("The transcript job has not finished yet.")
    validate(body)
    CACHE.mkdir(exist_ok=True)
    cache_file.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    return body


def timestamp(milliseconds):
    seconds = int(milliseconds // 1000)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def comparison_section(label, body, keyword):
    segments = sorted(body["content"], key=lambda part: part["offset"])
    pattern = re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)
    match = next((part for part in segments if pattern.search(part["text"])), None)
    first = timestamp(match["offset"]) if match else "Not found"
    lines = [f"## {label}", f"Transcript language: {body.get('lang', 'unknown')}",
             f"First matching segment for '{keyword}': {first}",
             "Segments starting in the first 60 seconds:"]
    opening = [part for part in segments if part["offset"] < 60000]
    lines.extend(f"- {timestamp(part['offset'])} | {part['text']}" for part in opening)
    if not opening:
        lines.append("- No transcript segments start in this window.")
    return "\n".join(lines)


def main():
    if sys.argv[1:] == ["--demo"]:
        keyword = "mortgage"
        videos = [
            ("Background-first opening", {"lang": "en", "content": [
                {"offset": 0, "text": "Welcome back. Let me start with some background."},
                {"offset": 30000, "text": "A mortgage rate change affects your monthly payment."}
            ]}),
            ("Direct opening", {"lang": "en", "content": [
                {"offset": 0, "text": "A mortgage rate change affects your monthly payment."},
                {"offset": 12000, "text": "Here is a simple example of the difference."}
            ]})
        ]
        heading = "# Transcript comparison: synthetic demo"
    else:
        if sys.argv[1:]:
            raise ValueError("Run with no arguments, or use --demo.")
        urls = [input("First YouTube URL: ").strip(), input("Second YouTube URL: ").strip()]
        keyword = input("Topic keyword or phrase: ").strip()
        if not keyword:
            raise ValueError("Enter a keyword or phrase to compare.")
        key = (os.environ.get("SUPADATA_API_KEY") or getpass("Supadata API key: ")).strip()
        if not key:
            raise ValueError("A Supadata API key is required.")
        videos = [(f"Video {i}: {url}", get_transcript(key, url))
                  for i, url in enumerate(urls, start=1)]
        heading = "# Transcript comparison"
    report = heading + "\n\n" + "\n\n".join(
        comparison_section(label, body, keyword) for label, body in videos
    ) + "\n"
    Path("comparison.md").write_text(report, encoding="utf-8")
    print(report)
    print("Saved comparison.md")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        sys.exit(f"Error: {error}")
