/**
 * ProcessingStatus Component
 *
 * 视频处理状态展示组件
 *
 * 功能特性：
 * 1. 实时进度条（0-100%）
 * 2. 当前阶段提示（检测中/提取中/完成）
 * 3. 状态图标和颜色
 * 4. 处理元数据展示（总帧数、检测数、关键帧数、耗时）
 * 5. 错误提示
 *
 * @module components/ProcessingStatus
 *
 * @example
 * ```tsx
 * const { status, loading, error } = useProcessingStatus(videoId);
 *
 * <ProcessingStatus
 *   status={status}
 *   loading={loading}
 *   error={error}
 * />
 * ```
 */

import React from 'react';
import {
  Card,
  Progress,
  Space,
  Typography,
  Alert,
  Spin,
  Statistic,
  Row,
  Col,
  Tag,
} from 'antd';
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import type { VideoStatusResponse } from '@/api/types';
import { STAGE_LABELS, STATUS_LABELS } from '@/utils/constants';
import { formatProcessingTime, formatRelativeTime } from '@/utils/formatters';

const { Title, Text } = Typography;

/**
 * 组件Props接口
 */
interface ProcessingStatusProps {
  /** 视频状态（null表示未开始） */
  status: VideoStatusResponse | null;

  /** 是否正在加载 */
  loading?: boolean;

  /** 错误信息 */
  error?: string | null;
}

/**
 * 根据状态获取进度条颜色
 */
const getProgressColor = (status?: string): string => {
  switch (status) {
    case 'pending':
      return '#1890ff';
    case 'processing':
      return '#52c41a';
    case 'completed':
      return '#52c41a';
    case 'failed':
      return '#ff4d4f';
    default:
      return '#d9d9d9';
  }
};

/**
 * 根据状态获取图标
 */
const getStatusIcon = (status?: string): React.ReactNode => {
  switch (status) {
    case 'pending':
      return <ClockCircleOutlined style={{ color: '#1890ff' }} />;
    case 'processing':
      return <LoadingOutlined style={{ color: '#52c41a' }} />;
    case 'completed':
      return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    case 'failed':
      return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
    default:
      return null;
  }
};

/**
 * ProcessingStatus 组件
 *
 * @component
 * @description
 * 根据状态显示不同的UI：
 * - loading: 骨架屏
 * - error: 错误提示
 * - status: 进度条 + 元数据
 */
export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  status,
  loading,
  error,
}) => {
  // ========== 错误状态 ==========
  if (error) {
    return (
      <Alert
        message="获取状态失败"
        description={error}
        type="error"
        showIcon
        icon={<CloseCircleOutlined />}
      />
    );
  }

  // ========== 加载状态 ==========
  if (loading && !status) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin tip="加载中..." size="large">
            <div style={{ minHeight: 100 }} />
          </Spin>
        </div>
      </Card>
    );
  }

  // ========== 无状态 ==========
  if (!status) {
    return null;
  }

  // ========== 渲染状态 ==========
  const {
    filename,
    status: videoStatus,
    progress = 0,
    stage,
    total_frames,
    total_detections,
    keyframes_extracted,
    processing_time_seconds,
    error_message,
    created_at,
    started_at,
    completed_at,
  } = status;

  const isProcessing = videoStatus === 'pending' || videoStatus === 'processing';
  const isCompleted = videoStatus === 'completed';
  const isFailed = videoStatus === 'failed';

  return (
    <Card>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 标题和状态 */}
        <div>
          <Space align="center">
            {getStatusIcon(videoStatus)}
            <Title level={4} style={{ margin: 0 }}>
              {filename}
            </Title>
            <Tag color={getProgressColor(videoStatus)}>
              {STATUS_LABELS[videoStatus] || videoStatus}
            </Tag>
          </Space>
          <Text type="secondary" style={{ fontSize: 12 }}>
            创建于 {formatRelativeTime(created_at)}
          </Text>
        </div>

        {/* 进度条 */}
        <div>
          <Progress
            percent={progress}
            status={isFailed ? 'exception' : isCompleted ? 'success' : 'active'}
            strokeColor={getProgressColor(videoStatus)}
            style={{ marginBottom: 8 }}
          />

          {/* 当前阶段 */}
          {stage && isProcessing && (
            <Text type="secondary">
              {STAGE_LABELS[stage] || stage}
            </Text>
          )}
        </div>

        {/* 失败信息 */}
        {isFailed && error_message && (
          <Alert
            message="处理失败"
            description={error_message}
            type="error"
            showIcon
          />
        )}

        {/* 处理元数据（处理中或已完成时显示） */}
        {(isProcessing || isCompleted) && (
          <Row gutter={16}>
            {/* 总帧数 */}
            {total_frames !== null && total_frames !== undefined && (
              <Col span={6}>
                <Statistic
                  title="视频总帧数"
                  value={total_frames}
                  suffix="帧"
                  valueStyle={{ fontSize: 20 }}
                />
              </Col>
            )}

            {/* 检测数量 */}
            {total_detections !== null && total_detections !== undefined && (
              <Col span={6}>
                <Statistic
                  title="人物检测数"
                  value={total_detections}
                  suffix="个"
                  valueStyle={{ fontSize: 20, color: '#1890ff' }}
                />
              </Col>
            )}

            {/* 关键帧数量 */}
            {keyframes_extracted !== null && keyframes_extracted !== undefined && (
              <Col span={6}>
                <Statistic
                  title="关键帧数量"
                  value={keyframes_extracted}
                  suffix="个"
                  valueStyle={{ fontSize: 20, color: '#52c41a' }}
                />
              </Col>
            )}

            {/* 处理时间 */}
            {processing_time_seconds !== null &&
              processing_time_seconds !== undefined && (
                <Col span={6}>
                  <Statistic
                    title="处理时间"
                    value={formatProcessingTime(processing_time_seconds)}
                    valueStyle={{ fontSize: 20 }}
                  />
                </Col>
              )}
          </Row>
        )}

        {/* 时间信息 */}
        {(started_at || completed_at) && (
          <Space size="large" style={{ fontSize: 12, color: '#8c8c8c' }}>
            {started_at && (
              <Text type="secondary">
                开始时间: {formatRelativeTime(started_at)}
              </Text>
            )}
            {completed_at && (
              <Text type="secondary">
                完成时间: {formatRelativeTime(completed_at)}
              </Text>
            )}
          </Space>
        )}
      </Space>
    </Card>
  );
};

export default ProcessingStatus;
