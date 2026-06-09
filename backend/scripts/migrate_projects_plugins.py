#!/usr/bin/env python3
"""
Migration script to convert projects from storing PluginConfiguration objects
to storing plugin IDs (to match provisioners and triggers).

This script:
1. Scans all project JSON files in data/shared/projects and data/users/*/projects
2. For each project with old-style global_plugins (list of objects)
3. Converts each PluginConfiguration to a plugin in the master plugin library
4. Updates the project to reference the plugin by ID
5. Creates a backup before making changes

Usage:
    python backend/scripts/migrate_projects_plugins.py [--dry-run]
"""

import json
import sys
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class ProjectMigrator:
    """Migrates projects from PluginConfiguration to plugin IDs."""
    
    def __init__(self, base_dir: str = "backend/data", dry_run: bool = False):
        """
        Initialize migrator.
        
        Args:
            base_dir: Base data directory
            dry_run: If True, only print what would be done
        """
        self.base_dir = Path(base_dir)
        self.dry_run = dry_run
        self.stats = {
            "projects_scanned": 0,
            "projects_migrated": 0,
            "plugins_created": 0,
            "errors": []
        }
    
    def find_all_project_files(self) -> List[Path]:
        """Find all project JSON files."""
        project_files = []
        
        # Shared projects
        shared_projects = self.base_dir / "shared" / "projects"
        if shared_projects.exists():
            project_files.extend(shared_projects.glob("*.json"))
        
        # User projects
        users_dir = self.base_dir / "users"
        if users_dir.exists():
            for user_dir in users_dir.iterdir():
                if user_dir.is_dir():
                    user_projects = user_dir / "projects"
                    if user_projects.exists():
                        project_files.extend(user_projects.glob("*.json"))
        
        return project_files
    
    def needs_migration(self, project_data: Dict[str, Any]) -> bool:
        """
        Check if project needs migration.
        
        Args:
            project_data: Project JSON data
            
        Returns:
            True if global_plugins contains objects instead of IDs
        """
        global_plugins = project_data.get("global_plugins", [])
        
        if not global_plugins:
            return False
        
        # Check if first item is an object (old format) or string (new format)
        first_plugin = global_plugins[0]
        return isinstance(first_plugin, dict)
    
    def get_or_create_plugin(
        self,
        plugin_config: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """
        Get or create a plugin in the master library from PluginConfiguration.
        
        Args:
            plugin_config: PluginConfiguration dict
            user_id: User ID (None for shared)
            
        Returns:
            Plugin ID
        """
        # Determine plugin storage location
        if user_id:
            plugins_dir = self.base_dir / "users" / user_id / "plugins"
        else:
            plugins_dir = self.base_dir / "shared" / "plugins"
        
        plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to find existing plugin by name
        plugin_name = plugin_config.get("name")
        for plugin_file in plugins_dir.glob("*.json"):
            try:
                with open(plugin_file, 'r') as f:
                    existing_plugin = json.load(f)
                    if existing_plugin.get("name") == plugin_name:
                        print(f"  Found existing plugin: {plugin_name} ({existing_plugin['id']})")
                        return existing_plugin["id"]
            except Exception as e:
                print(f"  Warning: Error reading {plugin_file}: {e}")
        
        # Create new plugin from PluginConfiguration
        plugin_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        plugin = {
            "id": plugin_id,
            "name": plugin_name,
            "description": f"Migrated from project plugin configuration",
            "source_url": None,
            "documentation_url": None,
            "default_version": plugin_config.get("version"),
            "configuration": json.dumps(plugin_config.get("config", {})) if plugin_config.get("config") else None,
            "is_deprecated": plugin_config.get("is_deprecated", False),
            "created_at": now,
            "updated_at": now,
            "is_shared": user_id is None,
            "owner_id": user_id,
            "source_id": None
        }
        
        # Save plugin
        plugin_file = plugins_dir / f"{plugin_id}.json"
        
        if not self.dry_run:
            with open(plugin_file, 'w') as f:
                json.dump(plugin, f, indent=2)
            print(f"  Created new plugin: {plugin_name} ({plugin_id})")
        else:
            print(f"  [DRY RUN] Would create plugin: {plugin_name} ({plugin_id})")
        
        self.stats["plugins_created"] += 1
        return plugin_id
    
    def migrate_project(self, project_file: Path) -> bool:
        """
        Migrate a single project file.
        
        Args:
            project_file: Path to project JSON file
            
        Returns:
            True if migration successful
        """
        try:
            # Load project
            with open(project_file, 'r') as f:
                project_data = json.load(f)
            
            # Check if needs migration
            if not self.needs_migration(project_data):
                return False
            
            print(f"\nMigrating: {project_file}")
            
            # Determine user_id from path
            user_id = None
            parts = project_file.parts
            if "users" in parts:
                user_idx = parts.index("users")
                if user_idx + 1 < len(parts):
                    user_id = parts[user_idx + 1]
            
            # Backup original
            if not self.dry_run:
                backup_file = project_file.with_suffix(".json.backup")
                shutil.copy2(project_file, backup_file)
                print(f"  Created backup: {backup_file}")
            
            # Convert plugins
            old_plugins = project_data["global_plugins"]
            new_plugin_ids = []
            
            for plugin_config in old_plugins:
                plugin_id = self.get_or_create_plugin(plugin_config, user_id)
                new_plugin_ids.append(plugin_id)
            
            # Update project
            project_data["global_plugins"] = new_plugin_ids
            project_data["updated_at"] = datetime.now().isoformat()
            
            # Save migrated project
            if not self.dry_run:
                with open(project_file, 'w') as f:
                    json.dump(project_data, f, indent=2)
                print(f"  ✓ Migrated {len(old_plugins)} plugin(s)")
            else:
                print(f"  [DRY RUN] Would migrate {len(old_plugins)} plugin(s)")
            
            return True
            
        except Exception as e:
            error_msg = f"Error migrating {project_file}: {str(e)}"
            print(f"  ✗ {error_msg}")
            self.stats["errors"].append(error_msg)
            return False
    
    def run(self):
        """Run the migration."""
        print("=" * 60)
        print("Project Plugin Migration")
        print("=" * 60)
        
        if self.dry_run:
            print("\n*** DRY RUN MODE - No changes will be made ***\n")
        
        # Find all projects
        project_files = self.find_all_project_files()
        print(f"\nFound {len(project_files)} project file(s)")
        
        # Migrate each project
        for project_file in project_files:
            self.stats["projects_scanned"] += 1
            if self.migrate_project(project_file):
                self.stats["projects_migrated"] += 1
        
        # Print summary
        print("\n" + "=" * 60)
        print("Migration Summary")
        print("=" * 60)
        print(f"Projects scanned:  {self.stats['projects_scanned']}")
        print(f"Projects migrated: {self.stats['projects_migrated']}")
        print(f"Plugins created:   {self.stats['plugins_created']}")
        print(f"Errors:            {len(self.stats['errors'])}")
        
        if self.stats["errors"]:
            print("\nErrors:")
            for error in self.stats["errors"]:
                print(f"  - {error}")
        
        print("\n" + "=" * 60)
        
        if self.dry_run:
            print("\nTo apply changes, run without --dry-run flag")
        else:
            print("\nMigration complete!")
            print("Backup files created with .backup extension")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate projects to use plugin IDs")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--base-dir",
        default="backend/data",
        help="Base data directory (default: backend/data)"
    )
    
    args = parser.parse_args()
    
    migrator = ProjectMigrator(base_dir=args.base_dir, dry_run=args.dry_run)
    migrator.run()


if __name__ == "__main__":
    main()
