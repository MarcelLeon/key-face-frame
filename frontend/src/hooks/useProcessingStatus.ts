/**
 * useProcessingStatus Hook
 *
 * 实时轮询视频处理状态的自定义Hook
 *
 * 核心功能：
 * 1. 动态轮询间隔（pending: 1s, processing: 0.5s）
 * 2. 超时检测（30分钟自动停止）
 * 3. 错误重试（最多3次，指数退避）
 * 4. 页面可见性检测（隐藏时暂停轮询）
 * 5. 自动清理定时器（组件卸载）
 *
 * @module hooks/useProcessingStatus
 *
 * @example
 * ```tsx
 * const { status, loading, error, refresh } = useProcessingStatus(videoId);
 *
 * if (loading) return <Spin />;
 * if (error) return <Alert message={error} />;
 * if (status?.status === 'completed') return <Result />;
 * ```
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import { getVideoStatus } from '@/api/video';
import type { VideoStatusResponse } from '@/api/types';
import { POLL_INTERVALS, PROCESSING_TIMEOUT, MAX_RETRIES } from '@/utils/constants';
import { useVideoStore } from '@/stores/videoStore';

/**
 * Hook 返回值接口
 */
interface UseProcessingStatusReturn {
  /** 当前视频状态（null表示未开始轮询） */
  status: VideoStatusResponse | null;

  /** 是否正在加载中 */
  loading: boolean;

  /** 错误信息（null表示无错误） */
  error: string | null;

  /** 手动刷新函数 */
  refresh: () => void;
}

/**
 * 轮询间隔类型（用于TypeScript类型推断）
 */
type PollIntervalKey = keyof typeof POLL_INTERVALS;

/**
 * 实时轮询视频处理状态
 *
 * @param videoId - 视频ID（null时不轮询）
 * @returns Hook状态和操作函数
 *
 * @description
 * 该Hook实现了智能轮询机制：
 * - pending状态：每1秒轮询一次
 * - processing状态：每0.5秒轮询一次（更频繁）
 * - completed/failed状态：停止轮询
 * - 超过30分钟：自动停止并报错
 * - 网络错误：最多重试3次（指数退避）
 * - 页面隐藏：暂停轮询（节省资源）
 */
export const useProcessingStatus = (
  videoId: string | null
): UseProcessingStatusReturn => {
  // ========== State ==========
  const [status, setStatus] = useState<VideoStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // ========== Store ==========
  const updateStatus = useVideoStore((state) => state.updateStatus);

  // ========== Refs（跨渲染周期保持引用） ==========
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(Date.now());
  const retryCountRef = useRef<number>(0);
  const isPollingRef = useRef<boolean>(false);

  /**
   * 清理定时器
   */
  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  /**
   * 核心轮询函数
   *
   * 职责：
   * 1. 发起API请求获取状态
   * 2. 更新本地状态和全局Store
   * 3. 根据状态决定是否继续轮询
   * 4. 处理超时和错误重试
   */
  const pollStatus = useCallback(async () => {
    // 防止重复轮询
    if (!videoId || isPollingRef.current) return;

    // 超时检查（30分钟）
    const elapsed = Date.now() - startTimeRef.current;
    if (elapsed > PROCESSING_TIMEOUT) {
      setError('处理超时（30分钟），请检查视频是否过大或联系管理员');
      clearTimer();
      return;
    }

    // 标记正在轮询
    isPollingRef.current = true;
    setLoading(true);

    try {
      // 发起API请求
      const response = await getVideoStatus(videoId);
      const data = response.data;

      // 更新状态
      setStatus(data);
      updateStatus(data); // 同步到全局Store
      setError(null);

      // 重置重试计数
      retryCountRef.current = 0;

      // 判断是否需要继续轮询
      const currentStatus = data.status as PollIntervalKey;
      const shouldContinue =
        currentStatus === 'pending' || currentStatus === 'processing';

      if (shouldContinue) {
        // 根据状态决定轮询间隔
        const interval = POLL_INTERVALS[currentStatus] || 1000;

        // 设置下一次轮询
        timerRef.current = setTimeout(() => {
          isPollingRef.current = false;
          pollStatus();
        }, interval);
      } else {
        // 停止轮询（completed 或 failed）
        clearTimer();
        console.log(`[Poll] Stopped: status=${currentStatus}`);
      }
    } catch (err: any) {
      console.error('[Poll] Error:', err);

      // 错误重试逻辑（指数退避）
      if (retryCountRef.current < MAX_RETRIES) {
        retryCountRef.current++;
        const retryDelay = Math.pow(2, retryCountRef.current) * 1000; // 2^n秒

        console.log(
          `[Poll] Retry ${retryCountRef.current}/${MAX_RETRIES} after ${retryDelay}ms`
        );

        timerRef.current = setTimeout(() => {
          isPollingRef.current = false;
          pollStatus();
        }, retryDelay);
      } else {
        // 重试次数用尽
        setError(err.message || '获取状态失败，请刷新页面重试');
        clearTimer();
      }
    } finally {
      setLoading(false);
      isPollingRef.current = false;
    }
  }, [videoId, updateStatus, clearTimer]);

  /**
   * 手动刷新函数（暴露给外部调用）
   */
  const refresh = useCallback(() => {
    clearTimer();
    retryCountRef.current = 0;
    isPollingRef.current = false;
    pollStatus();
  }, [pollStatus, clearTimer]);

  /**
   * Effect: 启动轮询
   */
  useEffect(() => {
    if (videoId) {
      // 重置状态
      startTimeRef.current = Date.now();
      retryCountRef.current = 0;
      setError(null);

      // 启动轮询
      pollStatus();
    } else {
      // 清空状态
      setStatus(null);
      setError(null);
      clearTimer();
    }

    // 清理函数：组件卸载时清理定时器
    return () => {
      clearTimer();
      isPollingRef.current = false;
    };
  }, [videoId, pollStatus, clearTimer]);

  /**
   * Effect: 页面可见性检测
   *
   * 当页面隐藏时暂停轮询，恢复可见时继续轮询
   * 目的：节省资源，避免后台持续请求
   */
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // 页面隐藏：暂停轮询
        console.log('[Poll] Paused: page hidden');
        clearTimer();
        isPollingRef.current = false;
      } else {
        // 页面恢复：继续轮询（如果状态未完成）
        if (videoId && status) {
          const currentStatus = status.status;
          const shouldResume =
            currentStatus === 'pending' || currentStatus === 'processing';

          if (shouldResume) {
            console.log('[Poll] Resumed: page visible');
            pollStatus();
          }
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [videoId, status, pollStatus, clearTimer]);

  return {
    status,
    loading,
    error,
    refresh,
  };
};
