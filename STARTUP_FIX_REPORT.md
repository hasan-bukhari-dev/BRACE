# BRACE startup repair

Port8765 is already occupied. The former launcher opened the browser on a timer even when binding failed, exposing the unrelated service's Not Found response.

Changed launch.py only in application behavior: reserve a loopback socket before starting; if the default port is occupied, choose an available port from8766–8785 and print its address; pass the same reserved socket to Uvicorn, avoiding a check/bind race. Set BRACE_PORT before application import so write-origin checks match that address. Open the browser only after Uvicorn reports startup complete. An explicitly configured occupied port fails clearly without opening a browser. No existing process is stopped.

Verification:12 targeted launcher/security tests passed, one existing dependency deprecation warning,12.48seconds. Real process:8765 occupied by existing service;8766 selected; actual BRACE homepage/health passed; correct-port POST reached validation422; wrong-port origin rejected403. See STARTUP_LIVE_VERIFICATION.json. Tests used the established isolated standardPython3.11.9 environment; the user's3.13 installation was not modified. No fresh full-suite run is claimed: the preceding Design3 checkpoint passed262 tests; this bounded repair adds3 launcher cases. Scientific engines, historical evidence and existing examples are unchanged.

Use the fixed checkpoint normally. Existing installations can replace only launch.py with this version, retaining their installed .venv. For the previous launcher, an immediate workaround in Command Prompt, from its folder, is:

set "BRACE_PORT=8766"
START_BRACE_WINDOWS.bat

Use another unused port if8766 is occupied. The fixed launcher does this automatically when no explicit port is configured. Earlier Design3 acceptance reports remain historical; human/screen-reader/event acceptance remains conditional.
