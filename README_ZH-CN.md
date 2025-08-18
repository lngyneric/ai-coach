<div align="center">
  <img src="assets/logo_zh.png" width=256></img>
<p><strong>你看到的一切，都是量身定制的</strong></p>

[English](README.md) | 简体中文

</div>

AI 师傅既是老师、主播、说书人，也是向导……作为一名 AI 驱动的讲述者，AI 师傅可以将任何文字内容以全方位个性化的方式呈现给每一位用户，创造前所未有的阅读体验。

![系统架构示意图](assets/architecture.png)

# 功能特性

1. **个性化输出**：根据用户的身份背景、兴趣偏好等，全方位个性化输出内容，媲美真人一对一的效果。
2. **丰富的媒体**：支持 Markdown、HTML、Mermaid 等多种格式的内容，以及嵌入图片、视频。
3. **内容安全**：通过预设的师傅剧本控制输出，减少大模型幻觉。
4. **追问**：用户可以随时提问，获得上下文相关的智能回答。
5. **互动**：随时向用户提问，基于用户的回答推动后续进程。
6. **剧本编辑器**：方便地编辑剧本，预览效果。

# 开发计划

- [ ] 整体重构
- [ ] 写作智能体，快速生成、维护剧本
- [ ] 知识库
- [ ] 语音输入输出

# 使用 AI 师傅

## 平台

[AI-Shifu.com](https://ai-shifu.com) 是一个由 AI 师傅开源项目驱动的教育平台。可以在上面学习各种 AI 课程。

## 自建站

> 如需从源代码安装，请参考 [安装手册](INSTALL_MANUAL.md)。

请先确认你的机器已经安装好[Docker](https://docs.docker.com/get-docker/)和[Docker Compose](https://docs.docker.com/compose/install/)。

### 使用 Docker Hub 镜像

```bash
git clone https://github.com/ai-shifu/ai-shifu.git
cd ai-shifu/docker

# 最小化配置（仅必需变量）：
cp .env.example.minimal .env

# 或选择完整配置选项：
cp .env.example.full .env

# 编辑 .env 文件并配置必需的变量：
# - SQLALCHEMY_DATABASE_URI: 数据库连接
# - SECRET_KEY: JWT签名密钥（生成方法: python -c "import secrets; print(secrets.token_urlsafe(32))"）
# - UNIVERSAL_VERIFICATION_CODE: 测试验证码
# - 至少一个大模型 API key（OPENAI_API_KEY、ERNIE_API_KEY 等）

docker compose up -d
```

### 从源代码构建

```bash
git clone https://github.com/ai-shifu/ai-shifu.git
cd ai-shifu/docker

# 选择配置模板：
cp .env.example.minimal .env  # 最小化配置
# 或
cp .env.example.full .env      # 完整配置

# 在 .env 文件中配置必需的变量
# 参考 .env.example.minimal 了解必需变量
# 参考 .env.example.full 了解所有可用选项

./dev_in_docker.sh
```

### 访问

Docker 启动后：
1. 用浏览器打开 `http://localhost:8080`，访问用户界面
2. 用浏览器打开 `http://localhost:8081`，访问剧本编辑器
3. 登录时可使用任意手机号，默认万能验证码为 **1024**（仅用于演示/测试，生产环境务必修改或禁用）
