/**
 * VideoUploader Component
 *
 * 视频文件上传组件（支持拖拽）
 *
 * 功能特性：
 * 1. 拖拽上传 + 点击选择文件
 * 2. 前端验证（文件格式、大小）
 * 3. 实时上传进度条
 * 4. 自动携带配置参数
 * 5. 上传成功后回调（返回video_id）
 *
 * @module components/VideoUploader
 *
 * @example
 * ```tsx
 * <VideoUploader
 *   config={config}
 *   onSuccess={(videoId) => navigate(`/processing/${videoId}`)}
 *   disabled={uploading}
 * />
 * ```
 */

import React, { useState } from 'react';
import { Upload, App, Progress, Typography } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import { uploadVideo } from '@/api/video';
import type { ProcessingConfig } from '@/api/types';
import {
  SUPPORTED_VIDEO_FORMATS,
  MAX_FILE_SIZE,
} from '@/utils/constants';
import { formatFileSize } from '@/utils/formatters';

const { Dragger } = Upload;
const { Text } = Typography;

/**
 * 组件Props接口
 */
interface VideoUploaderProps {
  /** 处理配置参数（采样率、最大帧数、置信度） */
  config: ProcessingConfig;

  /** 上传成功回调（返回video_id） */
  onSuccess: (videoId: string) => void;

  /** 是否禁用上传 */
  disabled?: boolean;
}

/**
 * VideoUploader 组件
 *
 * @component
 * @description
 * 使用 Ant Design 的 Upload.Dragger 实现拖拽上传
 * 包含完整的前端验证和错误处理
 */
export const VideoUploader: React.FC<VideoUploaderProps> = ({
  config,
  onSuccess,
  disabled = false,
}) => {
  // ========== Hooks ==========
  const { message } = App.useApp();

  // ========== State ==========
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  /**
   * 前端文件验证（在上传前执行）
   *
   * @param file - 待上传的文件
   * @returns true继续上传，false中断上传
   */
  const beforeUpload = (file: UploadFile): boolean => {
    // 1. 验证文件格式
    const isValidFormat = SUPPORTED_VIDEO_FORMATS.some((ext) =>
      file.name.toLowerCase().endsWith(ext)
    );

    if (!isValidFormat) {
      message.error(
        `不支持的文件格式！仅支持: ${SUPPORTED_VIDEO_FORMATS.join(', ')}`
      );
      return false;
    }

    // 2. 验证文件大小
    const isValidSize = (file.size || 0) <= MAX_FILE_SIZE;

    if (!isValidSize) {
      message.error(
        `文件过大！最大支持 ${formatFileSize(MAX_FILE_SIZE)}`
      );
      return false;
    }

    return true;
  };

  /**
   * 自定义上传实现
   *
   * @description
   * 使用自定义上传逻辑，而非Ant Design默认的action
   * 可以完全控制请求过程（进度、错误处理等）
   */
  const customRequest: UploadProps['customRequest'] = async ({
    file,
    onProgress,
    onSuccess: onUploadSuccess,
    onError,
  }) => {
    setUploading(true);
    setUploadProgress(0);

    try {
      // 构建FormData
      const formData = new FormData();
      formData.append('file', file as File);
      formData.append('sample_rate', config.sampleRate.toString());
      formData.append('max_frames', config.maxFrames.toString());
      formData.append('confidence_threshold', config.confidenceThreshold.toString());

      // 发起上传请求
      const response = await uploadVideo(formData, {
        onUploadProgress: (progressEvent) => {
          const percent = Math.floor(
            (progressEvent.loaded / (progressEvent.total || 1)) * 100
          );
          setUploadProgress(percent);
          onProgress?.({ percent });
        },
      });

      // 上传成功
      const { video_id, filename } = response.data;
      message.success(`${filename} 上传成功！正在处理视频...`);

      // 调用成功回调
      onUploadSuccess?.(response.data);
      onSuccess(video_id);
    } catch (error: any) {
      // 上传失败
      console.error('[Upload] Error:', error);
      message.error(error.message || '上传失败，请重试');
      onError?.(error);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div style={{ width: '100%' }}>
      {/* 拖拽上传区域 */}
      <Dragger
        name="file"
        multiple={false}
        maxCount={1}
        accept={SUPPORTED_VIDEO_FORMATS.join(',')}
        disabled={disabled || uploading}
        beforeUpload={beforeUpload}
        customRequest={customRequest}
        showUploadList={false}
        style={{
          background: disabled || uploading ? '#f5f5f5' : undefined,
        }}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
        </p>
        <p className="ant-upload-text" style={{ fontSize: 16, marginBottom: 8 }}>
          {uploading ? '上传中，请稍候...' : '点击或拖拽视频文件到此区域'}
        </p>
        <p className="ant-upload-hint" style={{ color: '#8c8c8c' }}>
          支持格式: {SUPPORTED_VIDEO_FORMATS.join(', ')}
          <br />
          最大文件大小: {formatFileSize(MAX_FILE_SIZE)}
        </p>
      </Dragger>

      {/* 上传进度条 */}
      {uploading && (
        <div style={{ marginTop: 16 }}>
          <Progress
            percent={uploadProgress}
            status="active"
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
          <Text type="secondary" style={{ fontSize: 12, marginTop: 8 }}>
            正在上传视频文件...
          </Text>
        </div>
      )}
    </div>
  );
};

export default VideoUploader;
