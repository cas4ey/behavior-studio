set BEHAVIOR_STUDIO_ROOT=%~dp0
start python %BEHAVIOR_STUDIO_ROOT%/source/main.py -c %BEHAVIOR_STUDIO_ROOT%/config/config.xml %*
