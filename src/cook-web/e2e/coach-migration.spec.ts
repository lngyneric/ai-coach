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

  // ── 1. 登录 devcoach ──
  await page.goto('/login', { waitUntil: 'networkidle', timeout: 60_000 });
  await page.waitForSelector('#employeeNo', { timeout: 30_000 });
  await page.fill('#employeeNo', process.env.CW_E2E_COACH || 'devcoach');
  await page.fill('#employee-password', process.env.CW_E2E_COACH_PWD || 'devpass-any');
  await page.getByRole('button', { name: /Login|登\s*录/ }).first().click();
  await page.waitForURL('**/admin**', { timeout: 30_000 });

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
  await expect(page.getByText(/待评分/)).toBeVisible();

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
