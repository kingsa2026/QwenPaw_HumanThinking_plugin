#!/bin/bash
echo "=== Testing HumanThinking APIs ==="

BASE_URL="http://localhost:8088/api/plugins/humanthinking"

echo "1. Stats:"
curl -s "$BASE_URL/stats"
echo ""

echo "2. Config:"
curl -s "$BASE_URL/config"
echo ""

echo "3. Emotion:"
curl -s "$BASE_URL/emotion"
echo ""

echo "4. Sessions:"
curl -s "$BASE_URL/sessions"
echo ""

echo "5. Recent Memories:"
curl -s "$BASE_URL/memories/recent"
echo ""

echo "6. Timeline:"
curl -s "$BASE_URL/memories/timeline"
echo ""

echo "7. Dreams:"
curl -s "$BASE_URL/dreams"
echo ""

echo "8. Search (POST):"
curl -s -X POST "$BASE_URL/search" -H 'Content-Type: application/json' -d '{"query":"test"}'
echo ""

echo "9. Update Config (POST):"
curl -s -X POST "$BASE_URL/config" -H 'Content-Type: application/json' -d '{"frozen_days":60}'
echo ""

echo "10. Bridge Sessions (POST):"
curl -s -X POST "$BASE_URL/sessions/bridge" -H 'Content-Type: application/json' -d '{"source_session":"s1","target_session":"s2"}'
echo ""

echo "=== All API tests completed ==="
