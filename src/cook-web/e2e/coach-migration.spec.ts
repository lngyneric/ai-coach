import { expect, test } from '@playwright/test';

/**
 * coach-lab 迁移核心流程 e2e：
 *   devcoach 登录 → /admin/coach 学员看板（统计卡/学员列表/待评分明细）
 *   → 面谈记录 Tab（既有 CRUD 保留）→ 学员详情 → 1v1 三环闭环
 *   （发起面谈 → 记录 → 课后总结 → 闭环完成）。
 *
 * 依赖：employee 登录可用（AAD_BYPASS dev）、devcoach 具备 role-coach
 * （create_session/view_all_students/score）。数据域由后端控制。
 */
test('coach 学员看板 + 1v1 三环闭环', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(String(e)));

  // ── 1. 登录 devcoach（API + token 注入，与 W23 e2e / docker/login.html 写
  //      法一致）。不依赖 /login 页面 DOM：dev nginx 把 /login 重写为静态
  //      login.html（#employeeNo/#password/#submitBtn），与 cook-web Next /login
  //      并存，UI 登录选择器不稳定；直接用 login_employee 端点取 token 最稳。
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

  // ── 2. 导师工作台 ──
  await page.goto('/admin/coach', { waitUntil: 'networkidle', timeout: 60_000 });
  await expect(page.getByRole('heading', { name: '导师工作台' })).toBeVisible();
  await expect(page.getByRole('tab', { name: '学员看板' })).toBeVisible();
  await expect(page.getByRole('tab', { name: '面谈记录' })).toBeVisible();

  // 学员看板：统计卡 + 学员列表
  await expect(page.locator('text=在带学员')).toBeVisible();
  const studentCards = page.locator('a[href^="/admin/coach/students/"]');
  await expect(studentCards.first()).toBeVisible();

  // 面谈记录 Tab：既有 sessions CRUD 保留
  await page.getByRole('tab', { name: '面谈记录' }).click();
  await expect(page.getByText('新建面谈记录')).toBeVisible();
  await expect(page.getByText('面谈记录列表')).toBeVisible();

  // ── 3. 学员详情 ──
  await page.getByRole('tab', { name: '学员看板' }).click();
  await studentCards.first().click();
  await page.waitForSelector('button:has-text("发起面谈")', { timeout: 20_000 });
  await expect(page.locator('h2:has-text("1v1 面谈")')).toBeVisible();
  await expect(page.getByText('查看分析报告')).toBeVisible();
  // 详情页「待评分」section（ScorePanel 标题）；页面存在多个含「待评分」的文案
  // 元素（标题 + 空态 + 催办提示），strict-mode 下用 .first() 消歧。
  await expect(page.getByText(/待评分/).first()).toBeVisible();

  // ── 4. 1v1 三环闭环（真实后端 CRUD + LLM 总结）──
  const topic = `e2e-三环-${Date.now().toString().slice(-6)}`;
  await page.getByRole('button', { name: '发起面谈' }).click();
  await page.locator('input[placeholder="面谈主题 *"]').fill(topic);
  await page.getByRole('button', { name: '创建面谈' }).click();
  await expect(page.locator(`text=${topic}`).first()).toBeVisible({
    timeout: 15_000,
  });

  const recordBtn = page.locator('button:has-text("记录面谈")').first();
  if (await recordBtn.count()) {
    await recordBtn.click();
    await page.locator('textarea[placeholder="面谈笔记…"]').first().fill('e2e：进度对齐');
    await page.locator('input[placeholder="行动项"]').first().fill('完成阶段考试');
    await page.getByRole('button', { name: '保存记录' }).click();
    // 保存记录的后端 PUT 会触发 LLM ai_summary 生成（dev 实测约 3s），期间
    // SessionPanel busy=true；等 notes 表单收起（run() 结束）后再进课后总结，
    // 避免「完成闭环」按钮仍被 busy 禁用、或表单被 run() 的 setSummarizing(null) 关闭。
    await expect(page.locator('textarea[placeholder="面谈笔记…"]')).toBeHidden({
      timeout: 30_000,
    });
    await expect(page.locator('button:has-text("课后总结")').first()).toBeVisible({
      timeout: 20_000,
    });
  } else {
    throw new Error('未找到「记录面谈」按钮');
  }

  await page.locator('button:has-text("课后总结")').first().click();
  await page
    .locator('textarea[placeholder="AI 汇总本场要点…"]')
    .fill('e2e 冒烟：目标达成，按行动项推进');
  await page.getByRole('button', { name: '完成闭环' }).click();
  await expect(page.locator('text=闭环完成').first()).toBeVisible({
    timeout: 30_000,
  });

  expect(errors).toEqual([]);
});
