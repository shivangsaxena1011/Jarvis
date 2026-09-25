# SHIVANI 1.0 Troubleshooting Guide

## 1. Quick Diagnostics with Doctor
If encountering any anomalies, run the built-in doctor command first:

```powershell
shivani doctor
# For extended diagnostic traces:
shivani doctor --full
```

---

## 2. Common Issues & Solutions

### Issue: Windows 11 App Control Blocks Python (`os error 4551`)
- **Symptom**: `Failed to query Python interpreter ... An Application Control policy has blocked this file.`
- **Cause**: Windows 11 WDAC/SmartAppControl blocks execution of Python venv trampoline shims.
- **Solution**: Execute directly through the base Python binary with `PYTHONPATH` set:
  ```powershell
  $env:PYTHONPATH = "C:\Users\Project\Jarvis\.venv\Lib\site-packages;C:\Users\Project\Jarvis"
  & "C:\Users\shiva\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe" cli/main.py status
  ```

### Issue: Port 8000 Already in Use
- **Symptom**: `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`
- **Solution**:
  1. Specify an alternative port: `shivani start --port 8080`
  2. Or stop running instances: `shivani stop`

### Issue: Emergency Kill-Switch is Active
- **Symptom**: `Emergency stop is ACTIVE (STOPPED): No action permitted`
- **Cause**: An emergency stop was triggered by user, watchdog, or red-team alarm.
- **Solution**: Resume the system via CLI or Python:
  ```python
  from core.orchestrator.emergency import EmergencyController
  EmergencyController().resume()
  ```

### Issue: Stalled or Runaway Task
- **Symptom**: Task is stuck in `PLANNING` or `EXECUTING` loop.
- **Solution**: The `TaskWatchdog` will automatically transition tasks to `BLOCKED` after 3 identical steps or 90 seconds without progress. You can inspect stalled tasks with:
  ```powershell
  shivani logs --lines 50
  ```
