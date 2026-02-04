import io
import tempfile
from typing import Tuple

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed


# ===========================
# 公共 HTTP 客户端配置
# ===========================

DEFAULT_TIMEOUT = 30.0  # 秒


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def _fetch(url: str) -> Tuple[bytes, str]:
    """
    内部通用下载函数，带重试。

    :param url: 资源的网络地址
    :return: (content_bytes, content_type)
    """
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url, follow_redirects=True)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        return resp.content, content_type


async def download_image_to_bytes(url: str) -> io.BytesIO:
    """
    下载图片到内存（BytesIO）。

    适用场景：
    - 图片文件普遍较小，可以直接读入内存，后续再做 Base64 编码。
    """
    content, content_type = await _fetch(url)

    # 简单的类型校验（非强制，可以根据业务需要调整）
    if "image" not in content_type:
        raise ValueError(f"URL 不是图片资源，Content-Type={content_type}")

    return io.BytesIO(content)


async def download_video_to_tempfile(url: str) -> str:
    """
    下载视频到临时文件，返回临时文件路径。

    设计要点：
    - 使用 tempfile.NamedTemporaryFile，并设置 delete=False；
    - 通过流式写入的方式避免一次性将整个视频读入内存。
    """
    # 这里仍然复用 _fetch 获取字节内容。
    # 如果你希望做到「真正的分块流式下载」，可以切换为 client.stream("GET", url)。
    content, content_type = await _fetch(url)

    if "video" not in content_type:
        # 某些场景下 Content-Type 可能缺失或不标准，这里仅作一个温和的校验
        # 也可以改为仅记录日志而不是抛异常。
        raise ValueError(f"URL 可能不是视频资源，Content-Type={content_type}")

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    with tmp_file as f:
        # 真正写入到磁盘文件
        f.write(content)

    return tmp_file.name

