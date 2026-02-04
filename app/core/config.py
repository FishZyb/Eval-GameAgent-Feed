from functools import lru_cache
from typing import Optional

import os
from pydantic import BaseModel
from dotenv import load_dotenv


# 预加载 .env 文件中的环境变量（如果存在）
load_dotenv()


class Settings(BaseModel):
    """
    全局配置对象，包含火山引擎 Doubao 相关配置。

    注意：
    - BASE_URL 和 MODEL_NAME 为固定配置；
    - API_KEY 从环境变量 ARK_API_KEY 读取，不要在代码中硬编码。
    """

    # 火山引擎 Ark 网关地址（固定）
    BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"

    # Doubao 模型名称（由题目要求给定）
    MODEL_NAME: str = "doubao-seed-1-8-251228"

    # 从环境变量中读取 API Key
    API_KEY: Optional[str] = os.getenv("ARK_API_KEY")
    
    # 调试配置：是否保存发送给 LLM 的图片帧（用于调试裁剪质量）
    SAVE_DEBUG_FRAMES: bool = os.getenv("SAVE_DEBUG_FRAMES", "True").lower() == "true"


@lru_cache()
def get_settings() -> Settings:
    """
    使用 lru_cache 缓存配置对象，避免在每次请求时重复创建。
    """
    return Settings()


# 对外暴露一个全局可用的 settings 实例，方便直接导入使用
settings = get_settings()

