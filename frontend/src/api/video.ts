/**
 * 视频相关API方法
 */
import apiClient from './client';
import type {
  VideoUploadResponse,
  VideoStatusResponse,
  KeyframesResponse,
} from './types';
import type { AxiosProgressEvent } from 'axios';

/**
 * 上传视频并启动处理
 * @param formData - 包含视频文件和配置参数的FormData
 * @param onUploadProgress - 上传进度回调
 */
export const uploadVideo = (
  formData: FormData,
  options?: {
    onUploadProgress?: (progressEvent: AxiosProgressEvent) => void;
  }
) => {
  return apiClient.post<VideoUploadResponse>('/api/videos/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 60000, // 上传允许60秒超时
    onUploadProgress: options?.onUploadProgress,
  });
};

/**
 * 查询视频处理状态
 * @param videoId - 视频ID
 */
export const getVideoStatus = (videoId: string) => {
  return apiClient.get<VideoStatusResponse>(`/api/videos/${videoId}/status`);
};

/**
 * 获取关键帧列表
 * @param videoId - 视频ID
 */
export const getKeyframes = (videoId: string) => {
  return apiClient.get<KeyframesResponse>(`/api/videos/${videoId}/keyframes`);
};

/**
 * 下载关键帧（ZIP格式）
 * @param videoId - 视频ID
 */
export const downloadKeyframes = (videoId: string) => {
  return apiClient.get(`/api/videos/${videoId}/download`, {
    responseType: 'blob',
  });
};
