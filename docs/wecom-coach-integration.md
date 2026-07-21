# 企业微信 + Coach 系统对接方案

## 架构

```
企业微信 → WeCom Bridge (ws) → FastClaw → Coach API (nginx)
                                         → AI-Shifu API
```

企业微信不直接调用 Coach API，通过 WeCom Bridge → FastClaw 中转。同时暴露 HTTP 回调接口供企业微信直接调用。

## 需要新增的 Nginx 路由

```nginx
# WeChat Work API 回调（用于企业微信服务器回调）
location /wecom/ {
    proxy_pass http://127.0.0.1:8800/;  # WeCom Bridge 端口
    proxy_set_header Host $host;
}
```

## Coach API 对接清单（对应 9 个节点）

| 节点 | 企业微信动作 | Coach API 端点 |
|:----:|-------------|---------------|
| 1 | 上传课件 | `POST /api/coach/courses`— 上传课件文件 |
| 2 | 录制面聊 | 企微原生能力，不调 API |
| 3 | 上传面聊总结 | `POST /api/coach/session` — 创建面谈记录 |
| 4 | 待办/完成标记 | `PUT /api/coach/tasks/{id}` — 更新任务状态 |
| 5 | 学员评分（评教练） | `POST /api/coach/learner-rating` |
| 6 | 教练评分（评学员） | `POST /api/coach/phase-summary` |
| 7 | 终评百分制 | `POST /api/coach/final-rating` |
| 8 | 上传学习凭证 | `POST /api/coach/learning-records` |
| 9 | 获取分析报告 | `GET /api/coach/report/{learner_bid}` |

## 认证方式

企业微信调用 Coach API 时使用 `X-WECOM-TOKEN` 请求头验证：
```nginx
if ($http_x_wecom_token != '配置的token') {
    return 403;
}
```
