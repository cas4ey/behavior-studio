set SCRIPT_DIR=%~dp0
start python %SCRIPT_DIR%/source/main.py -c %SCRIPT_DIR%/config/config.xml %*
