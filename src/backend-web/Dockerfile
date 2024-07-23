from node:18-alpine
# 使用官方的node运行时作为父镜像

# 设置工作目录
WORKDIR /usr/src/app

# 安装项目依赖
# 复制package.json和package-lock.json文件
COPY package*.json ./
#RUN npm install --force
RUN npm install --registry=http://registry.npm.taobao.org --force
# RUN npm install  --force



# 复制项目源代码
COPY . .

# 构建项目
RUN npm run build


# 安装serve工具，用于运行构建好的项目
RUN npm install -g serve


# 声明服务运行在5000端口
EXPOSE 5000

# 启动服务
CMD ["serve", "-s", "build", "-l", "5000"]
