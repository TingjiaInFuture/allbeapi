# Gunicorn配置文件
import multiprocessing

# 服务器套接字
bind = "0.0.0.0:5000"
backlog = 2048

# 工作进程
workers = multiprocessing.cpu_count() * 2 + 1  # 推荐的工作进程数
worker_class = "sync"  # 工作进程类型
worker_connections = 1000
timeout = 30
keepalive = 2

# 重启
max_requests = 1000  # 处理指定数量的请求后重启工作进程
max_requests_jitter = 50  # 随机化重启时间

# 日志
accesslog = "-"  # 访问日志输出到stdout
errorlog = "-"   # 错误日志输出到stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 进程命名
proc_name = 'beautifulsoup_api'

# 安全
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL（如果需要）
# keyfile = None
# certfile = None

# 预加载应用
preload_app = True

# 用户和组（在Linux上运行时）
# user = "www-data"
# group = "www-data"
