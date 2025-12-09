/**
 * ConfigPanel Component
 *
 * 视频处理参数配置面板
 *
 * 功能特性：
 * 1. 三个预设模板（快速/标准/高质量）
 * 2. 采样率滑块（1-10）
 * 3. 最大关键帧数输入框（10-500）
 * 4. 置信度阈值滑块（0.1-0.9）
 * 5. Tooltip 提示帮助用户理解参数
 *
 * @module components/ConfigPanel
 *
 * @example
 * ```tsx
 * const [config, setConfig] = useState(DEFAULT_CONFIG);
 *
 * <ConfigPanel
 *   value={config}
 *   onChange={setConfig}
 *   disabled={uploading}
 * />
 * ```
 */

import React from 'react';
import { Slider, InputNumber, Form, Collapse, Space, Card, Typography, Tooltip } from 'antd';
import {
  ThunderboltOutlined,
  DashboardOutlined,
  CrownOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import type { ProcessingConfig } from '@/api/types';
import { CONFIG_PRESETS } from '@/utils/constants';

const { Text, Title } = Typography;
const { Panel } = Collapse;

/**
 * 组件Props接口
 */
interface ConfigPanelProps {
  /** 当前配置值 */
  value: ProcessingConfig;

  /** 配置变更回调 */
  onChange: (config: ProcessingConfig) => void;

  /** 是否禁用（上传中时禁用） */
  disabled?: boolean;
}

/**
 * 预设卡片Props
 */
interface PresetCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  config: Omit<ProcessingConfig, 'label' | 'description'>;
  active: boolean;
  onClick: () => void;
  disabled?: boolean;
}

/**
 * 预设配置卡片
 */
const PresetCard: React.FC<PresetCardProps> = ({
  icon,
  title,
  description,
  active,
  onClick,
  disabled,
}) => (
  <Card
    hoverable={!disabled}
    size="small"
    onClick={disabled ? undefined : onClick}
    style={{
      borderColor: active ? '#1890ff' : undefined,
      backgroundColor: active ? '#e6f7ff' : undefined,
      cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.6 : 1,
      transition: 'all 0.3s',
    }}
    bodyStyle={{ padding: '16px' }}
  >
    <Space direction="vertical" size="small" style={{ width: '100%' }}>
      <Space>
        {icon}
        <Text strong style={{ fontSize: 16 }}>
          {title}
        </Text>
      </Space>
      <Text type="secondary" style={{ fontSize: 12 }}>
        {description}
      </Text>
    </Space>
  </Card>
);

/**
 * ConfigPanel 组件
 *
 * @component
 * @description
 * 使用 Ant Design Form + Collapse 实现可折叠的配置面板
 * 支持预设模板快速切换和自定义参数调整
 */
export const ConfigPanel: React.FC<ConfigPanelProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const [form] = Form.useForm();

  /**
   * 判断当前配置是否匹配某个预设
   */
  const getActivePreset = (): string | null => {
    for (const [key, preset] of Object.entries(CONFIG_PRESETS)) {
      if (
        preset.sampleRate === value.sampleRate &&
        preset.maxFrames === value.maxFrames &&
        preset.confidenceThreshold === value.confidenceThreshold
      ) {
        return key;
      }
    }
    return null; // 自定义配置
  };

  /**
   * 应用预设配置
   */
  const handlePresetClick = (presetKey: keyof typeof CONFIG_PRESETS) => {
    const preset = CONFIG_PRESETS[presetKey];
    const newConfig: ProcessingConfig = {
      sampleRate: preset.sampleRate,
      maxFrames: preset.maxFrames,
      confidenceThreshold: preset.confidenceThreshold,
    };

    form.setFieldsValue(newConfig);
    onChange(newConfig);
  };

  /**
   * 表单值变化回调
   */
  const handleValuesChange = (_: any, allValues: ProcessingConfig) => {
    onChange(allValues);
  };

  const activePreset = getActivePreset();

  return (
    <Collapse
      defaultActiveKey={['1']}
      bordered={false}
      style={{ background: 'transparent' }}
    >
      <Panel
        header={
          <Space>
            <DashboardOutlined />
            <Text strong>处理参数配置</Text>
          </Space>
        }
        key="1"
      >
        {/* 预设模板 */}
        <div style={{ marginBottom: 24 }}>
          <Title level={5} style={{ marginBottom: 12 }}>
            预设模板
            <Tooltip title="选择预设模板可快速配置常用参数组合">
              <InfoCircleOutlined style={{ marginLeft: 8, color: '#8c8c8c' }} />
            </Tooltip>
          </Title>

          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <PresetCard
              icon={<ThunderboltOutlined style={{ color: '#faad14' }} />}
              title="快速模式"
              description="快速处理，适合预览（采样率高，帧数少）"
              config={CONFIG_PRESETS.fast}
              active={activePreset === 'fast'}
              onClick={() => handlePresetClick('fast')}
              disabled={disabled}
            />

            <PresetCard
              icon={<DashboardOutlined style={{ color: '#1890ff' }} />}
              title="标准模式"
              description="平衡速度和质量，推荐使用"
              config={CONFIG_PRESETS.standard}
              active={activePreset === 'standard'}
              onClick={() => handlePresetClick('standard')}
              disabled={disabled}
            />

            <PresetCard
              icon={<CrownOutlined style={{ color: '#52c41a' }} />}
              title="高质量模式"
              description="详细处理，耗时较长（采样率低，帧数多）"
              config={CONFIG_PRESETS.high}
              active={activePreset === 'high'}
              onClick={() => handlePresetClick('high')}
              disabled={disabled}
            />
          </Space>
        </div>

        {/* 自定义参数 */}
        <Form
          form={form}
          layout="vertical"
          initialValues={value}
          onValuesChange={handleValuesChange}
          disabled={disabled}
        >
          {/* 采样率 */}
          <Form.Item
            label={
              <Space>
                <Text>采样率（每N帧处理1帧）</Text>
                <Tooltip title="值越小处理越慢但结果越精细。推荐：快速10，标准5，高质量1">
                  <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
                </Tooltip>
              </Space>
            }
            name="sampleRate"
            rules={[
              { required: true, message: '请设置采样率' },
              { type: 'number', min: 1, max: 10, message: '采样率范围：1-10' },
            ]}
          >
            <Slider
              min={1}
              max={10}
              marks={{
                1: '1（慢）',
                5: '5（中）',
                10: '10（快）',
              }}
              tooltip={{ formatter: (val) => `每${val}帧` }}
            />
          </Form.Item>

          {/* 最大关键帧数 */}
          <Form.Item
            label={
              <Space>
                <Text>最大关键帧数</Text>
                <Tooltip title="最多提取多少个关键帧。范围：10-500">
                  <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
                </Tooltip>
              </Space>
            }
            name="maxFrames"
            rules={[
              { required: true, message: '请设置最大关键帧数' },
              { type: 'number', min: 10, max: 500, message: '范围：10-500' },
            ]}
          >
            <InputNumber
              min={10}
              max={500}
              style={{ width: '100%' }}
              addonAfter="帧"
              placeholder="输入最大帧数"
            />
          </Form.Item>

          {/* 置信度阈值 */}
          <Form.Item
            label={
              <Space>
                <Text>检测置信度阈值</Text>
                <Tooltip title="人物检测的置信度阈值。越高过滤越严格，推荐0.5">
                  <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
                </Tooltip>
              </Space>
            }
            name="confidenceThreshold"
            rules={[
              { required: true, message: '请设置置信度阈值' },
              { type: 'number', min: 0.1, max: 0.9, message: '范围：0.1-0.9' },
            ]}
          >
            <Slider
              min={0.1}
              max={0.9}
              step={0.1}
              marks={{
                0.1: '0.1（松）',
                0.5: '0.5（中）',
                0.9: '0.9（严）',
              }}
              tooltip={{ formatter: (val) => `${val?.toFixed(1)}` }}
            />
          </Form.Item>
        </Form>

        {/* 当前配置提示 */}
        {!activePreset && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            当前为自定义配置
          </Text>
        )}
      </Panel>
    </Collapse>
  );
};

export default ConfigPanel;
