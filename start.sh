#!/bin/bash

cd /home/awe/ai-assistant
source .venv/bin/activate

exec python chat.py
chmod +x /home/awe/ai-assistant/start.sh
