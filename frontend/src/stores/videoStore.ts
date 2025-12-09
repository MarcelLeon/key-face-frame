/**
 * Video State Management Store
 *
 * 使用 Zustand 管理视频处理的全局状态
 *
 * 核心功能：
 * 1. 当前视频状态追踪（video_id, status）
 * 2. 用户配置管理（sample_rate, max_frames, confidence_threshold）
 * 3. LocalStorage 持久化（配置和当前视频ID）
 *
 * @module stores/videoStore
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { ProcessingConfig, VideoStatusResponse } from '@/api/types';
import { DEFAULT_CONFIG } from '@/utils/constants';

/**
 * 视频状态接口
 */
interface VideoState {
  // ========== 当前视频状态 ==========
  /** 当前处理的视频ID */
  currentVideoId: string | null;

  /** 当前视频的实时状态（从API轮询获取） */
  currentStatus: VideoStatusResponse | null;

  // ========== 用户配置 ==========
  /** 处理配置参数 */
  config: ProcessingConfig;

  // ========== Actions ==========
  /** 设置当前视频ID */
  setCurrentVideo: (videoId: string) => void;

  /** 更新视频状态（由轮询Hook调用） */
  updateStatus: (status: VideoStatusResponse) => void;

  /** 更新配置（部分更新） */
  updateConfig: (config: Partial<ProcessingConfig>) => void;

  /** 重置整个配置为默认值 */
  resetConfig: () => void;

  /** 清空当前视频（用于开始新的处理） */
  clearCurrentVideo: () => void;

  /** 完全重置Store */
  reset: () => void;
}

/**
 * Video Store
 *
 * 使用 persist 中间件实现 LocalStorage 持久化
 * 只持久化 currentVideoId 和 config，不持久化 currentStatus（实时数据）
 */
export const useVideoStore = create<VideoState>()(
  persist(
    (set) => ({
      // ========== 初始状态 ==========
      currentVideoId: null,
      currentStatus: null,
      config: {
        sampleRate: DEFAULT_CONFIG.sampleRate,
        maxFrames: DEFAULT_CONFIG.maxFrames,
        confidenceThreshold: DEFAULT_CONFIG.confidenceThreshold,
      },

      // ========== Actions 实现 ==========

      /**
       * 设置当前视频ID
       * @param videoId - 视频唯一标识符
       */
      setCurrentVideo: (videoId: string) => {
        set({
          currentVideoId: videoId,
          // 切换视频时清空旧状态
          currentStatus: null,
        });
      },

      /**
       * 更新视频状态
       * @param status - 从API获取的最新状态
       */
      updateStatus: (status: VideoStatusResponse) => {
        set({ currentStatus: status });
      },

      /**
       * 更新配置（部分更新，保留未修改的字段）
       * @param newConfig - 要更新的配置字段
       *
       * @example
       * updateConfig({ sampleRate: 10 }); // 只更新 sampleRate
       */
      updateConfig: (newConfig: Partial<ProcessingConfig>) => {
        set((state) => ({
          config: { ...state.config, ...newConfig },
        }));
      },

      /**
       * 重置配置为默认值
       */
      resetConfig: () => {
        set({
          config: {
            sampleRate: DEFAULT_CONFIG.sampleRate,
            maxFrames: DEFAULT_CONFIG.maxFrames,
            confidenceThreshold: DEFAULT_CONFIG.confidenceThreshold,
          },
        });
      },

      /**
       * 清空当前视频（不清空配置）
       */
      clearCurrentVideo: () => {
        set({
          currentVideoId: null,
          currentStatus: null,
        });
      },

      /**
       * 完全重置 Store（恢复到初始状态）
       */
      reset: () => {
        set({
          currentVideoId: null,
          currentStatus: null,
          config: {
            sampleRate: DEFAULT_CONFIG.sampleRate,
            maxFrames: DEFAULT_CONFIG.maxFrames,
            confidenceThreshold: DEFAULT_CONFIG.confidenceThreshold,
          },
        });
      },
    }),

    // ========== Persist 配置 ==========
    {
      name: 'video-storage', // LocalStorage key

      // 选择要持久化的字段（不持久化实时状态）
      partialize: (state) => ({
        currentVideoId: state.currentVideoId,
        config: state.config,
      }),

      // 使用 localStorage
      storage: createJSONStorage(() => localStorage),
    }
  )
);

/**
 * Selector Hooks（优化性能，避免不必要的重渲染）
 */

/** 获取当前视频ID */
export const useCurrentVideoId = () => useVideoStore((state) => state.currentVideoId);

/** 获取当前视频状态 */
export const useCurrentStatus = () => useVideoStore((state) => state.currentStatus);

/** 获取配置 */
export const useConfig = () => useVideoStore((state) => state.config);

/** 获取所有Actions */
export const useVideoActions = () => useVideoStore((state) => ({
  setCurrentVideo: state.setCurrentVideo,
  updateStatus: state.updateStatus,
  updateConfig: state.updateConfig,
  resetConfig: state.resetConfig,
  clearCurrentVideo: state.clearCurrentVideo,
  reset: state.reset,
}));
