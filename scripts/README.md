# OpenEdu Git Scripts

Utility scripts for OpenEdu Git setup, maintenance, and automation.

## Scripts

### `setup_minio_buckets.py`
Creates required MinIO buckets for the project:
- `pamphlets`: Stores uploaded pamphlet files (PDF, Word, Markdown).
- `avatars`: Stores user profile pictures.
- `video-courses`: Reserved for future video course uploads (Phase 2).

**Usage:**
```bash
python3 scripts/setup_minio_buckets.py
```

### Future Scripts
- `backup_db.sh`: Backup PostgreSQL database.
- `restore_db.sh`: Restore PostgreSQL database from backup.
- `seed_data.py`: Seed database with sample data for testing.
- `cleanup_files.py`: Clean up orphaned files in MinIO.