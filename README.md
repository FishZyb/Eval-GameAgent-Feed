# Media Evaluation Service

基于 FastAPI 的多媒体评测服务，使用火山引擎 Doubao 大模型对图片和视频进行自动化质量评测（LLM-as-a-Judge）。

## 快速开始

1. 创建并填写 `.env`：

```bash
cp .env.example .env
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 运行服务：

```bash
uvicorn app.main:app --reload
```

## 主要技术栈

- FastAPI (异步)
- OpenAI SDK (`AsyncOpenAI`) 对接火山引擎 Doubao
- httpx 异步下载多媒体资源
- OpenCV & NumPy 进行视频抽帧与图像处理
- Tenacity 实现网络重试
- python-dotenv 管理环境变量

