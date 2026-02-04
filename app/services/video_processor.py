import base64
from pathlib import Path
from typing import List

import cv2
import numpy as np
from loguru import logger


def _resize_frame_keep_ratio(frame, target_short_side: int = 1080, max_long_side: int = 1920):
    """
    按短边等比缩放到 target_short_side 像素（Pure Vision 模式：高分辨率）。
    
    如果原图小于 max_long_side，则保持原画质（不放大）。
    
    :param frame: 输入帧（numpy array）
    :param target_short_side: 目标短边分辨率（默认1080，确保高清晰度）
    :param max_long_side: 如果原图长边小于此值，则保持原画（默认1920）
    :return: 缩放后的帧
    """
    h, w = frame.shape[:2]
    long_side = max(h, w)
    short_side = min(h, w)
    
    if short_side == 0:
        return frame
    
    # 如果原图长边小于 max_long_side，保持原画（不放大）
    if long_side < max_long_side:
        return frame
    
    # 否则按短边缩放到 target_short_side（确保高分辨率）
    scale = target_short_side / short_side
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    return resized


def _frame_to_base64(frame, quality: int = 85):
    """
    将帧编码为 JPEG 格式的 Base64 字符串。
    
    :param frame: 输入帧
    :param quality: JPEG 质量（1-100，默认85平衡清晰度和文件大小，避免Request Entity Too Large）
    :return: Base64 编码的字符串
    """
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    success, buffer = cv2.imencode(".jpg", frame, encode_params)
    if not success:
        raise ValueError("帧编码失败")
    jpg_bytes = buffer.tobytes()
    return base64.b64encode(jpg_bytes).decode("utf-8")


def video_to_base64_frames(
    video_path: str,
    max_frames: int = 100,
    sampling_fps: float = 4.0,
    save_debug_frames: bool = False,
) -> List[str]:
    """
    将视频按「Pure Vision + 全时长均匀采样」策略抽帧，并输出为 Base64 字符串列表。
    
    Pure Vision 模式特性：
    1. 高分辨率：短边至少1080p（原图小于1920px则保持原画）
    2. 全时长覆盖：使用均匀采样确保覆盖从0s到结尾的整个视频，无截断
    3. 纯视觉：仅保留全屏画面，移除所有裁剪逻辑，相信LMM的原生视觉理解能力
    
    返回格式：[Frame1_Full, Frame2_Full, Frame3_Full, ...]
    
    :param video_path: 视频文件路径
    :param max_frames: 目标采样帧数（默认100，会根据视频时长均匀分布）
    :param sampling_fps: 抽帧频率参考值（每秒多少帧，默认4.0，实际采样会根据视频时长均匀分布）
    :param save_debug_frames: 是否保存调试图片到本地（默认False）
    :return: Base64 编码的图片列表
    """
    filename = Path(video_path).stem  # 获取不带扩展名的文件名
    logger.info(f"🚀 Strategy: Pure Vision (Full Frame Only)")
    logger.info(f"📹 Processing video: {filename}...")
    
    # 如果开启调试模式，创建保存目录
    debug_dir = None
    if save_debug_frames:
        debug_dir = Path("logs/debug_frames") / filename
        debug_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"🔍 Debug mode enabled: saving frames to {debug_dir.absolute()}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件：{video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        video_fps = 25.0
        logger.warning(f"无法获取视频FPS，使用默认值 {video_fps}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / video_fps if video_fps > 0 else 0
    
    # 计算目标采样帧数：根据视频时长和sampling_fps计算，但不超过max_frames上限
    target_frame_count = min(max_frames, int(video_duration * sampling_fps))
    if target_frame_count < 1:
        target_frame_count = 1
    
    # 使用 np.linspace 生成均匀分布的帧索引，确保覆盖整个视频（从0到total_frames-1）
    if total_frames <= 1:
        frame_indices = [0]
    else:
        frame_indices = np.linspace(0, total_frames - 1, num=target_frame_count, dtype=int)
    
    logger.info(
        f"📊 Coverage: Uniformly sampled {len(frame_indices)} frames from {video_duration:.2f}s video. "
        f"No truncation. (FPS={video_fps:.2f}, Total frames={total_frames})"
    )

    frames_base64: List[str] = []
    
    # 遍历均匀分布的帧索引
    for idx, frame_idx in enumerate(frame_indices):
        # 将读取位置跳到指定帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = cap.read()
        if not success:
            logger.warning(f"⚠️ Failed to read frame at index {frame_idx}")
            continue

        # 缩放全屏帧到高分辨率（短边至少1080p）
        full_frame = _resize_frame_keep_ratio(frame, target_short_side=1080, max_long_side=1920)
        h, w = full_frame.shape[:2]
        
        # 编码为Base64
        full_b64 = _frame_to_base64(full_frame, quality=85)
        frames_base64.append(full_b64)
        
        # 保存调试图片
        if save_debug_frames and debug_dir:
            frame_number = idx + 1
            full_path = debug_dir / f"frame_{frame_number:03d}_full.jpg"
            cv2.imwrite(str(full_path), full_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            logger.debug(f"💾 Saved debug frame: {full_path.name}")

    cap.release()
    
    # 如果开启了调试模式，记录保存的图片数量
    if save_debug_frames and debug_dir:
        saved_files = list(debug_dir.glob("*.jpg"))
        logger.info(f"💾 Debug frames saved: {len(saved_files)} images in {debug_dir.absolute()}")
    
    # 记录最终生成的图片数量和分辨率信息
    total_images = len(frames_base64)
    if total_images > 0:
        # 计算总数据量（Base64编码后的字符串总长度）
        total_base64_size = sum(len(img_b64) for img_b64 in frames_base64)
        total_size_mb = total_base64_size / (1024 * 1024)  # 转换为MB
        
        # 获取第一张全屏图的分辨率作为参考
        try:
            sample_frame = cv2.imdecode(
                np.frombuffer(base64.b64decode(frames_base64[0]), np.uint8),
                cv2.IMREAD_COLOR
            )
            if sample_frame is not None:
                h, w = sample_frame.shape[:2]
                
                logger.info(
                    f"✅ Pure Vision Mode: Generated {total_images} full frames for {filename}, "
                    f"resolution={w}x{h}, coverage={video_duration:.2f}s (0s to end), "
                    f"total_size≈{total_size_mb:.2f} MB"
                )
            else:
                logger.info(
                    f"✅ Pure Vision Mode: Generated {total_images} full frames for {filename}, "
                    f"coverage={video_duration:.2f}s (0s to end), total_size≈{total_size_mb:.2f} MB"
                )
        except Exception as e:
            logger.info(
                f"✅ Pure Vision Mode: Generated {total_images} full frames for {filename}, "
                f"coverage={video_duration:.2f}s (0s to end), total_size≈{total_size_mb:.2f} MB "
                f"(resolution parse failed: {e})"
            )
        
        # 如果数据量过大，给出警告
        if total_size_mb > 50:
            logger.warning(
                f"⚠️ 数据量较大（{total_size_mb:.2f} MB），可能超过API限制。"
                f"建议：降低max_frames"
            )
    else:
        logger.warning(f"⚠️ 未抽取到任何帧，请检查视频文件: {filename}")

    return frames_base64
