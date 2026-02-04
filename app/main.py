from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logger import setup_logger
from app.routers.evaluate import router as eval_router

# 初始化日志系统
logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理：启动和关闭时的操作。
    """
    # 启动时
    logger.info("🚀 Media Evaluation Service 正在启动...")
    yield
    # 关闭时
    logger.info("🛑 Media Evaluation Service 正在关闭...")


def create_app() -> FastAPI:
    """
    应用工厂函数，便于后续在单元测试或脚本中复用。
    """
    app = FastAPI(
        title="Media Evaluation Service",
        description="基于 FastAPI 和火山引擎 Doubao 的多媒体质量评测服务（LLM-as-a-Judge）。",
        version="0.1.0",
        lifespan=lifespan,
    )

    # 注册路由，统一加上 /api 前缀
    app.include_router(eval_router, prefix="/api", tags=["evaluation"])

    return app


# Uvicorn 入口
app = create_app()

