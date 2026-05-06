@echo off
echo 正在清理所有 FastAPI/Python 幽灵进程...
taskkill /F /IM python.exe /T
echo 清理完成！
pause