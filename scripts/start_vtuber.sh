#!/bin/bash
cd /Users/leafrain/Projects/Open-LLM-VTuber

for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
    if curl -s http://localhost:50021/speakers > /dev/null 2>&1; then
        break
    fi
    sleep 5
done

exec /Users/leafrain/Projects/Open-LLM-VTuber/.venv/bin/python3 run_server.py
