# 真夜中のノイ / Noi VTuber

AI VTuber「真夜中のノイ」のセットアップファイル一式。  
[Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) をベースに、ノイ固有のカスタマイズを加えたもの。

## キャラクター
- **名前:** 真夜中のノイ（愛称：ノイ）
- **声:** VOICEVOX 春日部つむぎ
- **LLM:** gemma3:4b（ローカル・Ollama）
- **路線:** ニューロサマ路線（暴走・予測不能）日本語版
- **口癖:** 「メモリします」「メモリされてない！！」

## 環境
- Mac mini M4 16GB
- [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) v1.2.1
- [VOICEVOX](https://voicevox.hiroshiba.jp/) (macOS)
- Ollama + gemma3:4b

## ファイル構成
```
conf.yaml              # ノイのキャラクター・TTS・LLM設定
model_dict.json        # Live2Dモデル登録（noi）
patches/
  voicevox_tts.py      # VOICEVOXカスタムTTSエンジン
  tts_factory.py       # voicevox_ttsを追加したファクトリー
  tts_config.py        # VoicevoxTTSConfigを追加した設定ファイル
scripts/
  start_vtuber.sh      # 起動スクリプト（VOICEVOX待機→サーバー起動）
  switch_model.py      # LLMモデル切り替えスクリプト
  com.leafrain.llmvtuber.plist  # macOS LaunchAgent（自動起動）
```

## セットアップ手順

### 1. Open-LLM-VTuberをインストール
```bash
git clone https://github.com/Open-LLM-VTuber/Open-LLM-VTuber
cd Open-LLM-VTuber
uv sync
```

### 2. patchesのファイルをコピー
```bash
cp patches/voicevox_tts.py src/open_llm_vtuber/tts/
cp patches/tts_factory.py src/open_llm_vtuber/tts/
cp patches/tts_config.py src/open_llm_vtuber/config_manager/tts.py
cp conf.yaml .
cp model_dict.json .
```

### 3. VOICEVOXをインストール・起動
[VOICEVOX公式](https://voicevox.hiroshiba.jp/) からダウンロード。

### 4. Ollamaでgemma3:4bをダウンロード
```bash
ollama pull gemma3:4b
```

### 5. サーバー起動
```bash
uv run run_server.py
```

### 自動起動設定（macOS）
```bash
cp scripts/start_vtuber.sh ~/start_vtuber.sh
chmod +x ~/start_vtuber.sh
cp scripts/com.leafrain.llmvtuber.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.leafrain.llmvtuber.plist
```

### モデル切り替え
```bash
# 予備モデルに切り替え
python3 ~/switch_model.py qwen3:4b

# gemma3に戻す
python3 ~/switch_model.py gemma3:4b
```

## アクセス方法（Safari + マイク）
SafariはHTTPでマイクを使えないため、SSHトンネル経由でlocalhostとしてアクセスする。

```bash
ssh -i ~/.ssh/id_ed25519 -L 12393:localhost:12393 leafrain@192.168.1.15 -N
```

その後 `http://localhost:12393` をSafariで開く。
