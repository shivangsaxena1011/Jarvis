# SHIVANI 1.0 Update & Rollback Procedures

## 1. Upgrade Protocol
Before applying updates or checking out a new release tag:

1. **Create Pre-Upgrade Safety Backup**:
   ```powershell
   shivani data backup --name pre_update_1_0
   ```
2. **Stop Active Background Services**:
   ```powershell
   shivani stop
   ```
3. **Pull Latest Changes & Update Dependencies**:
   ```powershell
   git fetch origin
   git checkout tags/v1.0.0
   uv pip install -e .
   ```
4. **Validate Integrity**:
   ```powershell
   shivani doctor
   uv run pytest tests/
   ```

---

## 2. Emergency Rollback Protocol
If an update causes regression or unexpected instability:

1. **Trigger Emergency Stop**:
   ```powershell
   shivani stop
   ```
2. **Revert Codebase**:
   ```powershell
   git checkout <previous-commit-or-tag>
   uv pip install -e .
   ```
3. **Restore Data State from Pre-Upgrade Backup**:
   ```powershell
   shivani data restore --path "%APPDATA%\Shivani\backups\pre_update_1_0.zip" --overwrite
   ```
4. **Verify Health**:
   ```powershell
   shivani doctor
   shivani status
   ```
