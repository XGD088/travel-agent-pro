import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging():
    """配置详细的日志系统"""
    
    # 创建logs目录
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # 生成日志文件名（按日期）
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"travel_agent_{today}.log")
    error_log_file = os.path.join(logs_dir, f"travel_agent_errors_{today}.log")
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(filename)-15s:%(lineno)-4d | %(funcName)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 1. 控制台处理器（INFO级别）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # 2. 文件处理器（DEBUG级别，所有日志）
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # 3. 错误文件处理器（ERROR级别）
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # 设置特定模块的日志级别
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    logging.getLogger('httpx').setLevel(logging.INFO)
    
    # 记录日志系统启动
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("🚀 日志系统启动")
    logger.info(f"📁 日志目录: {os.path.abspath(logs_dir)}")
    logger.info(f"📄 详细日志: {log_file}")
    logger.info(f"❌ 错误日志: {error_log_file}")
    logger.info("=" * 80)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return logging.getLogger(name) 