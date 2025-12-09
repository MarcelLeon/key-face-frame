/**
 * 格式化工具函数
 */
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import duration from 'dayjs/plugin/duration';
import 'dayjs/locale/zh-cn';

// 配置dayjs
dayjs.extend(relativeTime);
dayjs.extend(duration);
dayjs.locale('zh-cn');

/**
 * 格式化文件大小
 * @param bytes - 字节数
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

/**
 * 格式化时间戳（秒）为 mm:ss 格式
 * @param seconds - 秒数
 */
export const formatTimestamp = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

/**
 * 格式化处理时间
 * @param seconds - 秒数
 */
export const formatProcessingTime = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}秒`;
  }
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${minutes}分${secs}秒`;
};

/**
 * 格式化日期时间
 * @param dateString - ISO日期字符串
 * @param format - 格式模板
 */
export const formatDateTime = (
  dateString: string,
  format: string = 'YYYY-MM-DD HH:mm:ss'
): string => {
  return dayjs(dateString).format(format);
};

/**
 * 格式化为相对时间
 * @param dateString - ISO日期字符串
 */
export const formatRelativeTime = (dateString: string): string => {
  return dayjs(dateString).fromNow();
};

/**
 * 验证视频文件格式
 * @param filename - 文件名
 * @param allowedFormats - 允许的格式列表
 */
export const isValidVideoFormat = (
  filename: string,
  allowedFormats: string[]
): boolean => {
  const lowerFilename = filename.toLowerCase();
  return allowedFormats.some((ext) => lowerFilename.endsWith(ext));
};

/**
 * 验证文件大小
 * @param size - 文件大小（字节）
 * @param maxSize - 最大允许大小（字节）
 */
export const isValidFileSize = (size: number, maxSize: number): boolean => {
  return size <= maxSize;
};
