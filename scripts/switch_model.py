import re, sys, subprocess

model = sys.argv[1] if len(sys.argv) > 1 else "gemma3:4b"
conf = "/Users/leafrain/Projects/Open-LLM-VTuber/conf.yaml"

content = open(conf).read()

def replace(m):
    return m.group(1) + model + m.group(2)

new_content = re.sub(
    r"(ollama_llm:.*?model: ')[^']+(')",
    replace,
    content,
    flags=re.DOTALL
)

if new_content == content:
    print("変更なし（既に " + model + " です）")
    sys.exit(0)

open(conf, "w").write(new_content)
print("モデルを " + model + " に切り替えました")
subprocess.run(["pkill", "-f", "run_server.py"])
print("サーバー再起動中（約30秒後に自動起動します）")
