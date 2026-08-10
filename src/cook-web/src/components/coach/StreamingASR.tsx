'use client';

import { useState, useRef, useCallback } from 'react';

interface ASRState {
  /** 累积的转写全文 */
  transcript: string;
  /** 最新的增量片段（实时刷新） */
  partial: string;
  recording: boolean;
  error: string | null;
}

interface UseStreamingASR {
  state: ASRState;
  start: () => Promise<void>;
  stop: () => void;
}

/** WebSocket 流式 ASR → 增量文本 */
export function useStreamingASR(): UseStreamingASR {
  const [state, setState] = useState<ASRState>({
    transcript: '',
    partial: '',
    recording: false,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const transcriptRef = useRef('');

  const start = useCallback(async () => {
    setState(s => ({ ...s, error: null, transcript: '', partial: '' }));
    transcriptRef.current = '';

    try {
      // 1. 获取麦克风
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // 2. 连接 WebSocket (云 ASR)
      // TODO: 替换为真实 ASR WebSocket URL
      const ws = new WebSocket('wss://asr.example.com/v1/stream');
      wsRef.current = ws;

      ws.onopen = () => {
        // 3. 启动录音（短分片，高频发送）
        const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        recorderRef.current = recorder;

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) {
            ws.send(e.data); // 实时发送音频分片
          }
        };

        recorder.start(200); // 200ms 一个分片 = 低延迟流式
        setState(s => ({ ...s, recording: true }));
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        // { type: 'partial' | 'final', text: '...' }
        if (msg.type === 'partial') {
          setState(s => ({ ...s, partial: msg.text }));
        } else if (msg.type === 'final') {
          transcriptRef.current += msg.text;
          setState(s => ({
            ...s,
            transcript: transcriptRef.current,
            partial: '',
          }));
        }
      };

      ws.onerror = () => {
        setState(s => ({ ...s, error: 'ASR 连接失败' }));
      };

      ws.onclose = () => {
        cleanup();
      };
    } catch {
      setState(s => ({ ...s, error: '麦克风权限未授予' }));
    }
  }, []);

  const cleanup = useCallback(() => {
    recorderRef.current?.stop();
    streamRef.current?.getTracks().forEach(t => t.stop());
    wsRef.current?.close();
    setState(s => ({ ...s, recording: false }));
  }, []);

  const stop = useCallback(() => {
    // 发送结束信号
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ eos: true }));
    }
    // 短暂延迟后关闭，等待最后一批 final 消息
    setTimeout(cleanup, 500);
  }, [cleanup]);

  return { state, start, stop };
}

/** 流式 ASR 显示组件 */
export function StreamingTranscript({
  transcript,
  partial,
  recording,
  onStart,
  onStop,
}: {
  transcript: string;
  partial: string;
  recording: boolean;
  onStart: () => void;
  onStop: () => void;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <button
          onClick={recording ? onStop : onStart}
          className={`inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
            recording
              ? 'bg-destructive text-white animate-pulse'
              : 'bg-primary text-primary-foreground hover:opacity-90'
          }`}
        >
          {recording ? '🔴 停止' : '🎤 开始语音输入'}
        </button>
        {recording && <span className="text-xs text-muted-foreground">正在聆听…</span>}
      </div>

      {(transcript || partial) && (
        <div className="rounded-lg border border-border bg-muted/30 p-3 text-sm min-h-[40px]">
          {transcript}
          {partial && (
            <span className="text-muted-foreground italic"> {partial}</span>
          )}
          {!transcript && !partial && recording && (
            <span className="text-muted-foreground animate-pulse">…</span>
          )}
        </div>
      )}
    </div>
  );
}
