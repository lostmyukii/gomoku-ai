# 智慧教室系统项目 README

融合学教王智能作业系统与强脑科技EEG头环打造的智慧教室解决方案，聚焦注意力实时采集、错题智能分析、个性化路径推荐、家校协同反馈。

---

## 🚀 快速启动

```bash
# 克隆仓库
$ git clone https://github.com/your-org/smart-classroom.git
$ cd smart-classroom

# 安装依赖
$ npm install            # 前端
$ pip install -r requirements.txt  # 后端/AI模块

# 启动开发环境
$ npm run dev            # 前端开发环境（Next.js）
$ uvicorn main:app --reload  # FastAPI后端接口服务
```

---

## 🧱 目录结构

```
智慧教室系统/
├── frontend/        # 教师仪表盘 + 家长端页面
├── backend/         # API服务、权限管理、路径推荐
├── eeg-collector/   # 强脑头环数据采集
├── pen-capture/     # 笔迹采集与OCR识别
├── ai-analyzer/     # 融合分析模块（GPT+OCR）
├── docs/            # Swagger接口、隐私协议、流程图
├── assets/          # UI图标、脑波图、结构图素材
└── README.md        # 项目说明（当前文件）
```

---

## 📦 主要依赖

### 后端
- Python 3.10+
- FastAPI
- Uvicorn
- OpenAI / Azure OpenAI SDK
- Tesseract OCR / EasyOCR

### 前端
- React 18 + Next.js
- ECharts（注意力热力图）
- TailwindCSS
- Web Bluetooth API

---

## 🔗 核心功能模块

| 模块 | 路径 | 描述 |
|------|------|------|
| EEG上传 | `/api/eeg/upload` | 上传学生专注力脑波数组 |
| 笔迹上传 | `/api/pen/trace` | 上传学生答题图片或矢量笔迹 |
| 报告查询 | `/api/report/:student_id` | 返回个体学习数据报告 |
| 个性化推荐 | `/api/path/recommend` | 推送补练 / 增项 / 脑控竞赛路径 |

---

## 🔐 数据与隐私规范

- 学生数据仅以 `student_id` 显示（不含姓名）
- 家长需通过OAuth授权访问孩子数据
- 所有传输 HTTPS，服务端数据加密存储

---

## 📷 示例截图

建议将以下文件放入 assets：
- `diagram_mechanism.png`：智慧课堂机制图
- `student_dashboard_sample.png`：仪表盘样例
- `parent_report_example.pdf`：家长报告样式

---

## 📅 开发进度建议

| 周 | 内容 |
|----|------|
| 1  | 设计原型、定义数据模型、蓝牙测试头环 |
| 2  | OCR对接+答题记录模块、笔迹热区分析 |
| 3  | 教师仪表盘开发、AI评语初版上线 |
| 4  | 家长小程序原型、个性化路径算法落地 |
| 5  | 教室试用部署、数据采集联调 |
| 6  | 期末课堂展示、家长开放日演示准备 |

---

## 📫 联系方式
如需试点部署、SDK授权、产品咨询，请联系：

- 教研团队负责人：[your.name@example.com]
- 技术支持：[dev-team@example.com]

---

_欢迎贡献建议、提交PR，共建智慧教育新生态。_

MIT License © 2025
