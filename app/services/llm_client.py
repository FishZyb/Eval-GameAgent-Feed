from typing import List

from openai import AsyncOpenAI

from app.core.config import settings


class LLMClient:
    """
    对 AsyncOpenAI 客户端进行简单封装，统一管理与火山引擎 Doubao 的交互逻辑。
    """

    def __init__(self) -> None:
        if not settings.API_KEY:
            raise RuntimeError("未检测到 ARK_API_KEY 环境变量，无法调用 Doubao 模型。")

        # 初始化异步客户端
        self._client = AsyncOpenAI(
            api_key=settings.API_KEY,
            base_url=settings.BASE_URL,
        )

    async def judge_media(
        self,
        system_prompt: str,
        user_prompt: str,
        base64_images: List[str],
    ) -> str:
        """
        调用 Doubao 大模型，对一组图片（图片或视频抽帧）进行质量评测。

        :param system_prompt: 角色设定 / 评测准则
        :param user_prompt: 用户问题描述
        :param base64_images: 已编码为 Base64 的图片列表（视频抽帧结果也以图片列表形式上传）
        :return: 大模型自然语言评测结果
        """
        # 构建多模态 message 内容：
        # - 第一段为文本（用户提示）
        # - 后续每段为一张图片；
        #   注意：火山引擎返回的错误信息中说明，仅支持 `text` / `image_url` / `video_url`，
        #   因此这里必须使用 `image_url` 作为 type，而不是 `input_image`。
        content: List[dict] = [
            {"type": "text", "text": user_prompt},
        ]
        for img_b64 in base64_images:
            content.append(
                {
                    # OpenAI / Doubao 多模态规范：使用 image_url + data URL 形式传入 Base64 图片
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}",
                    },
                }
            )

        response = await self._client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
        )

        # 取第一条候选的文本内容作为最终结果
        return response.choices[0].message.content or ""


# 提供一个全局可用的单例实例，避免每次请求都重新创建客户端
llm_client = LLMClient()

