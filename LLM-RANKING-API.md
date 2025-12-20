# LLM 排行榜 API 文档

基于 Chatbot Arena 数据的 LLM 排行榜实现指南。

## 数据源地址

```
# jsDelivr CDN（国内推荐）
https://cdn.jsdelivr.net/gh/SmallAi-API/LLM-Ranking@main/data/

# GitHub Raw
https://raw.githubusercontent.com/SmallAi-API/LLM-Ranking/main/data/
```

---

## 可用榜单

### 1. 文本模型榜单

| 文件 | 说明 |
|------|------|
| `leaderboard-text.json` | 文本模型排行榜 |
| `leaderboard-text-style-control.json` | 文本模型排行榜（风格控制） |

**分类 (29个)：**

| 分类 | 说明 |
|------|------|
| `full` | 综合排名 |
| `coding` | 编程能力 |
| `math` | 数学能力 |
| `creative_writing` | 创意写作 |
| `hard_6` | 困难问题 |
| `hard_english_6` | 困难英语问题 |
| `multiturn` | 多轮对话 |
| `long_user` | 长文本处理 |
| `if` | 指令遵循 |
| `no_refusal` | 无拒绝 |
| `no_short` | 非短回答 |
| `no_tie` | 无平局 |
| `expert` | 专家级问题 |
| `chinese` | 中文能力 |
| `english` | 英语能力 |
| `japanese` | 日语能力 |
| `korean` | 韩语能力 |
| `french` | 法语能力 |
| `german` | 德语能力 |
| `spanish` | 西班牙语能力 |
| `russian` | 俄语能力 |
| `industry_software_and_it_services` | 软件与IT |
| `industry_medicine_and_healthcare` | 医疗健康 |
| `industry_legal_and_government` | 法律政务 |
| `industry_business_and_management_and_financial_operations` | 商业金融 |
| `industry_mathematical` | 数学行业 |
| `industry_life_and_physical_and_social_science` | 科学领域 |
| `industry_entertainment_and_sports_and_media` | 娱乐媒体 |
| `industry_writing_and_literature_and_language` | 写作文学 |

---

### 2. 视觉模型榜单

| 文件 | 说明 |
|------|------|
| `leaderboard-vision.json` | 视觉模型排行榜 |
| `leaderboard-vision-style-control.json` | 视觉模型排行榜（风格控制） |

**分类 (10个)：**

| 分类 | 说明 |
|------|------|
| `full` | 综合排名 |
| `captioning` | 图片描述 |
| `chinese` | 中文视觉 |
| `english` | 英文视觉 |
| `creative_writing_vision` | 创意写作（视觉） |
| `diagram` | 图表理解 |
| `entity_recognition` | 实体识别 |
| `homework` | 作业解答 |
| `humor` | 幽默理解 |
| `ocr` | 文字识别 |

---

### 3. 图像生成模型榜单

| 文件 | 说明 |
|------|------|
| `leaderboard-image.json` | 图像生成模型排行榜 |

**分类 (3个)：**

| 分类 | 说明 |
|------|------|
| `full` | 综合排名 |
| `is_preset_generation` | 预设提示词生成 |
| `not_preset_generation` | 自由提示词生成 |

---

### 4. 模型定价信息

| 文件 | 说明 |
|------|------|
| `scatterplot-data.json` | 模型定价与元信息 |

---

## 数据结构

### 排行榜数据 (leaderboard-*.json)

```json
{
  "分类名": {
    "模型API名": {
      "rating": 1495.76,        // Arena 评分 (Elo)
      "rating_q975": 1518.07,   // 95% 置信区间上限
      "rating_q025": 1473.45    // 95% 置信区间下限
    }
  }
}
```

### 定价数据 (scatterplot-data.json)

```json
[
  {
    "name": "GPT-4o",                           // 显示名称
    "model_api_name": "chatgpt-4o-latest",      // API 名称（与排行榜关联的 key）
    "input_token_price": "2.5",                 // 输入价格 ($/1M tokens)
    "output_token_price": "10",                 // 输出价格 ($/1M tokens)
    "organization": "OpenAI",                   // 厂商
    "license": "Proprietary",                   // 许可证
    "price_source": "https://...",              // 价格来源
    "model_source": "https://...",              // 模型来源
    "hidden": false                             // 是否隐藏
  }
]
```

---

## React 实现示例

### 1. 类型定义

```typescript
// types/leaderboard.ts

// 单个模型评分
export interface ModelRating {
  rating: number;
  rating_q975: number;
  rating_q025: number;
}

// 排行榜数据结构
export interface LeaderboardData {
  [category: string]: {
    [modelName: string]: ModelRating;
  };
}

// 定价数据
export interface ModelPricing {
  name: string;
  model_api_name: string;
  input_token_price: string;
  output_token_price: string;
  organization: string;
  license: string;
  price_source: string;
  model_source: string;
  hidden?: boolean;
}

// 排行榜展示项
export interface LeaderboardItem {
  rank: number;
  modelName: string;
  displayName?: string;
  rating: number;
  ratingLower: number;
  ratingUpper: number;
  organization?: string;
  inputPrice?: number;
  outputPrice?: number;
}
```

### 2. 数据获取 Hook

```typescript
// hooks/useLeaderboard.ts
import { useState, useEffect } from 'react';
import type { LeaderboardData, ModelPricing } from '../types/leaderboard';

const CDN_BASE = 'https://cdn.jsdelivr.net/gh/SmallAi-API/LLM-Ranking@main/data';
const FALLBACK_BASE = 'https://raw.githubusercontent.com/SmallAi-API/LLM-Ranking/main/data';

async function fetchWithFallback<T>(path: string): Promise<T> {
  try {
    const res = await fetch(`${CDN_BASE}${path}`);
    if (!res.ok) throw new Error('CDN failed');
    return res.json();
  } catch {
    const res = await fetch(`${FALLBACK_BASE}${path}`);
    return res.json();
  }
}

export function useLeaderboard(type: 'text' | 'vision' | 'image' = 'text') {
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [pricing, setPricing] = useState<ModelPricing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const [leaderboard, priceData] = await Promise.all([
          fetchWithFallback<LeaderboardData>(`/leaderboard-${type}.json`),
          fetchWithFallback<ModelPricing[]>('/scatterplot-data.json'),
        ]);
        setData(leaderboard);
        setPricing(priceData);
      } catch (e) {
        setError(e as Error);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [type]);

  return { data, pricing, loading, error };
}
```

### 3. 数据处理工具

```typescript
// utils/leaderboard.ts
import type { LeaderboardData, ModelPricing, LeaderboardItem } from '../types/leaderboard';

export function getLeaderboardItems(
  data: LeaderboardData,
  category: string,
  pricing: ModelPricing[]
): LeaderboardItem[] {
  const categoryData = data[category];
  if (!categoryData) return [];

  // 创建定价映射
  const priceMap = new Map(
    pricing.map(p => [p.model_api_name, p])
  );

  // 转换并排序
  const items = Object.entries(categoryData)
    .map(([modelName, scores]) => {
      const priceInfo = priceMap.get(modelName);
      return {
        rank: 0,
        modelName,
        displayName: priceInfo?.name || modelName,
        rating: Math.round(scores.rating),
        ratingLower: Math.round(scores.rating_q025),
        ratingUpper: Math.round(scores.rating_q975),
        organization: priceInfo?.organization,
        inputPrice: priceInfo ? parseFloat(priceInfo.input_token_price) : undefined,
        outputPrice: priceInfo ? parseFloat(priceInfo.output_token_price) : undefined,
      };
    })
    .sort((a, b) => b.rating - a.rating);

  // 添加排名
  items.forEach((item, index) => {
    item.rank = index + 1;
  });

  return items;
}

// 获取所有分类
export function getCategories(data: LeaderboardData): string[] {
  return Object.keys(data);
}
```

### 4. 排行榜组件

```tsx
// components/Leaderboard.tsx
import { useState } from 'react';
import { useLeaderboard } from '../hooks/useLeaderboard';
import { getLeaderboardItems, getCategories } from '../utils/leaderboard';

interface Props {
  type?: 'text' | 'vision' | 'image';
}

export function Leaderboard({ type = 'text' }: Props) {
  const { data, pricing, loading, error } = useLeaderboard(type);
  const [category, setCategory] = useState('full');

  if (loading) return <div>加载中...</div>;
  if (error) return <div>加载失败: {error.message}</div>;
  if (!data) return null;

  const categories = getCategories(data);
  const items = getLeaderboardItems(data, category, pricing);

  return (
    <div className="leaderboard">
      {/* 分类选择 */}
      <div className="category-tabs">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={category === cat ? 'active' : ''}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* 排行榜表格 */}
      <table>
        <thead>
          <tr>
            <th>排名</th>
            <th>模型</th>
            <th>厂商</th>
            <th>评分</th>
            <th>置信区间</th>
            <th>输入价格</th>
            <th>输出价格</th>
          </tr>
        </thead>
        <tbody>
          {items.map(item => (
            <tr key={item.modelName}>
              <td>{item.rank}</td>
              <td>{item.displayName}</td>
              <td>{item.organization || '-'}</td>
              <td><strong>{item.rating}</strong></td>
              <td>{item.ratingLower} - {item.ratingUpper}</td>
              <td>{item.inputPrice ? `$${item.inputPrice}` : '-'}</td>
              <td>{item.outputPrice ? `$${item.outputPrice}` : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### 5. 多榜单页面

```tsx
// pages/Rankings.tsx
import { useState } from 'react';
import { Leaderboard } from '../components/Leaderboard';

type TabType = 'text' | 'vision' | 'image';

const TABS: { key: TabType; label: string }[] = [
  { key: 'text', label: '文本模型' },
  { key: 'vision', label: '视觉模型' },
  { key: 'image', label: '图像生成' },
];

export function Rankings() {
  const [activeTab, setActiveTab] = useState<TabType>('text');

  return (
    <div className="rankings-page">
      <h1>LLM 排行榜</h1>

      {/* 榜单切换 */}
      <div className="tabs">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={activeTab === tab.key ? 'active' : ''}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 当前榜单 */}
      <Leaderboard type={activeTab} />
    </div>
  );
}
```

---

## 性价比计算

```typescript
// 计算性价比得分 (评分/平均价格)
function calculateValueScore(item: LeaderboardItem): number | null {
  if (!item.inputPrice || !item.outputPrice) return null;
  const avgPrice = (item.inputPrice + item.outputPrice) / 2;
  return item.rating / avgPrice;
}

// 性价比排行榜
function getValueRanking(items: LeaderboardItem[]): LeaderboardItem[] {
  return items
    .filter(item => item.inputPrice && item.outputPrice)
    .map(item => ({
      ...item,
      valueScore: calculateValueScore(item),
    }))
    .sort((a, b) => (b.valueScore || 0) - (a.valueScore || 0));
}
```

---

## 评分说明

| 字段 | 含义 |
|------|------|
| `rating` | Elo 评分，基于用户两两对比投票计算，越高越强 |
| `rating_q975` | 95% 置信区间上限 |
| `rating_q025` | 95% 置信区间下限 |

**评分参考：**
- 1400+ = 顶尖模型
- 1300+ = 优秀模型
- 1200+ = 良好模型
- 1200以下 = 一般模型

**置信区间用途：**
- 区间越窄 = 数据越多、越可靠
- 两个模型区间重叠 = 差距不显著

---

## 数据更新频率

数据由 LMArena 团队维护，通常每周更新。可通过 GitHub 仓库的 commit 历史查看最近更新时间。
