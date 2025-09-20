import os
import shutil
from pathlib import Path

def cleanup_project():
    """Clean up project files and folders to free space."""

    # 1. Clean log files
    logs_dir = Path("logs")
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            try:
                log_file.unlink()
                print(f"✅ Deleted {log_file}")
            except Exception as e:
                print(f"❌ Error deleting {log_file}: {e}")

    # 2. Clean gemini histories (delete files >1MB)
    gemini_dir = Path("gemini_histories")
    if gemini_dir.exists():
        for history_file in gemini_dir.glob("*.json"):
            try:
                if history_file.stat().st_size > 1024 * 1024:  # 1MB
                    history_file.unlink()
                    print(f"✅ Deleted large history {history_file}")
            except Exception as e:
                print(f"❌ Error processing {history_file}: {e}")

    # 3. Clean gpt_history folder (delete everything inside)
    gpt_history_dir = Path("gpt_history")
    if gpt_history_dir.exists():
        for file in gpt_history_dir.glob("*"):
            try:
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file)
                print(f"✅ Deleted {file}")
            except Exception as e:
                print(f"❌ Error deleting {file}: {e}")

    # 4. Clean cache and imagine_cache folders
    for cache_name in ["cache", "imagine_cache"]:
        cache_dir = Path(cache_name)
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(exist_ok=True)
                print(f"✅ Cleaned {cache_name}/")
            except Exception as e:
                print(f"❌ Error cleaning {cache_name}/: {e}")

    print("\n🧹 Cleanup completed!")

if __name__ == "__main__":
    cleanup_project()
