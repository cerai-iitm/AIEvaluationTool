@echo off
set "profile_dir="%cd%\whatsapp_profile""

:: Check if the folder exists
if not exist "%profile_dir%" (
    echo Profile directory does not exist. Creating it...
    mkdir "%profile_dir%"
)

:: Start Chrome with the specified user data directory and force new window
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="%profile_dir%" --new-window --start-maximized https://web.whatsapp.com
