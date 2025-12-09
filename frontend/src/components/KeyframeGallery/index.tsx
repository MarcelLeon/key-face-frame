/**
 * KeyframeGallery Component
 *
 * 关键帧图片展示画廊组件
 *
 * 功能特性：
 * 1. 响应式网格布局（手机2列、平板3列、桌面4列）
 * 2. 图片懒加载（Ant Design Image自带）
 * 3. 点击放大预览（Image.PreviewGroup）
 * 4. 排序功能（按评分/时间戳）
 * 5. 空状态处理
 * 6. 关键帧元数据展示（帧号、时间、评分）
 *
 * @module components/KeyframeGallery
 *
 * @example
 * ```tsx
 * <KeyframeGallery
 *   keyframes={status.keyframes || []}
 *   videoId={videoId}
 *   loading={loading}
 * />
 * ```
 */

import React, { useState, useMemo } from 'react';
import {
  Image,
  Card,
  Row,
  Col,
  Select,
  Tag,
  Space,
  Empty,
  Typography,
  Skeleton,
} from 'antd';
import {
  TrophyOutlined,
  ClockCircleOutlined,
  PictureOutlined,
} from '@ant-design/icons';
import type { KeyframeInfo } from '@/api/types';
import { API_BASE_URL } from '@/utils/constants';
import { formatTimestamp } from '@/utils/formatters';

const { Text } = Typography;
const { Meta } = Card;

/**
 * 组件Props接口
 */
interface KeyframeGalleryProps {
  /** 关键帧列表 */
  keyframes: KeyframeInfo[];

  /** 视频ID（用于构建图片URL） */
  videoId: string;

  /** 是否正在加载 */
  loading?: boolean;
}

/**
 * 排序选项类型
 */
type SortOption = 'score' | 'timestamp';

/**
 * KeyframeGallery 组件
 *
 * @component
 * @description
 * 使用 Ant Design 的 Image + Card 实现关键帧画廊
 * 支持响应式布局和图片预览
 */
export const KeyframeGallery: React.FC<KeyframeGalleryProps> = ({
  keyframes,
  videoId,
  loading = false,
}) => {
  // ========== State ==========
  const [sortBy, setSortBy] = useState<SortOption>('score');

  /**
   * 构建图片URL
   *
   * @param filename - 图片文件名
   * @returns 完整的图片URL
   */
  const getImageUrl = (filename: string): string => {
    return `${API_BASE_URL}/files/video-${videoId}/keyframes/${filename}`;
  };

  /**
   * 排序逻辑（useMemo缓存结果，避免重复计算）
   */
  const sortedKeyframes = useMemo(() => {
    if (!keyframes || keyframes.length === 0) return [];

    return [...keyframes].sort((a, b) => {
      if (sortBy === 'score') {
        // 按评分降序排列（高分在前）
        return b.score - a.score;
      }
      // 按时间戳升序排列（早的在前）
      return a.timestamp - b.timestamp;
    });
  }, [keyframes, sortBy]);

  // ========== 加载状态 ==========
  if (loading) {
    return (
      <Row gutter={[16, 16]}>
        {[...Array(8)].map((_, index) => (
          <Col xs={12} sm={8} md={6} lg={6} key={index}>
            <Card>
              <Skeleton.Image active style={{ width: '100%', height: 200 }} />
              <Skeleton active paragraph={{ rows: 2 }} />
            </Card>
          </Col>
        ))}
      </Row>
    );
  }

  // ========== 空状态 ==========
  if (!keyframes || keyframes.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description="暂无关键帧数据"
        style={{ padding: '60px 0' }}
      />
    );
  }

  // ========== 渲染画廊 ==========
  return (
    <div style={{ width: '100%' }}>
      {/* 工具栏 */}
      <div
        style={{
          marginBottom: 16,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Space>
          <PictureOutlined />
          <Text strong>关键帧画廊</Text>
          <Tag color="blue">{keyframes.length} 个关键帧</Tag>
        </Space>

        <Select
          value={sortBy}
          onChange={setSortBy}
          style={{ width: 200 }}
          options={[
            {
              value: 'score',
              label: (
                <Space>
                  <TrophyOutlined />
                  按评分排序（高→低）
                </Space>
              ),
            },
            {
              value: 'timestamp',
              label: (
                <Space>
                  <ClockCircleOutlined />
                  按时间排序（早→晚）
                </Space>
              ),
            },
          ]}
        />
      </div>

      {/* 图片网格 */}
      <Image.PreviewGroup>
        <Row gutter={[16, 16]}>
          {sortedKeyframes.map((kf) => (
            <Col
              xs={12}  // 手机：2列
              sm={8}   // 平板：3列
              md={6}   // 桌面：4列
              lg={6}
              key={kf.frame_index}
            >
              <Card
                hoverable
                cover={
                  <Image
                    src={getImageUrl(kf.filename)}
                    alt={`帧 ${kf.frame_index}`}
                    placeholder={
                      <div
                        style={{
                          width: '100%',
                          height: 200,
                          background: '#f0f0f0',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <PictureOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                      </div>
                    }
                    style={{
                      width: '100%',
                      height: 200,
                      objectFit: 'cover',
                    }}
                  />
                }
                bodyStyle={{ padding: '12px' }}
              >
                <Meta
                  title={
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Text strong style={{ fontSize: 14 }}>
                        帧 {kf.frame_index}
                      </Text>
                      <Tag
                        color={kf.score >= 0.8 ? 'green' : kf.score >= 0.6 ? 'blue' : 'default'}
                        style={{ margin: 0 }}
                      >
                        {kf.score.toFixed(3)}
                      </Tag>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        <ClockCircleOutlined /> {formatTimestamp(kf.timestamp)}
                      </Text>
                      {kf.track_id !== null && kf.track_id !== undefined && (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          追踪ID: {kf.track_id}
                        </Text>
                      )}
                    </Space>
                  }
                />
              </Card>
            </Col>
          ))}
        </Row>
      </Image.PreviewGroup>
    </div>
  );
};

export default KeyframeGallery;
