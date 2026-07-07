'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { 
  BookOpenIcon, 
  AcademicCapIcon, 
  UserGroupIcon, 
  LightBulbIcon,
  ArrowRightIcon,
  TrophyIcon,
  ClockIcon,
  ChartBarIcon,
  SparklesIcon,
  CheckCircleIcon,
  CalendarDaysIcon,
} from '@heroicons/react/24/outline';
import { ChevronRightIcon } from '@heroicons/react/20/solid';
import { useUserStore } from '@/store';
import api from '@/api';
import { Shifu } from '@/types/shifu';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { useRouter } from 'next/navigation';

// ── Category Definitions ──────────────────────────────────────────
const COURSE_CATEGORIES = [
  {
    id: 'onboarding',
    label: '新人入学',
    description: '面向新入职员工，帮助快速融入公司文化、了解组织架构、掌握基础业务流程，打好职业发展第一步。',
    icon: '🎓',
    color: 'from-blue-500 to-indigo-600',
    bgColor: 'bg-blue-50',
    ringColor: 'ring-blue-200',
    textColor: 'text-blue-700',
    badgeColor: 'bg-blue-100 text-blue-700',
    target: '普通员工（新入职）',
  },
  {
    id: 'mentorship',
    label: '学分制带教',
    description: '系统化导师带教计划，学分制管理学习进度。涵盖岗位技能、产品知识、销售方法论等结构化课程体系。',
    icon: '📚',
    color: 'from-emerald-500 to-teal-600',
    bgColor: 'bg-emerald-50',
    ringColor: 'ring-emerald-200',
    textColor: 'text-emerald-700',
    badgeColor: 'bg-emerald-100 text-emerald-700',
    target: '一线营业部门 / 初级员工',
  },
  {
    id: 'intensive',
    label: '小灶教学',
    description: '针对特定场景的精品小班课程，聚焦实战技能提升。包含案例分析、小组研讨、模拟演练等互动式教学。',
    icon: '🔥',
    color: 'from-orange-500 to-red-600',
    bgColor: 'bg-orange-50',
    ringColor: 'ring-orange-200',
    textColor: 'text-orange-700',
    badgeColor: 'bg-orange-100 text-orange-700',
    target: '一线营业部门 / 二线支援部门',
  },
  {
    id: 'leadership',
    label: '领导力课程',
    description: '面向管理层的领导力发展项目，涵盖团队管理、战略思维、决策能力、跨部门协作等高层级管理技能。',
    icon: '⭐',
    color: 'from-purple-500 to-violet-600',
    bgColor: 'bg-purple-50',
    ringColor: 'ring-purple-200',
    textColor: 'text-purple-700',
    badgeColor: 'bg-purple-100 text-purple-700',
    target: '管理层',
  },
] as const;

// ── Mock learner persona dimensions ────────────────────────────────
const LEARNER_DIMENSIONS = [
  { role: '普通员工', focus: '新员工入职引导、岗位基础技能、合规培训', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  { role: '管理层', focus: '领导力发展、战略决策、团队管理', color: 'bg-purple-100 text-purple-700 border-purple-200' },
  { role: '一线营业部门', focus: '产品知识、销售技巧、客户管理', color: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  { role: '二线支援部门', focus: '流程优化、项目管理、跨部门协作', color: 'bg-orange-100 text-orange-700 border-orange-200' },
];

// ── Dashboard Stat Card ────────────────────────────────────────────
function StatCard({ icon, label, value, sub, color }: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  color: string;
}) {
  return (
    <Card className="border-slate-200">
      <CardContent className="p-4 flex items-start gap-3">
        <div className={`rounded-lg p-2.5 ${color}`}>
          {icon}
        </div>
        <div className="min-w-0">
          <p className="text-sm text-slate-500">{label}</p>
          <p className="text-2xl font-bold text-slate-900 mt-0.5">{value}</p>
          {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Todo Item ──────────────────────────────────────────────────────
function TodoItem({ checked, label, course }: { checked: boolean; label: string; course: string }) {
  return (
    <div className="flex items-start gap-2.5 py-2 group cursor-pointer hover:bg-slate-50 rounded-lg px-2 -mx-2 transition-colors">
      <div className={`mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors ${
        checked 
          ? 'bg-emerald-500 border-emerald-500' 
          : 'border-slate-300 group-hover:border-blue-400'
      }`}>
        {checked && <CheckCircleIcon className="w-4 h-4 text-white" />}
      </div>
      <div className="min-w-0 flex-1">
        <p className={`text-sm ${checked ? 'text-slate-400 line-through' : 'text-slate-700'}`}>{label}</p>
        <p className="text-xs text-slate-400 mt-0.5">{course}</p>
      </div>
    </div>
  );
}

// ── Course Card ────────────────────────────────────────────────────
function CourseCard({ shifu }: { shifu: Shifu }) {
  return (
    <Link href={`/c/${shifu.bid}`} className="block group">
      <Card className="border-slate-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 h-full">
        <CardContent className="p-4 flex flex-col gap-2 h-full">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white text-lg shrink-0">
              {shifu.avatar ? (
                <img src={shifu.avatar} alt="" className="w-full h-full object-cover rounded-lg" />
              ) : (
                <BookOpenIcon className="w-5 h-5" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="font-medium text-slate-900 text-sm leading-tight line-clamp-1 group-hover:text-blue-600 transition-colors">
                {shifu.name || '未命名课程'}
              </h4>
            </div>
          </div>
          {shifu.description && (
            <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed mt-1">
              {shifu.description}
            </p>
          )}
          <div className="flex items-center gap-2 mt-auto pt-2">
            <Badge variant="secondary" className="text-xs font-normal">
              {shifu.tts_enabled ? '🎧 语音' : '📖 阅读'}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function CourseCardSkeleton() {
  return (
    <Card className="border-slate-200">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <Skeleton className="w-10 h-10 rounded-lg" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-3/4" />
          </div>
        </div>
        <Skeleton className="h-3 w-full mt-3" />
        <Skeleton className="h-3 w-2/3 mt-1.5" />
      </CardContent>
    </Card>
  );
}

// ── Main Page ──────────────────────────────────────────────────────
export default function CoursesPage() {
  const router = useRouter();
  const isInitialized = useUserStore(s => s.isInitialized);
  const isGuest = useUserStore(s => s.isGuest);
  const userInfo = useUserStore(s => s.userInfo);
  const [shifus, setShifus] = useState<Shifu[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [greeting, setGreeting] = useState('');

  // Set greeting based on time
  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 6) setGreeting('夜深了');
    else if (hour < 9) setGreeting('早上好');
    else if (hour < 12) setGreeting('上午好');
    else if (hour < 14) setGreeting('中午好');
    else if (hour < 18) setGreeting('下午好');
    else setGreeting('晚上好');
  }, []);

  // Redirect unauthenticated users
  useEffect(() => {
    if (isInitialized && isGuest) {
      const currentPath = encodeURIComponent('/courses');
      router.push(`/login?redirect=${currentPath}`);
    }
  }, [isInitialized, isGuest, router]);

  // Fetch courses
  const fetchCourses = useCallback(async () => {
    setLoading(true);
    try {
      const { items } = await api.getShifuList({
        page_index: 1,
        page_size: 50,
        archived: false,
      });
      setShifus(items || []);
    } catch (err) {
      console.error('Failed to fetch courses:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isInitialized && !isGuest) {
      fetchCourses();
    } else if (isInitialized) {
      setLoading(false);
    }
  }, [isInitialized, isGuest, fetchCourses]);

  // Group courses by category (using keywords or name matching for now)
  // In a production system, this would use a proper category field from the API
  const getCoursesByCategory = (categoryId: string) => {
    return shifus.filter(s => {
      const name = (s.name || '').toLowerCase();
      const desc = (s.description || '').toLowerCase();
      const kw = (s.keywords || []).join(' ').toLowerCase();
      const combined = `${name} ${desc} ${kw}`;
      
      switch (categoryId) {
        case 'onboarding':
          return /新人|入职|入门|基础|新员工|onboarding|新手/.test(combined);
        case 'mentorship':
          return /带教|学分|mentor|导师|岗位|技能|培训/.test(combined);
        case 'intensive':
          return /小灶|实战|案例|精品|专项|研修|workshop|训练营/.test(combined);
        case 'leadership':
          return /领导|管理|管理層|战略|决策|团队|leadership/.test(combined);
        default:
          return false;
      }
    }).slice(0, 6);
  };

  // Uncategorized courses (fallback)  
  const otherCourses = shifus.filter(s => {
    const name = (s.name || '').toLowerCase();
    const desc = (s.description || '').toLowerCase();
    const kw = (s.keywords || []).join(' ').toLowerCase();
    const combined = `${name} ${desc} ${kw}`;
    return !/新人|入职|入门|基础|新员工|onboarding|新手|带教|学分|mentor|导师|岗位|技能|培训|小灶|实战|案例|精品|专项|研修|workshop|训练营|领导|管理|管理層|战略|决策|团队|leadership/.test(combined);
  });

  // Mock dashboard data (to be connected to real API)
  const mockTodos = [
    { checked: false, label: '完成「第2课：三层架构落地」学习', course: '从零搭建Obsidian知识库' },
    { checked: true, label: '提交课后作业', course: '华鑫产品线销售培训' },
    { checked: false, label: '参加本周五直播答疑', course: 'AI产品经理面试知识体系' },
    { checked: false, label: '完成月度学习总结报告', course: '流程体系建设' },
  ];

  const mockGrowthData = [
    { month: '1月', count: 2 },
    { month: '2月', count: 3 },
    { month: '3月', count: 5 },
    { month: '4月', count: 4 },
    { month: '5月', count: 7 },
    { month: '6月', count: 6 },
  ];

  const totalCourses = shifus.length;
  const completedCourses = shifus.slice(0, Math.floor(totalCourses * 0.45)).length;
  const totalHours = shifus.length * 1.5;
  const completionRate = totalCourses > 0 ? Math.round((completedCourses / totalCourses) * 100) : 0;

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-500">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* ═══ Top Navigation ═══ */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">
                S
              </div>
              <span className="font-semibold text-slate-900">sysmex Learning</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-500">
                {userInfo?.name || userInfo?.user_id || '用户'}
              </span>
              <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium">
                {(userInfo?.name || '?')[0]}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* ═══ Hero: Welcome + Quick Stats ═══ */}
        <section className="mb-10">
          <h1 className="text-3xl font-bold text-slate-900">
            {greeting}，{userInfo?.name || '同学'} 👋
          </h1>
          <p className="text-slate-500 mt-1.5">
            欢迎来到企业学习平台。根据你的岗位和发展阶段，以下是为您推荐的课程体系。
          </p>
        </section>

        {/* ═══ Quick Stats Dashboard ═══ */}
        <section className="mb-10">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <StatCard
              icon={<BookOpenIcon className="w-5 h-5 text-blue-600" />}
              label="在学课程"
              value={totalCourses}
              sub="全部课程"
              color="bg-blue-50"
            />
            <StatCard
              icon={<CheckCircleIcon className="w-5 h-5 text-emerald-600" />}
              label="已完成"
              value={completedCourses}
              sub={`完成率 ${completionRate}%`}
              color="bg-emerald-50"
            />
            <StatCard
              icon={<ClockIcon className="w-5 h-5 text-amber-600" />}
              label="学习时长"
              value={`${totalHours}h`}
              sub="累计学习"
              color="bg-amber-50"
            />
            <StatCard
              icon={<TrophyIcon className="w-5 h-5 text-purple-600" />}
              label="学习积分"
              value="1,280"
              sub="超越 73% 学员"
              color="bg-purple-50"
            />
          </div>
        </section>

        {/* ═══ Learner Profile Dimensions ═══ */}
        <section className="mb-10">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">学员画像维度</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {LEARNER_DIMENSIONS.map(dim => (
              <div key={dim.role} className={`rounded-xl border ${dim.color} p-4 bg-white`}>
                <h3 className="font-medium text-sm">{dim.role}</h3>
                <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{dim.focus}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ═══ Dashboard: Left = Progress+Todo, Right = Growth+AI ═══ */}
        <section className="mb-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Left Column */}
            <div className="space-y-4">
              {/* Learning Progress */}
              <Card className="border-slate-200">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <ChartBarIcon className="w-4 h-4 text-blue-500" />
                      学习进度概览
                    </h3>
                    <span className="text-xs text-slate-400">更新于今日</span>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1.5">
                        <span className="text-slate-600">课程完成率</span>
                        <span className="font-medium text-slate-900">{completionRate}%</span>
                      </div>
                      <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500"
                          style={{ width: `${completionRate}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1.5">
                        <span className="text-slate-600">本月目标</span>
                        <span className="font-medium text-slate-900">4/8 门</span>
                      </div>
                      <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full" style={{ width: '50%' }} />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Todos */}
              <Card className="border-slate-200">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <CalendarDaysIcon className="w-4 h-4 text-amber-500" />
                      待办事项
                    </h3>
                    <Badge variant="secondary" className="text-xs font-normal">
                      {mockTodos.filter(t => !t.checked).length} 项待处理
                    </Badge>
                  </div>
                  <div className="divide-y divide-slate-100">
                    {mockTodos.map((todo, i) => (
                      <TodoItem key={i} {...todo} />
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              {/* Growth Curve */}
              <Card className="border-slate-200">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <ChartBarIcon className="w-4 h-4 text-emerald-500" />
                      成长曲线
                    </h3>
                    <span className="text-xs text-slate-400">近6个月</span>
                  </div>
                  <div className="h-32 flex items-end gap-2.5">
                    {mockGrowthData.map((d, i) => {
                      const max = Math.max(...mockGrowthData.map(x => x.count));
                      const height = (d.count / max) * 100;
                      return (
                        <div key={i} className="flex-1 flex flex-col items-center gap-1.5">
                          <span className="text-xs text-slate-400 font-medium">{d.count}</span>
                          <div 
                            className="w-full rounded-md bg-gradient-to-t from-blue-500 to-blue-400 transition-all hover:from-blue-600 cursor-pointer"
                            style={{ height: `${height}%`, minHeight: '8px' }}
                          />
                          <span className="text-xs text-slate-400">{d.month}</span>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* AI Advisor */}
              <Card className="border-slate-200 bg-gradient-to-br from-blue-50/50 to-indigo-50/50">
                <CardContent className="p-5">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center shrink-0">
                      <SparklesIcon className="w-5 h-5 text-white" />
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold text-slate-900">AI 学习建议</h3>
                      <p className="text-sm text-slate-600 mt-1.5 leading-relaxed">
                        根据你的学习进度和岗位方向，建议你接下来重点关注 
                        <strong className="text-blue-700">「流程体系才是AI建设的锚点」</strong> 
                        课程。该课程与你已完成的「从零搭建Obsidian知识库」形成进阶链路，
                        帮助你从个人知识管理延伸到企业级AI建设。
                      </p>
                      <div className="flex items-center gap-2 mt-3">
                        <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-200 border-0 text-xs cursor-pointer">
                          基于你的学习画像
                        </Badge>
                        <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-200 border-0 text-xs">
                          推荐度 92%
                        </Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* ═══ Course Categories Section ═══ */}
        <section className="mb-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-1">课程体系</h2>
          <p className="text-sm text-slate-500 mb-6">围绕四个成长阶段，构建完整的企业人才培养路径</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {COURSE_CATEGORIES.map(cat => {
              const count = getCoursesByCategory(cat.id).length;
              return (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(activeCategory === cat.id ? null : cat.id)}
                  className={`relative overflow-hidden rounded-2xl border-2 p-5 text-left transition-all duration-200 group ${
                    activeCategory === cat.id
                      ? 'border-blue-500 shadow-md bg-white'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                  }`}
                >
                  <div className={`absolute inset-0 opacity-5 bg-gradient-to-br ${cat.color}`} />
                  <div className="relative">
                    <span className="text-3xl">{cat.icon}</span>
                    <h3 className="text-base font-bold text-slate-900 mt-2">{cat.label}</h3>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed line-clamp-2">{cat.description}</p>
                    <div className="flex items-center gap-2 mt-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cat.badgeColor}`}>
                        {count > 0 ? `${count} 门课程` : '即将上线'}
                      </span>
                      <span className="text-xs text-slate-400">{cat.target}</span>
                    </div>
                    {activeCategory === cat.id && (
                      <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center">
                        <ChevronRightIcon className="w-4 h-4" />
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* ═══ Course Listings by Category ═══ */}
        {loading ? (
          <div className="space-y-6">
            {[1, 2, 3].map(i => (
              <div key={i}>
                <Skeleton className="h-6 w-40 mb-4" />
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {[1, 2, 3, 4].map(j => (
                    <CourseCardSkeleton key={j} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-10">
            {/* Show active category or all */}
            {(activeCategory ? COURSE_CATEGORIES.filter(c => c.id === activeCategory) : COURSE_CATEGORIES).map(cat => {
              const catCourses = getCoursesByCategory(cat.id);
              if (catCourses.length === 0 && activeCategory !== cat.id) return null;
              
              return (
                <section key={cat.id}>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                        <span>{cat.icon}</span>
                        {cat.label}
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">{cat.description}</p>
                    </div>
                    {catCourses.length > 0 && (
                      <Link 
                        href={catCourses.length > 0 ? `/c/${catCourses[0].bid}` : '#'}
                        className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
                      >
                        查看全部 <ArrowRightIcon className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                  
                  {catCourses.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                      {catCourses.map(s => (
                        <CourseCard key={s.bid} shifu={s} />
                      ))}
                    </div>
                  ) : (
                    <Card className="border-slate-200 border-dashed">
                      <CardContent className="p-8 flex flex-col items-center justify-center text-center">
                        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
                          <BookOpenIcon className="w-6 h-6 text-slate-400" />
                        </div>
                        <p className="text-sm text-slate-500">该分类暂无课程</p>
                        <p className="text-xs text-slate-400 mt-1">课程正在准备中，敬请期待</p>
                      </CardContent>
                    </Card>
                  )}
                </section>
              );
            })}

            {/* Other/uncategorized courses */}
            {otherCourses.length > 0 && (
              <section>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                      <span>📂</span> 其他课程
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">更多推荐课程</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {otherCourses.map(s => (
                    <CourseCard key={s.bid} shifu={s} />
                  ))}
                </div>
              </section>
            )}

            {shifus.length === 0 && (
              <Card className="border-slate-200 border-dashed">
                <CardContent className="p-12 flex flex-col items-center justify-center text-center">
                  <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                    <BookOpenIcon className="w-8 h-8 text-slate-400" />
                  </div>
                  <h3 className="text-base font-medium text-slate-700">暂无课程</h3>
                  <p className="text-sm text-slate-500 mt-1">等待管理员发布课程后，这里将展示所有学习内容</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </main>

      {/* ═══ Footer ═══ */}
      <footer className="border-t border-slate-200 bg-white mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span>sysmex Learning Platform</span>
              <span>·</span>
              <span>企业大学</span>
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <span>© {new Date().getFullYear()} sysmex</span>
              <button className="hover:text-slate-600 transition-colors">帮助</button>
              <button className="hover:text-slate-600 transition-colors">反馈</button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
