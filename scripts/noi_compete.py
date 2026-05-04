"""
競合分析エージェント（noi_compete.py）
毎朝3時に実行。AI VTuberのトレンドをYouTubeで調査し、
ノイの話題リストをDeepSeekで生成してファイルに保存する。
"""
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

ENV_PATH = Path("/Users/leafrain/Projects/Open-LLM-VTuber/.env")
LOG_PATH = Path("/Users/leafrain/noi_compete.log")
TRENDS_PATH = Path("/Users/leafrain/Projects/Open-LLM-VTuber/noi_trends.md")
COMPETE_LOG_DIR = Path("/Users/leafrain/Projects/Open-LLM-VTuber/compete_log")
YTDLP = Path("/Users/leafrain/Library/Python/3.9/bin/yt-dlp")

SEARCH_QUERIES = [
    "AI VTuber 2025",
    "AITuber 配信",
    "AIVtuber 日本語",
    "VTuber AI 自動配信",
]


def load_env():
    for line in ENV_PATH.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def search_youtube(query, max_results=5):
    try:
        result = subprocess.run(
            [
                str(YTDLP),
                f"ytsearch{max_results}:{query}",
                "--dump-json",
                "--flat-playlist",
                "--no-warnings",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        videos = []
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            try:
                v = json.loads(line)
                videos.append({
                    "title": v.get("title", ""),
                    "channel": v.get("channel", "") or v.get("uploader", ""),
                    "views": v.get("view_count", 0),
                    "duration": v.get("duration_string", ""),
                    "query": query,
                })
            except json.JSONDecodeError:
                continue
        return videos
    except Exception as e:
        log(f"YouTube検索エラー ({query}): {e}")
        return []


def call_deepseek(prompt):
    import urllib.request
    api_key = os.environ["DEEPSEEK_API_KEY"]
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        result = json.loads(r.read())
    return result["choices"][0]["message"]["content"].strip()


def collect_videos():
    all_videos = []
    seen_titles = set()
    for q in SEARCH_QUERIES:
        log(f"検索中: {q}")
        videos = search_youtube(q, max_results=5)
        for v in videos:
            if v["title"] not in seen_titles:
                seen_titles.add(v["title"])
                all_videos.append(v)
        log(f"  → {len(videos)}件取得")
    return all_videos


def analyze_trends(videos):
    video_text = ""
    for i, v in enumerate(videos[:20]):
        views = f"{v['views']:,}" if isinstance(v['views'], int) else str(v['views'])
        video_text += f"{i+1}. 【{v['title']}】\n"
        video_text += f"   ch: {v['channel']} / 再生: {views} / {v['duration']}\n"

    prompt = f"""あなたはAI VTuber「真夜中のノイ」のコンテンツ戦略アドバイザーです。
今週のYouTube上のAI VTuber関連動画を分析してください。

【収集した動画一覧】
{video_text}

以下の3点を日本語で回答してください：
1. 今週のAI VTuberシーンで流行っている話題・フォーマット（上位3つ）
2. ノイが取り入れられそうな要素（ノイのキャラ：ネット雑学好き・古いボカロ・記憶が消える・暴走型・日本語のみ）
3. ノイが今週話すべきおすすめトピック5個（具体的に・日本語）"""

    return call_deepseek(prompt)


def save_trends(analysis, videos, today):
    COMPETE_LOG_DIR.mkdir(exist_ok=True)
    log_entry = {
        "date": today,
        "videos_collected": len(videos),
        "videos": videos,
        "analysis": analysis,
    }
    (COMPETE_LOG_DIR / f"{today}.json").write_text(
        json.dumps(log_entry, ensure_ascii=False, indent=2)
    )

    # noi_evolve.pyが参照するトレンドファイル
    content = f"""# ノイの今週のトレンドネタ（{today}更新）

{analysis}

---
*競合分析エージェント自動生成 / noi_compete.py*
"""
    TRENDS_PATH.write_text(content)
    log(f"トレンドファイル更新: {TRENDS_PATH}")


def main():
    load_env()
    today = datetime.now().strftime("%Y-%m-%d")
    log(f"=== 競合分析エージェント開始 {today} ===")

    videos = collect_videos()
    log(f"合計 {len(videos)} 件の動画を収集（重複除去済み）")

    if not videos:
        log("動画取得0件 → スキップ")
        return

    log("DeepSeekでトレンド分析中...")
    analysis = analyze_trends(videos)
    log(f"分析完了:\n{analysis}")

    save_trends(analysis, videos, today)
    log("=== 完了 ===")


if __name__ == "__main__":
    main()
