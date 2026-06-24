# AI-Shifu 功能测试手册

> 更新时间: 2026-06-24 | 分支: main / dev

---

## 📋 环境检查

```bash
# 1. 检查所有服务
docker ps

# 2. 检查路由
curl -sI http://localhost:8080/api/config
curl -sI http://localhost:8080/
curl -sI http://localhost:8080/fastclaw/

# 3. 登录
curl -s -X POST http://localhost:8080/api/user/login_employee \
  -H "Content-Type: application/json" \
  -d '{"employeeNo":"admin","password":"any","verificationCode":"1024"}'
```

---

## 🆕 今日新增功能测试

### 1. 🎬 视频多媒体支持

支持的视频源 URL 格式：

| 类型 | 示例 |
|:-----|:------|
| MP4 直链 | `https://example.com/video.mp4` |
| HLS 流 | `https://example.com/stream.m3u8` |
| WebM | `https://example.com/video.webm` |
| 阿里云 VOD | `aliyunvod://e08280975efb71f1b8946732b68f0102` |
| Bilibili | `https://www.bilibili.com/video/BV1xx411c7mD` |
| YouTube | `https://www.youtube.com/watch?v=dQw4w9WgXcQ` |

### 2. 📥 课件导出 (Markdown / HTML)

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/api/user/login_employee \
  -H "Content-Type: application/json" \
  -d '{"employeeNo":"admin","password":"any","verificationCode":"1024"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

BID="8155268c74df4284b714b41deb048c37"

# 导出 Markdown
curl -s "http://localhost:8080/api/shifu/shifus/$BID/export?format=markdown" \
  -H "Cookie: token=$TOKEN" > /tmp/course.md
echo "✅ Markdown: $(wc -l /tmp/course.md) 行"

# 导出 HTML（含样式，浏览器直接打开）
curl -s "http://localhost:8080/api/shifu/shifus/$BID/export?format=html" \
  -H "Cookie: token=$TOKEN" > /tmp/course.html
open /tmp/course.html

# 导出 JSON
curl -s "http://localhost:8080/api/shifu/shifus/$BID/export?format=json" \
  -H "Cookie: token=$TOKEN" > /tmp/course.json
```

### 3. 🎬 Aliplayer SDK + iframe 回退

在 MDFlow 课程内容中插入视频链接即可自动识别播放。

### 4. 🧭 幻灯片渲染（完整版）

课程预览 → 听模式 → 幻灯片播放（含动画 + 移动端适配）

### 5. 📖 课程编辑器引导

首次进入课程编辑页出现分步引导。

### 6. 🔧 Celery Worker 自愈

```bash
docker ps | grep celery
docker logs ai-shifu-celery-worker --tail 3
```

---

## 🌐 Web 测试流程

```
1. 登录 → http://localhost:8080/sysmex-login.html
   工号: admin / 密码: 任意 / 验证码: 1024

2. 管理后台 → http://localhost:8080/admin/operations
   → 创建课程 → 编辑内容 → 预览

3. FastClaw → http://localhost:8080/fastclaw/
   邮箱: lng_yn@hotmail.com / 密码: x2RsIqPS
```

---

## 📊 测试结果汇总

| 功能 | 状态 |
|:-----|:----:|
| 视频源检测 (7种) | ✅ |
| Markdown 导出 | ✅ |
| HTML 导出（含深色主题） | ✅ |
| Aliplayer SDK 动态加载 | ✅ |
| 幻灯片渲染完整版 | ✅ |
| Celery worker 自愈 | ✅ |
| 课程编辑器引导 | ✅ |
