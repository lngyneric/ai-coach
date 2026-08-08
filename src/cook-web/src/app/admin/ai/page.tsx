'use client';

import React, { useState } from 'react';
import api from '@/api';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { useToast } from '@/hooks/useToast';

/**
 * AI 问答助手（/admin/ai）—— W2 遗留 3：/api/chat 前端真实接入。
 *
 * 消费 POST /api/chat（非流式）：
 *   {"messages":[{"role":"user","content":"..."}]}
 *   → data.answer
 *
 * 需要登录（全局 before_request 鉴权），无额外角色限制。
 */

type ChatMessage = {
  role: 'system' | 'user' | 'assistant';
  content: string;
};

export default function AiAssistantPage() {
  const { toast } = useToast();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    const content = input.trim();
    if (!content || loading) {
      return;
    }
    const next: ChatMessage[] = [...messages, { role: 'user', content }];
    setMessages(next);
    setInput('');
    setLoading(true);
    try {
      const res = (await api.chatCompletion({
        messages: [{ role: 'user', content }],
        temperature: 0.3,
        stream: false,
      })) as { answer?: string };
      setMessages([
        ...next,
        { role: 'assistant', content: res?.answer || '（无回复）' },
      ]);
    } catch (e: any) {
      toast({
        title: e?.message || '调用 /api/chat 失败',
        variant: 'destructive',
      });
      setMessages([
        ...next,
        { role: 'assistant', content: `⚠️ 调用失败：${e?.message || ''}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='space-y-4'>
      <div>
        <h1 className='text-xl font-semibold text-gray-900'>AI 问答助手</h1>
        <p className='mt-1 text-sm text-gray-500'>
          POST /api/chat（deepseek-v4-flash）· 登录即可使用
        </p>
      </div>

      <Card className='border-slate-200'>
        <CardContent className='p-4'>
          <div className='max-h-[420px] min-h-[200px] space-y-3 overflow-y-auto'>
            {messages.length === 0 && (
              <p className='py-10 text-center text-sm text-slate-400'>
                输入问题开始对话（例如：请用一句话介绍 AI-Coach 企业大学）
              </p>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 text-slate-800'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className='flex justify-start'>
                <div className='rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-400'>
                  AI 思考中…
                </div>
              </div>
            )}
          </div>

          <div className='mt-3 flex gap-2'>
            <Textarea
              placeholder='输入问题…'
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  void handleSend();
                }
              }}
              className='min-h-[60px] flex-1'
            />
            <Button onClick={handleSend} disabled={loading || !input.trim()}>
              {loading ? '发送中…' : '发送'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
