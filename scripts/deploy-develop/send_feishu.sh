URL="https://open.feishu.cn/open-apis/bot/v2/hook/639524e5-d290-4749-9f09-d0f3ef4db101"

send_notify_to_feishu() {
    local title="$1"
    local text="$2"
    local headers="Content-Type: application/json"
    local data='{
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                   "title": "'师傅~"$title"'",
                    "content": [
                        [
                            {
                                "tag": "text",
                                "text": "'"$text"'"
                            }
                        ]
                    ]
                }
            }
        }
    }'
    response=$(curl -s -X POST -H "$headers" -d "$data" "$URL")
    echo "$response"
}


send_notify_to_feishu $1 $2
