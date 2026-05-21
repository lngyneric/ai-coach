# HR 路径前缀动态路由说明

## 架构

```
公网: tool.sysmex.com.cn /HR/* → Windows nginx (10.32.16.42) → Ubuntu (10.32.16.47:8080) → Docker nginx → 内部容器

内网: 10.32.16.47:8080 → Docker nginx → 内部容器（保持不变）
```

## 链路

### 带 /HR 前缀（公网 → Windows 反代）

```
地址栏: https://tool.sysmex.com.cn/HR/login
    → window.location.pathname = '/HR/login'
    → bp = '/HR'
点击登录 → fetch(bp + '/api/user/login_employee')
    → fetch('/HR/api/user/login_employee')
浏览器发请求到: https://tool.sysmex.com.cn/HR/api/user/login_employee
    → Windows nginx: rewrite /HR/... → /... → Ubuntu:8080
    → Docker nginx: /api/... → ai-shifu-api:5800 → 200
登录成功 → window.location.href = bp + '/admin'
    → /HR/admin
    → Windows nginx → rewrite → Docker nginx → cook-web:5000
```

### 不带前缀（内网直连）

```
地址栏: http://10.32.16.47:8080/login
    → window.location.pathname = '/login'
    → bp = ''
点击登录 → fetch(bp + '/api/user/login_employee')
    → fetch('/api/user/login_employee')
    → Docker nginx: /api/... → ai-shifu-api:5800 → 200
登录成功 → window.location.href = bp + '/admin'
    → /admin → Docker nginx → cook-web:5000
```

## 核心代码

```javascript
var m = window.location.pathname.match(/^(\/HR|\/hr)(?=\/|$)/i);
var bp = m ? m[1] : '';   // 有前缀 → '/HR'，没有 → ''
```

所有 API 请求和页面跳转都拼接 `bp`，不硬编码任何路径前缀。

## 相关文件

- Windows nginx: `C:\0-Ubuntu\tool.sysmex.com.cn.conf`
- Docker nginx 静态页: `sysmex-login.html`, `course-entry.html`
- Docker nginx 配置: `ai-shifu-nginx` 容器内 `/etc/nginx/conf.d/default.conf`
