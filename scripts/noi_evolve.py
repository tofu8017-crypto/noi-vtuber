"""
ノイ改善エージェント（Co-Scientistループ）
会話ログをDeepSeekで分析してシステムプロンプトを自動更新する
"""
import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

CHAT_DIR = Path("/Users/leafrain/Projects/Open-LLM-VTuber/chat_history/noi_001")
CONF_PATH = Path("/Users/leafrain/Projects/Open-LLM-VTuber/conf.yaml")
LOG_PATH = Path("/Users/leafrain/noi_evolve.log")
ENV_PATH = Path("/Users/leafrain/Projects/Open-LLM-VTuber/.env")

def load_env():
    for line in ENV_PATH.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()


def load_trends():
    if TRENDS_PATH.exists():
        return TRENDS_PATH.read_text()
    return ""
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")

def load_recent_logs(hours=24):
    since = datetime.now() - timedelta(hours=hours)
    conversations = []
    for f in sorted(CHAT_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            ts_str = next((m["timestamp"] for m in data if m["role"] == "metadata"), None)
            if not ts_str:
                continue
            ts = datetime.fromisoformat(ts_str)
            if ts < since:
                continue
            turns = [m for m in data if m["role"] in ("human", "ai")]
            if turns:
                conversations.append(turns)
        except Exception:
            continue
    return conversations

def get_current_prompt():
    content = CONF_PATH.read_text()
    m = re.search(r"persona_prompt: \|\n(.*?)(?=\n  #|\n  [a-z])", content, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""

def update_prompt(new_prompt):
    content = CONF_PATH.read_text()
    indented = "\n".join("    " + line for line in new_prompt.splitlines())
    new_content = re.sub(
        r"(persona_prompt: \|\n).*?(?=\n  #|\n  [a-z])",
        r"\g<1>" + indented + "\n",
        content,
        flags=re.DOTALL
    )
    CONF_PATH.write_text(new_content)

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

def analyze(conversations, current_prompt, trends=""):
    conv_text = ""
    for i, turns in enumerate(conversations[:10]):
        conv_text += f"\n--- 会話{i+1} ---\n"
        for t in turns:
            role = "ユーザー" if t["role"] == "human" else "ノイ"
            conv_text += f"{role}: {t['content']}\n"

    trends_section = f"

【今週のAI VTuberトレンド（参考）】
{trends}" if trends else ""
    prompt = f"""あなたはAI VTuber「真夜中のノイ」の改善担当アナリストです。
以下の会話ログを分析してください。

【現在のシステムプロンプト】
{current_prompt}

【昨日の会話ログ】
{conv_text}{trends_section}

以下の3点を日本語で回答してください：
1. 良かった点（具体的に）
2. 改善が必要な点（具体的に）
3. 明日のプロンプトへの提言（具体的な修正案）"""

    return call_deepseek(prompt)

def generate_new_prompt(analysis, current_prompt):
    prompt = f"""あなたはAI VTuberのシステムプロンプト専門家です。
以下の分析結果を元に現在のプロンプトを改善してください。

【現在のプロンプト】
{current_prompt}

【分析結果】
{analysis}

ルール：
- プロンプト本文のみ出力（説明・コメント不要）
- キャラクターの核（名前・口癖・マスター）は変えない
- 改善点だけを小さく修正する
- 「システム」「エラー」などの機械的な言葉を使わせる指示は入れない
- 日本語で書く"""

    return call_deepseek(prompt)

def save_evolution_log(day, analysis, old_prompt, new_prompt):
    evo_dir = Path("/Users/leafrain/Projects/Open-LLM-VTuber/evolution_log")
    evo_dir.mkdir(exist_ok=True)
    entry = {
        "date": day,
        "analysis": analysis,
        "old_prompt": old_prompt,
        "new_prompt": new_prompt
    }
    (evo_dir / f"{day}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2))

def main():
    load_env()
    today = datetime.now().strftime("%Y-%m-%d")
    log(f"=== ノイ改善エージェント開始 {today} ===")

    conversations = load_recent_logs(hours=24)
    log(f"会話ログ {len(conversations)} 件を取得")

    if not conversations:
        log("会話ログなし → スキップ")
        return

    current_prompt = get_current_prompt()
    trends = load_trends()
    if trends:
        log("トレンドデータを読み込みました")
    log("DeepSeekで分析中...")
    analysis = analyze(conversations, current_prompt, trends)
    log(f"分析結果:\n{analysis}")

    log("DeepSeekで改善プロンプト生成中...")
    new_prompt = generate_new_prompt(analysis, current_prompt)
    log(f"新プロンプト生成完了（{len(new_prompt)}文字）")

    save_evolution_log(today, analysis, current_prompt, new_prompt)
    log("進化ログを保存しました")

    update_prompt(new_prompt)
    log("conf.yamlを更新しました")

    subprocess.run(["pkill", "-f", "run_server.py"])
    log("サーバー再起動を指示（30秒後に自動起動）")
    log("=== 完了 ===")

if __name__ == "__main__":
    main()
