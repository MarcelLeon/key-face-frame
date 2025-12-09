/**
 * API 类型定义
 * 与后端 backend/api/schemas/video.py 保持一致
 */

// 处理配置参数
export interface ProcessingConfig {
  sampleRate: number; // 1-10，采样率
  maxFrames: number; // 10-500，最大关键帧数
  confidenceThreshold: number; // 0.1-0.9，置信度阈值
}

// 关键帧信息
export interface KeyframeInfo {
  frame_index: number; // 帧序号
  timestamp: number; // 秒级时间戳
  score: number; // 关键帧评分（0-1）
  bbox: number[]; // 检测框 [x1, y1, x2, y2]
  filename: string; // 保存的文件名
  track_id?: number | null; // 可选的追踪ID
}

// 视频上传响应
export interface VideoUploadResponse {
  video_id: string;
  filename: string;
  status: string; // pending, processing, completed, failed
  message: string;
}

// 视频状态响应
export interface VideoStatusResponse {
  // 基本信息
  video_id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  stage?: string | null; // detection, extraction, complete

  // 处理结果（完成后）
  total_frames?: number | null;
  total_detections?: number | null;
  keyframes_extracted?: number | null;
  processing_time_seconds?: number | null;

  // 输出路径
  output_dir?: string | null;
  metadata_path?: string | null;

  // 关键帧列表
  keyframes?: KeyframeInfo[] | null;

  // 错误信息
  error_message?: string | null;

  // 时间戳
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
}

// 关键帧列表响应
export interface KeyframesResponse {
  video_id: string;
  count: number;
  keyframes: KeyframeInfo[];
  output_dir: string;
}
