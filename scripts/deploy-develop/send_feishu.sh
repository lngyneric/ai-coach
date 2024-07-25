URL="https://open.feishu.cn/open-apis/bot/v2/hook/3b7b9e11-498d-4598-b2c3-cad985d6e299"

send_notify_to_feishu() {
    local title="$1"
    local text="$2"
    local headers="Content-Type: application/json"
    local data='{
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "'"$title"'",
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
