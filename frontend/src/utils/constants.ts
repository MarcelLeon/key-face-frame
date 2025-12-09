/**
 * 全局常量定义
 */

// API基础URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// 支持的视频格式
export const SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.mkv'];

// 文件大小限制（字节）
export const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

// 轮询间隔（毫秒）
export const POLL_INTERVALS = {
  pending: 1000,      // 1秒
  processing: 500,    // 0.5秒
  completed: 0,       // 停止
  failed: 0,          // 停止
} as const;

// 超时时间（毫秒）
export const PROCESSING_TIMEOUT = 30 * 60 * 1000; // 30分钟

// 错误重试次数
export const MAX_RETRIES = 3;

// 处理配置预设
export const CONFIG_PRESETS = {
  fast: {
    sampleRate: 10,
    maxFrames: 10,
    confidenceThreshold: 0.5,
    label: '快速模式',
    description: '快速处理，适合预览',
  },
  standard: {
    sampleRate: 5,
    maxFrames: 20,
    confidenceThreshold: 0.5,
    label: '标准模式',
    description: '平衡速度和质量',
  },
  high: {
    sampleRate: 1,
    maxFrames: 50,
    confidenceThreshold: 0.5,
    label: '高质量模式',
    description: '详细处理，耗时较长',
  },
} as const;

// 默认配置
export const DEFAULT_CONFIG = CONFIG_PRESETS.standard;

// 处理阶段映射
export const STAGE_LABELS: Record<string, string> = {
  detection: '检测人物中...',
  extraction: '提取关键帧中...',
  complete: '处理完成',
};

// 状态标签映射
export const STATUS_LABELS: Record<string, string> = {
  pending: '等待处理',
  processing: '处理中',
  completed: '已完成',
  failed: '处理失败',
};
