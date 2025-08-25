"""
模型管理器

负责AI模型的下载、加载、缓存和版本管理。
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from loguru import logger

try:
    import torch
    from transformers import (
        AutoTokenizer, 
        AutoModelForCausalLM, 
        GenerationConfig,
        TextStreamer
    )
    from huggingface_hub import hf_hub_download, HfFolder, snapshot_download
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("transformers库未安装，AI功能将受限")

from ..core.config_models import ModelConfiguration


class ModelManager:
    """AI模型管理器"""
    
    def __init__(self, config: ModelConfiguration, cache_dir: Optional[str] = None):
        """
        初始化模型管理器
        
        Args:
            config: 模型配置
            cache_dir: 缓存目录
        """
        self.config = config
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "sysgraph" / "models"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.tokenizer = None
        self.generation_config = None
        self.device = None
        
        self._model_info = {}
        self._load_status = "unloaded"  # unloaded, loading, loaded, error
    
    def _get_device(self) -> str:
        """获取运行设备"""
        if not HAS_TRANSFORMERS:
            return "cpu"
            
        if self.config.device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        else:
            return self.config.device
    
    async def download_model(self, progress_callback: Optional[callable] = None) -> bool:
        """
        下载模型
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            bool: 下载是否成功
        """
        if not HAS_TRANSFORMERS:
            logger.error("transformers库未安装，无法下载模型")
            return False
        
        try:
            logger.info(f"开始下载模型: {self.config.model_name}")
            
            # 设置缓存目录
            model_cache_dir = self.cache_dir / self.config.model_name.replace("/", "_")
            
            if progress_callback:
                progress_callback({"status": "downloading", "progress": 0, "message": "准备下载模型"})
            
            # 下载模型文件
            loop = asyncio.get_event_loop()
            
            def download_snapshot():
                return snapshot_download(
                    repo_id=self.config.model_name,
                    cache_dir=str(model_cache_dir),
                    resume_download=True,
                    local_files_only=False
                )
            
            model_path = await loop.run_in_executor(None, download_snapshot)
            
            if progress_callback:
                progress_callback({"status": "downloaded", "progress": 100, "message": "模型下载完成"})
            
            # 保存模型信息
            self._save_model_info(model_path)
            
            logger.info(f"模型下载完成: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"下载模型失败: {e}")
            if progress_callback:
                progress_callback({"status": "error", "progress": 0, "message": f"下载失败: {e}"})
            return False
    
    def _save_model_info(self, model_path: str) -> None:
        """保存模型信息"""
        try:
            model_info = {
                "model_name": self.config.model_name,
                "model_path": model_path,
                "download_time": datetime.now().isoformat(),
                "device": self._get_device(),
                "config": self.config.dict()
            }
            
            info_file = self.cache_dir / "model_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(model_info, f, indent=2, ensure_ascii=False)
                
            self._model_info = model_info
            
        except Exception as e:
            logger.warning(f"保存模型信息失败: {e}")
    
    def _load_model_info(self) -> bool:
        """加载模型信息"""
        try:
            info_file = self.cache_dir / "model_info.json"
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    self._model_info = json.load(f)
                return True
        except Exception as e:
            logger.warning(f"加载模型信息失败: {e}")
        return False
    
    def is_model_available(self) -> bool:
        """检查模型是否可用"""
        if not HAS_TRANSFORMERS:
            return False
            
        self._load_model_info()
        if not self._model_info:
            return False
        
        model_path = self._model_info.get("model_path")
        if not model_path or not Path(model_path).exists():
            return False
            
        return True
    
    async def load_model(self, progress_callback: Optional[callable] = None) -> bool:
        """
        加载模型
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            bool: 加载是否成功
        """
        if not HAS_TRANSFORMERS:
            logger.error("transformers库未安装，无法加载模型")
            return False
        
        if self._load_status == "loaded":
            return True
        
        if self._load_status == "loading":
            logger.warning("模型正在加载中")
            return False
        
        try:
            self._load_status = "loading"
            logger.info(f"开始加载模型: {self.config.model_name}")
            
            if progress_callback:
                progress_callback({"status": "loading", "progress": 0, "message": "准备加载模型"})
            
            # 检查模型是否存在
            if not self.is_model_available():
                if self.config.auto_download:
                    logger.info("模型不存在，开始自动下载")
                    if not await self.download_model(progress_callback):
                        self._load_status = "error"
                        return False
                else:
                    logger.error("模型不存在且禁用自动下载")
                    self._load_status = "error"
                    return False
            
            # 获取模型路径
            model_path = self._model_info.get("model_path") or self.config.model_name
            self.device = self._get_device()
            
            if progress_callback:
                progress_callback({"status": "loading", "progress": 25, "message": "加载tokenizer"})
            
            # 加载tokenizer
            loop = asyncio.get_event_loop()
            self.tokenizer = await loop.run_in_executor(
                None, 
                lambda: AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=True,
                    cache_dir=str(self.cache_dir)
                )
            )
            
            if progress_callback:
                progress_callback({"status": "loading", "progress": 60, "message": "加载模型"})
            
            # 加载模型
            self.model = await loop.run_in_executor(
                None,
                lambda: AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map="auto" if self.device == "cuda" else None,
                    trust_remote_code=True,
                    cache_dir=str(self.cache_dir)
                )
            )
            
            # 移动模型到指定设备
            if self.device != "cuda":  # cuda模式下device_map已处理
                self.model = self.model.to(self.device)
            
            if progress_callback:
                progress_callback({"status": "loading", "progress": 80, "message": "配置生成参数"})
            
            # 设置生成配置
            self.generation_config = GenerationConfig(
                max_new_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
            
            self._load_status = "loaded"
            
            if progress_callback:
                progress_callback({"status": "loaded", "progress": 100, "message": "模型加载完成"})
            
            logger.info(f"模型加载完成，设备: {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            self._load_status = "error"
            if progress_callback:
                progress_callback({"status": "error", "progress": 0, "message": f"加载失败: {e}"})
            return False
    
    def unload_model(self) -> None:
        """卸载模型"""
        try:
            if self.model is not None:
                del self.model
                self.model = None
            
            if self.tokenizer is not None:
                del self.tokenizer
                self.tokenizer = None
            
            self.generation_config = None
            
            # 清理GPU内存
            if HAS_TRANSFORMERS and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self._load_status = "unloaded"
            logger.info("模型已卸载")
            
        except Exception as e:
            logger.error(f"卸载模型失败: {e}")
    
    async def generate_text(self, prompt: str, stream: bool = False) -> AsyncGenerator[str, None]:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            stream: 是否流式输出
            
        Yields:
            str: 生成的文本
        """
        if self._load_status != "loaded":
            raise RuntimeError("模型未加载")
        
        try:
            # 编码输入
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
            
            if stream:
                # 流式生成
                async for token in self._generate_stream(inputs, prompt):
                    yield token
            else:
                # 一次性生成
                loop = asyncio.get_event_loop()
                
                def generate():
                    with torch.no_grad():
                        outputs = self.model.generate(
                            inputs,
                            generation_config=self.generation_config,
                            do_sample=True,
                            return_dict_in_generate=True,
                            output_scores=True
                        )
                    
                    # 解码输出
                    generated_text = self.tokenizer.decode(
                        outputs.sequences[0][len(inputs[0]):],
                        skip_special_tokens=True
                    )
                    
                    return generated_text
                
                result = await loop.run_in_executor(None, generate)
                yield result
                
        except Exception as e:
            logger.error(f"文本生成失败: {e}")
            yield f"生成失败: {e}"
    
    async def _generate_stream(self, inputs: torch.Tensor, original_prompt: str) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        try:
            generated_tokens = []
            
            with torch.no_grad():
                past_key_values = None
                
                for _ in range(self.config.max_tokens):
                    # 生成下一个token
                    if past_key_values is None:
                        outputs = self.model(inputs)
                    else:
                        outputs = self.model(inputs[:, -1:], past_key_values=past_key_values)
                    
                    past_key_values = outputs.past_key_values
                    
                    # 应用生成配置
                    logits = outputs.logits[0, -1, :] / self.config.temperature
                    
                    # Top-p采样
                    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                    cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
                    
                    # 找到cutoff位置
                    cutoff_index = torch.searchsorted(cumulative_probs, self.config.top_p)
                    cutoff_index = max(1, cutoff_index.item())
                    
                    # 保留top-p的tokens
                    top_p_logits = sorted_logits[:cutoff_index]
                    top_p_indices = sorted_indices[:cutoff_index]
                    
                    # 采样
                    probs = torch.softmax(top_p_logits, dim=-1)
                    next_token_idx = torch.multinomial(probs, 1)
                    next_token = top_p_indices[next_token_idx]
                    
                    # 检查是否为结束token
                    if next_token.item() == self.tokenizer.eos_token_id:
                        break
                    
                    generated_tokens.append(next_token.item())
                    
                    # 解码并输出新token
                    new_text = self.tokenizer.decode([next_token.item()], skip_special_tokens=True)
                    yield new_text
                    
                    # 准备下一次迭代的输入
                    inputs = torch.cat([inputs, next_token.unsqueeze(0)], dim=1)
                    
                    # 添加小延迟以实现流式效果
                    await asyncio.sleep(0.01)
                    
        except Exception as e:
            logger.error(f"流式生成失败: {e}")
            yield f"\n[生成错误: {e}]"
    
    def get_model_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        return {
            "model_name": self.config.model_name,
            "load_status": self._load_status,
            "device": self.device,
            "is_available": self.is_model_available(),
            "model_info": self._model_info,
            "config": self.config.dict()
        }