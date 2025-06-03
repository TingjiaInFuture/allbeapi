@echo off
REM Windows 生产环境启动脚本


REM 使用Gunicorn启动应用
echo Starting BeautifulSoup API with Gunicorn...
gunicorn -c gunicorn.conf.py app:app

REM 或者直接指定参数启动：
REM gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 30 --log-level info app:app
