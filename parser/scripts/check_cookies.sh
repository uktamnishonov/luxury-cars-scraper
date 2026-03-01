#!/bin/bash
# check_cookies.sh

if [ -f "cookies/headers.json" ]; then
    timestamp=$(jq -r '.timestamp' headers.json)
    timestamp=${timestamp%.*}
    current_time=$(date +%s)
    age=$((current_time - timestamp))

    if [ $age -lt 86400 ]; then
        echo "✅ Cookies свежие ($(($age / 3600))ч назад)"
        exit 0
    else
        echo "⚠️ Cookies старые ($(($age / 3600))ч назад)"
        exit 1
    fi
else
    echo "❌ headers.json не найден"
    exit 1
fi
