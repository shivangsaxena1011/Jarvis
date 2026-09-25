# SHIVANI 1.0 Backup & Disaster Recovery Guide

## 1. Creating System Backups
SHIVANI provides cryptographic, portable backup archives containing your memories, knowledge graphs, tasks, and configurations.

```powershell
# Create standard backup
shivani data backup

# Create named backup including debug logs
shivani data backup --name pre_upgrade_backup --logs
```

Backups are saved to `%APPDATA%\Shivani\backups` with an accompanying `.manifest.json` containing SHA-256 integrity checksums.

---

## 2. Listing & Verifying Backups
```powershell
# List existing backups with timestamps and sizes
shivani data list

# Verify checksum and archive integrity
shivani data verify --path "%APPDATA%\Shivani\backups\pre_upgrade_backup.zip"
```

---

## 3. Restoring from a Backup
The restoration pipeline validates the archive structure and protects against zip-slip directory traversal vulnerabilities before extracting files:

```powershell
# Restore into active application directory
shivani data restore --path "%APPDATA%\Shivani\backups\pre_upgrade_backup.zip" --overwrite

# Restore to an isolated recovery directory for inspection
shivani data restore --path "%APPDATA%\Shivani\backups\pre_upgrade_backup.zip" --target "C:\Recovery\Shivani"
```

---

## 4. Exporting Data for Portability
To export your personal assistant data (goals, knowledge entities, memory facts) into standard JSON or ZIP without system binary dependencies:

```powershell
shivani data export --output "C:\Users\Project\my_shivani_export.json" --format json
```
