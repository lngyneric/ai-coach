'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { 
  BookOpenIcon, 
  ArrowRightIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import { useUserStore } from '@/store';
import api from '@/api';
import request from '@/lib/request';
import { Shifu } from '@/types/shifu';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { useRouter } from 'next/navigation';
import { toast } from '@/hooks/useToast';

// ── Category Definitions ──────────────────────────────────────────
const COURSE_CATEGORIES = [
  { id: 'onboarding', label: '新人入学', description: '面向新入职员工，帮助快速融入公司文化、了解组织架构、掌握基础业务流程。', icon: '🎓', color: 'from-blue-500 to-indigo-600', bgColor: 'bg-blue-50', ringColor: 'ring-blue-200', textColor: 'text-blue-700', badgeColor: 'bg-blue-100 text-blue-700', target: '普通员工（新入职）' },
  { id: 'mentorship', label: '学分制带教', description: '系统化导师带教计划，学分制管理学习进度。涵盖岗位技能、产品知识、销售方法论等。', icon: '📚', color: 'from-emerald-500 to-teal-600', bgColor: 'bg-emerald-50', ringColor: 'ring-emerald-200', textColor: 'text-emerald-700', badgeColor: 'bg-emerald-100 text-emerald-700', target: '一线营业部门 / 初级员工' },
  { id: 'intensive', label: '小灶教学', description: '针对特定场景的精品小班课程，聚焦实战技能提升。包含案例分析、小组研讨等。', icon: '🔥', color: 'from-orange-500 to-red-600', bgColor: 'bg-orange-50', ringColor: 'ring-orange-200', textColor: 'text-orange-700', badgeColor: 'bg-orange-100 text-orange-700', target: '一线营业部门 / 二线支援部门' },
  { id: 'leadership', label: '领导力课程', description: '面向管理层的领导力发展项目，涵盖团队管理、战略思维、决策能力等。', icon: '⭐', color: 'from-purple-500 to-violet-600', bgColor: 'bg-purple-50', ringColor: 'ring-purple-200', textColor: 'text-purple-700', badgeColor: 'bg-purple-100 text-purple-700', target: '管理层' },
] as const;

// ── Course Card ──────────────────────────────────────────────────
function CourseCard({ shifu }: { shifu: Shifu }) {
  const isVideo = (shifu.keywords || []).some((k: string) => /视频|video/i.test(k));
  const courseUrl = isVideo ? `/video-player.html?bid=${shifu.bid}` : `/c/${shifu.bid}`;
  return (
    <Link href={courseUrl} className="block group">
      <Card className="border-slate-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 h-full">
        <CardContent className="p-4 flex flex-col gap-2 h-full">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white text-lg shrink-0">
              {shifu.avatar ? <img src={shifu.avatar} alt="" className="w-full h-full object-cover rounded-lg" /> : <BookOpenIcon className="w-5 h-5" />}
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="font-medium text-slate-900 text-sm leading-tight line-clamp-1 group-hover:text-blue-600 transition-colors">{shifu.name || '未命名课程'}</h4>
            </div>
          </div>
          {shifu.description && <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed mt-1">{shifu.description}</p>}
          <div className="flex items-center gap-2 mt-auto pt-2">
            <Badge variant="secondary" className="text-xs font-normal">{shifu.tts_enabled ? '🎧 语音' : '📖 阅读'}</Badge>
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
        <div className="flex items-center gap-3"><Skeleton className="w-10 h-10 rounded-lg" /><div className="flex-1 space-y-1.5"><Skeleton className="h-4 w-3/4" /></div></div>
        <Skeleton className="h-3 w-full mt-3" /><Skeleton className="h-3 w-2/3 mt-1.5" />
      </CardContent>
    </Card>
  );
}

// ── Enroll Modal ─────────────────────────────────────────────────
function EnrollModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [users, setUsers] = useState<any[]>([]);
  const [courses, setCourses] = useState<any[]>([]);
  const [userBid, setUserBid] = useState('');
  const [module, setModule] = useState('onboarding');
  const [courseBid, setCourseBid] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    request.get('/api/shifu/admin/operations/users?page_index=1&page_size=200').then((r: any) => setUsers(r?.items || r || [])).catch(() => {});
    request.get('/api/shifu/shifus?page_index=1&page_size=200').then((r: any) => setCourses(r?.items || r || [])).catch(() => {});
  }, []);

  const submit = async () => {
    if (!userBid || !courseBid) { toast({ title: '请选择学员和课程', variant: 'destructive' }); return; }
    setSubmitting(true);
    try {
      await request.post('/api/portal/admin/enroll', { user_bid: userBid, shifu_bid: courseBid, module });
      toast({ title: '分配成功' });
      onSuccess();
      onClose();
    } catch (e: any) {
      toast({ title: e?.message || '分配失败', variant: 'destructive' });
    } finally { setSubmitting(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-lg p-6 shadow-xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900">分配课程</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl">&times;</button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">选择学员</label>
            <select value={userBid} onChange={e => setUserBid(e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm">
              <option value="">选择学员...</option>
              {users.map((u: any) => <option key={u.user_bid || u.bid} value={u.user_bid || u.bid}>{u.name || u.nickname || u.username || '未知'}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">培训模块</label>
            <select value={module} onChange={e => setModule(e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm">
              <option value="onboarding">🎓 新人培训</option>
              <option value="mentorship">📚 学分制带教</option>
              <option value="intensive">🔥 小灶培训</option>
              <option value="leadership">👑 领导力课程</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">选择课程</label>
            <select value={courseBid} onChange={e => setCourseBid(e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm">
              <option value="">选择课程...</option>
              {courses.map((c: any) => <option key={c.bid} value={c.bid}>{c.name || '未命名'}</option>)}
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="px-4 py-2 text-sm text-slate-600 hover:text-slate-800 border border-slate-300 rounded-lg">取消</button>
          <button onClick={submit} disabled={submitting} className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50">
            {submitting ? '分配中...' : '确认分配'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────
export default function CoursesPage() {
  const router = useRouter();
  const isInitialized = useUserStore(s => s.isInitialized);
  const isGuest = useUserStore(s => s.isGuest);
  const userInfo = useUserStore(s => s.userInfo);
  const [shifus, setShifus] = useState<Shifu[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [greeting, setGreeting] = useState('');

  const isAdmin = userInfo?.is_operator || userInfo?.is_creator;

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 6) setGreeting('夜深了');
    else if (hour < 9) setGreeting('早上好');
    else if (hour < 12) setGreeting('上午好');
    else if (hour < 14) setGreeting('中午好');
    else if (hour < 18) setGreeting('下午好');
    else setGreeting('晚上好');
  }, []);

  useEffect(() => {
    if (isInitialized && isGuest) { router.push(`/login?redirect=${encodeURIComponent('/courses')}`); }
  }, [isInitialized, isGuest, router]);

  const fetchCourses = useCallback(async () => {
    setLoading(true);
    try {
      const { items } = await api.getShifuList({ page_index: 1, page_size: 50, archived: false });
      setShifus(items || []);
    } catch (err) { console.error('Failed to fetch courses:', err); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (isInitialized && !isGuest) fetchCourses();
    else if (isInitialized) setLoading(false);
  }, [isInitialized, isGuest, fetchCourses]);

  const getCoursesByCategory = (categoryId: string) => {
    return shifus.filter(s => {
      const name = (s.name || '').toLowerCase();
      const desc = (s.description || '').toLowerCase();
      const kw = (s.keywords || []).join(' ').toLowerCase();
      const combined = `${name} ${desc} ${kw}`;
      switch (categoryId) {
        case 'onboarding': return /新人|入职|入门|基础|新员工|onboarding|新手/.test(combined);
        case 'mentorship': return /带教|学分|mentor|导师|岗位|技能|培训/.test(combined);
        case 'intensive': return /小灶|实战|案例|精品|专项|研修|workshop|训练营/.test(combined);
        case 'leadership': return /领导|管理|管理層|战略|决策|团队|leadership/.test(combined);
        default: return false;
      }
    }).slice(0, 6);
  };

  const otherCourses = shifus.filter(s => {
    const name = (s.name || '').toLowerCase();
    const desc = (s.description || '').toLowerCase();
    const kw = (s.keywords || []).join(' ').toLowerCase();
    const combined = `${name} ${desc} ${kw}`;
    return !/新人|入职|入门|基础|新员工|onboarding|新手|带教|学分|mentor|导师|岗位|技能|培训|小灶|实战|案例|精品|专项|研修|workshop|训练营|领导|管理|管理層|战略|决策|团队|leadership/.test(combined);
  });

  if (!isInitialized) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="flex flex-col items-center gap-3"><div className="w-10 h-10 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" /><p className="text-sm text-slate-500">加载中...</p></div></div>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">S</div>
              <span className="font-semibold text-slate-900">sysmex 全部课程</span>
              {isAdmin && (
                <button onClick={() => setShowEnrollModal(true)} className="ml-3 px-3 py-1.5 text-xs font-medium bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors">
                  ＋ 分配课程
                </button>
              )}
            </div>
            <div className="flex items-center gap-4">
              <Link href="/training-portal.html" className="text-xs text-blue-600 hover:text-blue-700">培训门户</Link>
              <span className="text-sm text-slate-500">{userInfo?.name || userInfo?.user_id || '用户'}</span>
              <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium">{(userInfo?.name || '?')[0]}</div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <section className="mb-10">
          <h1 className="text-3xl font-bold text-slate-900">{greeting}，{userInfo?.name || '同学'} 👋</h1>
          <p className="text-slate-500 mt-1.5">浏览全部课程，根据你的岗位和发展阶段选择适合的学习内容。</p>
        </section>

        <section className="mb-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-1">课程体系</h2>
          <p className="text-sm text-slate-500 mb-6">围绕四个成长阶段，构建完整的企业人才培养路径</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {COURSE_CATEGORIES.map(cat => {
              const count = getCoursesByCategory(cat.id).length;
              return (
                <button key={cat.id} onClick={() => setActiveCategory(activeCategory === cat.id ? null : cat.id)}
                  className={`relative overflow-hidden rounded-2xl border-2 p-5 text-left transition-all duration-200 group ${activeCategory === cat.id ? 'border-blue-500 shadow-md bg-white' : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'}`}>
                  <div className={`absolute inset-0 opacity-5 bg-gradient-to-br ${cat.color}`} />
                  <div className="relative">
                    <span className="text-3xl">{cat.icon}</span>
                    <h3 className="text-base font-bold text-slate-900 mt-2">{cat.label}</h3>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed line-clamp-2">{cat.description}</p>
                    <div className="flex items-center gap-2 mt-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cat.badgeColor}`}>{count > 0 ? `${count} 门课程` : '即将上线'}</span>
                      <span className="text-xs text-slate-400">{cat.target}</span>
                    </div>
                    {activeCategory === cat.id && <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center"><ChevronRightIcon className="w-4 h-4" /></div>}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {loading ? (
          <div className="space-y-6">
            {[1, 2, 3].map(i => (
              <div key={i}><Skeleton className="h-6 w-40 mb-4" /><div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">{[1, 2, 3, 4].map(j => <CourseCardSkeleton key={j} />)}</div></div>
            ))}
          </div>
        ) : (
          <div className="space-y-10">
            {(activeCategory ? COURSE_CATEGORIES.filter(c => c.id === activeCategory) : COURSE_CATEGORIES).map(cat => {
              const catCourses = getCoursesByCategory(cat.id);
              if (catCourses.length === 0 && activeCategory !== cat.id) return null;
              return (
                <section key={cat.id}>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2"><span>{cat.icon}</span>{cat.label}</h3>
                      <p className="text-xs text-slate-500 mt-0.5">{cat.description}</p>
                    </div>
                  </div>
                  {catCourses.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                      {catCourses.map(s => <CourseCard key={s.bid} shifu={s} />)}
                    </div>
                  ) : (
                    <Card className="border-slate-200 border-dashed"><CardContent className="p-8 flex flex-col items-center justify-center text-center">
                      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3"><BookOpenIcon className="w-6 h-6 text-slate-400" /></div>
                      <p className="text-sm text-slate-500">该分类暂无课程</p>
                    </CardContent></Card>
                  )}
                </section>
              );
            })}
            {otherCourses.length > 0 && (
              <section>
                <div className="flex items-center justify-between mb-4"><div><h3 className="text-base font-semibold text-slate-900 flex items-center gap-2"><span>📂</span> 其他课程</h3></div></div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">{otherCourses.map(s => <CourseCard key={s.bid} shifu={s} />)}</div>
              </section>
            )}
            {shifus.length === 0 && (
              <Card className="border-slate-200 border-dashed"><CardContent className="p-12 flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4"><BookOpenIcon className="w-8 h-8 text-slate-400" /></div>
                <h3 className="text-base font-medium text-slate-700">暂无课程</h3>
                <p className="text-sm text-slate-500 mt-1">等待管理员发布课程</p>
              </CardContent></Card>
            )}
          </div>
        )}
      </main>

      {showEnrollModal && <EnrollModal onClose={() => setShowEnrollModal(false)} onSuccess={fetchCourses} />}

      <footer className="border-t border-slate-200 bg-white mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-sm text-slate-400"><span>sysmex Learning Platform</span><span>·</span><span>企业大学</span></div>
            <div className="flex items-center gap-4 text-xs text-slate-400"><span>&copy; {new Date().getFullYear()} sysmex</span></div>
          </div>
        </div>
      </footer>
    </div>
  );
}
