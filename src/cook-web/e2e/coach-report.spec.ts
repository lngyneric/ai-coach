import { expect, test } from '@playwright/test';

/**
 * coach 学员分析报告页 e2e：
 *   devcoach 登录 → /admin/coach 学员看板（取第一个学员 learner_bid）
 *   → /admin/coach/students/<bid>/report：4 统计卡 / 面谈时间线 / AI 改进建议
 *   → progress 页入口互链（「查看报告」→ 报告页）。
 *
 * 依赖：employee 登录可用（AAD_BYPASS dev）、devcoach 具备 role-coach
 * （view_all_students / view_any_report）。AI 建议走真实后端
 * GET /api/coach/report/<learner_bid>（LLM 优先、规则降级），耗时放宽。
 *
 * 与 coach-migration.spec.ts 登录写法一致（API + token 注入，不依赖 /login DOM）。
 */
test('coach 学员分析报告页（4 卡 + 面谈时间线 + AI 建议 + progress 互链）', async ({
  page,
}) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(String(e)));

  // ── 1. 登录 devcoach ──
  const loginRes = await page.request.post('/api/user/login_employee', {
    data: {
      employeeNo: process.env.CW_E2E_COACH || 'devcoach',
      password: process.env.CW_E2E_COACH_PWD || 'devpass-any',
      language: 'zh-CN',
      login_context: 'web',
    },
  });
  const loginBody = (await loginRes.json()) as {
    code?: number;
    data?: { token?: string };
  };
  if (loginBody.code !== 0 || !loginBody.data?.token) {
    throw new Error(`devcoach 登录失败: ${JSON.stringify(loginBody)}`);
  }
  const coachToken = loginBody.data.token;
  await page.addInitScript(
    ({ token }) => {
      localStorage.setItem('token', JSON.stringify(token));
      localStorage.setItem('token_faked', '0');
      document.cookie = `token=${token};path=/;SameSite=Lax`;
    },
    { token: coachToken },
  );

  // ── 2. 学员看板 → 取第一个学员 bid ──
  await page.goto('/admin/coach', { waitUntil: 'networkidle', timeout: 60_000 });
  await expect(page.getByRole('heading', { name: '导师工作台' })).toBeVisible();
  const studentLink = page.locator('a[href^="/admin/coach/students/"]').first();
  await expect(studentLink).toBeVisible();
  const href = (await studentLink.getAttribute('href')) ?? '';
  const match = href.match(/\/admin\/coach\/students\/([^/?#]+)$/);
  const learnerBid = match ? match[1] : 'w3-ln-4';
  expect(learnerBid.length).toBeGreaterThan(0);
  // eslint-disable-next-line no-console
  console.log(`[coach-report] learner_bid=${learnerBid}`);

  // ── 3. 报告页：4 统计卡 + 面谈时间线 + AI 建议 ──
  await page.goto(`/admin/coach/students/${learnerBid}/report`, {
    waitUntil: 'load',
    timeout: 90_000,
  });
  await expect(page.getByText(/的带教分析报告/)).toBeVisible({ timeout: 30_000 });
  for (const label of ['阶段完成', '验收通过率', '面谈次数', '最新阶段总分']) {
    await expect(page.getByText(label)).toBeVisible();
  }
  await expect(page.getByRole('heading', { name: '面谈时间线' })).toBeVisible();
  // AI 建议卡（真实后端，LLM 或规则降级；放宽等待）
  await expect(page.getByText('AI 改进建议').first()).toBeVisible({
    timeout: 120_000,
  });
  // 返回进度详表链接（互链）
  await expect(page.locator('a[href*="/progress"]').first()).toBeVisible();

  // ── 4. progress 页入口互链 ──
  await page.goto(`/admin/coach/students/${learnerBid}/progress`, {
    waitUntil: 'load',
    timeout: 60_000,
  });
  const reportLink = page.locator('a[href$="/report"]').first();
  await expect(reportLink).toBeVisible();
  await reportLink.click();
  await expect(page.getByText(/的带教分析报告/)).toBeVisible({ timeout: 30_000 });

  expect(errors).toEqual([]);
});
