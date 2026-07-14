/**
 * patched-watcher.js — chokidar 文件监听忽略规则补丁
 *
 * 用于 dev 容器启动时覆盖 chokidar 默认行为，
 * 排除缓存/依赖目录，避免 ENOSPC (inotify 上限) 错误。
 *
 * 使用方式（在 Dockerfile_DEV 或 dev 入口脚本中）：
 *   export CHOKIDAR_USEPOLLING=1
 *   node -r ./patched-watcher.js node_modules/.bin/next dev
 *
 * 或在 docker-compose.dev.yml 的环境变量中设置：
 *   CHOKIDAR_USEPOLLING: "1"
 *   NODE_OPTIONS: "-r /app/patched-watcher.js"
 */

const path = require('path');
const Module = require('module');

// ============================================================
// 忽略规则列表（glob 模式，相对于项目根目录）
// 匹配的路径不会创建文件监听器
// ============================================================
const IGNORE_PATTERNS = [
  '**/node_modules/**',
  '**/.npm/**',
  '**/.cache/**',
  '**/.local/**',
  '**/.rustup/**',
  '**/.lark-channel/**',
  '**/.lark-cli/**',
  '**/.config/**',
  '**/pnpm-store/**',
  '**/.next/**',
  '**/__pycache__/**',
  '**/.git/**',
  '**/dist/**',
  '**/build/**',
  '**/coverage/**',
  '**/.vscode/**',
];

// ============================================================
// 拦截 chokidar.watch()，注入忽略规则
// ============================================================
const originalWatch = require('chokidar').watch;

// 保存原始 watch 引用
let chokidarResolve = null;

// 拦截模块加载，在 chokidar 加载后立即 patched
const originalRequire = Module.prototype.require;
Module.prototype.require = function (id) {
  const mod = originalRequire.apply(this, arguments);
  if (id === 'chokidar' && mod && mod.watch) {
    const patchedWatch = function (target, opts = {}) {
      // 合并忽略规则
      const existingIgnored = opts.ignored || [];
      const combinedIgnored = Array.isArray(existingIgnored)
        ? existingIgnored.concat(IGNORE_PATTERNS)
        : [existingIgnored].concat(IGNORE_PATTERNS);

      console.log(
        `[patched-watcher] chokidar.watch("${target}") → ${IGNORE_PATTERNS.length} 条忽略规则已注入`,
      );

      return originalWatch.call(mod, target, {
        ...opts,
        ignored: combinedIgnored,
        // 轮询模式（文件系统事件不可用时回退）
        usePolling: process.env.CHOKIDAR_USEPOLLING === 'true',
        interval: 500,
      });
    };
    mod.watch = patchedWatch;
    if (chokidarResolve) chokidarResolve();
  }
  return mod;
};

// ============================================================
// 健康检查：确保 chokidar 已加载并 patched
// ============================================================
let chokidarPatched = false;
try {
  const chok = require('chokidar');
  if (chok.watch !== originalWatch) {
    chokidarPatched = true;
    console.log(
      `[patched-watcher] ✅ chokidar 已 patched（${IGNORE_PATTERNS.length} 条忽略规则生效）`,
    );
  }
} catch (e) {
  // chokidar 尚未加载，后续加载时会被拦截
  console.log('[patched-watcher] ⏳ 等待 chokidar 加载...');
  new Promise((resolve) => {
    chokidarResolve = resolve;
  }).then(() => {
    console.log('[patched-watcher] ✅ chokidar 已 patched');
  });
}

module.exports = { IGNORE_PATTERNS };
