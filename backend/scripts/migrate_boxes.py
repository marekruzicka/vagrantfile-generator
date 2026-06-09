#!/usr/bin/env python3
"""
Migration script to convert boxes.json to individual box files.

This script:
1. Reads the existing boxes.json file
2. Creates individual JSON files for each box
3. Backs up the original boxes.json file
"""

import json
import sys
from pathlib import Path


def migrate_boxes(boxes_file_path: Path):
    """Migrate boxes.json to individual files."""
    
    if not boxes_file_path.exists():
        print(f"❌ No boxes.json found at {boxes_file_path}, skipping migration")
        return False
    
    print(f"📦 Starting boxes migration from {boxes_file_path}")
    
    try:
        with open(boxes_file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error reading boxes.json: {e}")
        return False
    
    # Handle both {"boxes": [...]} and [...] formats
    if isinstance(data, dict):
        boxes = data.get("boxes", [])
    elif isinstance(data, list):
        boxes = data
    else:
        print(f"❌ Unexpected data format in boxes.json")
        return False
    
    if not boxes:
        print("⚠️  No boxes found in boxes.json")
        return False
    
    print(f"📋 Found {len(boxes)} boxes to migrate")
    
    # Create individual files for each box
    migrated_count = 0
    for box in boxes:
        box_id = box.get('id')
        box_name = box.get('name', 'unknown')
        
        if not box_id:
            print(f"⚠️  Skipping box without ID: {box_name}")
            continue
        
        output_file = boxes_file_path.parent / f"{box_id}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(box, f, indent=2)
            print(f"✅ Migrated: {box_name} -> {box_id}.json")
            migrated_count += 1
        except Exception as e:
            print(f"❌ Error migrating box {box_name}: {e}")
    
    # Backup original file
    backup_file = boxes_file_path.parent / "boxes.json.backup"
    try:
        boxes_file_path.rename(backup_file)
        print(f"💾 Backed up original to {backup_file.name}")
    except Exception as e:
        print(f"⚠️  Could not backup original file: {e}")
    
    print(f"\n✨ Migration complete! Migrated {migrated_count}/{len(boxes)} boxes")
    return True


def main():
    """Main entry point for the migration script."""
    
    # Default path to boxes.json in shared directory
    default_path = Path(__file__).parent.parent / "data" / "shared" / "boxes" / "boxes.json"
    
    # Allow custom path as command line argument
    if len(sys.argv) > 1:
        boxes_file_path = Path(sys.argv[1])
    else:
        boxes_file_path = default_path
    
    print("=" * 60)
    print("  Boxes Migration Script")
    print("  Converting boxes.json to individual box files")
    print("=" * 60)
    print()
    
    success = migrate_boxes(boxes_file_path)
    
    if success:
        print("\n🎉 Migration successful!")
        sys.exit(0)
    else:
        print("\n⚠️  Migration completed with issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
