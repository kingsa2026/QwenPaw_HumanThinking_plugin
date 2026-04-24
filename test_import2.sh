#!/bin/bash
cd /root/.qwenpaw/plugins/HumanThinking
uv run python -c 'from prod_ui_patcher import install_human_thinking_to_qwenpaw; print("OK")'