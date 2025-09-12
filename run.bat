
@echo off
REM set env vars
set VOICETRANSOR_LOG_LEVEL=DEBUG
echo In BAT: %VOICETRANSOR_LOG_LEVEL%

python -m app.main

@REM pause