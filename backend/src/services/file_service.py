"""
FileService for Vagrantfile GUI Generator.

This service handles file I/O operations for project persistence.
"""

import os
import json
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import uuid

from ..models.project import Project
from ..models.virtual_machine import VirtualMachine
from ..models.network_interface import NetworkInterface


class FileServiceError(Exception):
    """Custom exception for file service errors."""
    pass


class FileService:
    """Service for handling project file operations."""
    
    def __init__(self, base_directory: str = "data"):
        """
        Initialize the file service.
        
        Args:
            base_directory: Base directory for storing project files
        """
        self.base_directory = Path(base_directory)
        self.projects_directory = self.base_directory / "projects"
        self.exports_directory = self.base_directory / "exports"
        self.templates_directory = self.base_directory / "templates"
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.base_directory,
            self.projects_directory,
            self.exports_directory,
            self.templates_directory
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_project(self, project: Project, create_backup: bool = True) -> str:
        """
        Save a project to disk.
        
        Args:
            project: The project to save
            create_backup: Whether to create a backup of existing file
            
        Returns:
            Path to the saved file
        """
        try:
            project_dir = self.projects_directory / str(project.id)
            project_dir.mkdir(parents=True, exist_ok=True)
            
            project_file = project_dir / "project.json"
            
            # Create backup if file exists and backup is requested
            if create_backup and project_file.exists():
                self._create_backup(project_file)
            
            # Convert project to dict and save
            project_data = project.model_dump()
            project_data["last_saved"] = datetime.now().isoformat()
            
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            return str(project_file)
            
        except Exception as e:
            raise FileServiceError(f"Failed to save project {project.id}: {str(e)}")
    
    def load_project(self, project_id: str) -> Project:
        """
        Load a project from disk.
        
        Args:
            project_id: The ID of the project to load
            
        Returns:
            The loaded project
        """
        try:
            project_file = self.projects_directory / project_id / "project.json"
            
            if not project_file.exists():
                raise FileServiceError(f"Project file not found: {project_file}")
            
            with open(project_file, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Remove metadata fields that aren't part of the model
            project_data.pop("last_saved", None)
            
            return Project(**project_data)
            
        except json.JSONDecodeError as e:
            raise FileServiceError(f"Invalid project file format: {str(e)}")
        except Exception as e:
            raise FileServiceError(f"Failed to load project {project_id}: {str(e)}")
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project from disk.
        
        Args:
            project_id: The ID of the project to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            project_dir = self.projects_directory / project_id
            
            if project_dir.exists():
                shutil.rmtree(project_dir)
                return True
            
            return False
            
        except Exception as e:
            raise FileServiceError(f"Failed to delete project {project_id}: {str(e)}")
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects with basic metadata.
        
        Returns:
            List of project metadata dictionaries
        """
        projects = []
        
        try:
            for project_dir in self.projects_directory.iterdir():
                if project_dir.is_dir():
                    project_file = project_dir / "project.json"
                    
                    if project_file.exists():
                        try:
                            with open(project_file, 'r', encoding='utf-8') as f:
                                project_data = json.load(f)
                            
                            # Extract metadata
                            metadata = {
                                "id": project_data.get("id"),
                                "name": project_data.get("name"),
                                "description": project_data.get("description", ""),
                                "created_at": project_data.get("created_at"),
                                "updated_at": project_data.get("updated_at"),
                                "last_saved": project_data.get("last_saved"),
                                "vm_count": len(project_data.get("vms", [])),
                                "file_size": project_file.stat().st_size
                            }
                            
                            projects.append(metadata)
                            
                        except (json.JSONDecodeError, KeyError) as e:
                            # Skip corrupted project files
                            continue
            
            # Sort by updated_at or created_at
            projects.sort(key=lambda p: p.get("updated_at") or p.get("created_at"), reverse=True)
            
            return projects
            
        except Exception as e:
            raise FileServiceError(f"Failed to list projects: {str(e)}")
    
    def export_project(self, project: Project, format: str = "json") -> str:
        """
        Export a project to a specific format.
        
        Args:
            project: The project to export
            format: Export format ("json", "yaml", "vagrantfile")
            
        Returns:
            Path to the exported file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = self.exports_directory / f"{project.name}_{timestamp}"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            if format == "json":
                return self._export_json(project, export_dir)
            elif format == "yaml":
                return self._export_yaml(project, export_dir)
            elif format == "vagrantfile":
                return self._export_vagrantfile(project, export_dir)
            else:
                raise FileServiceError(f"Unsupported export format: {format}")
                
        except Exception as e:
            raise FileServiceError(f"Failed to export project: {str(e)}")
    
    def _export_json(self, project: Project, export_dir: Path) -> str:
        """Export project as JSON."""
        export_file = export_dir / f"{project.name}.json"
        
        project_data = project.model_dump()
        project_data["exported_at"] = datetime.now().isoformat()
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        return str(export_file)
    
    def _export_yaml(self, project: Project, export_dir: Path) -> str:
        """Export project as YAML."""
        try:
            import yaml  # type: ignore
        except ImportError:
            raise FileServiceError("YAML export requires PyYAML package")
        
        export_file = export_dir / f"{project.name}.yaml"
        
        project_data = project.model_dump()
        project_data["exported_at"] = datetime.now().isoformat()
        
        with open(export_file, 'w', encoding='utf-8') as f:
            yaml.dump(project_data, f, default_flow_style=False, allow_unicode=True)
        
        return str(export_file)
    
    def _export_vagrantfile(self, project: Project, export_dir: Path) -> str:
        """Export project as Vagrantfile."""
        from ..services.vagrantfile_generator import VagrantfileGenerator
        
        generator = VagrantfileGenerator()
        result = generator.generate(project)
        
        # Extract content from the result dictionary
        vagrantfile_content = result.get("content", "")
        
        export_file = export_dir / "Vagrantfile"
        
        with open(export_file, 'w', encoding='utf-8') as f:
            f.write(vagrantfile_content)
        
        return str(export_file)
    
    def import_project(self, file_path: str) -> Project:
        """
        Import a project from a file.
        
        Args:
            file_path: Path to the file to import
            
        Returns:
            The imported project
        """
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                raise FileServiceError(f"Import file not found: {file_path_obj}")
            
            if file_path_obj.suffix.lower() == '.json':
                return self._import_json(file_path_obj)
            elif file_path_obj.suffix.lower() in ['.yaml', '.yml']:
                return self._import_yaml(file_path_obj)
            else:
                raise FileServiceError(f"Unsupported import format: {file_path_obj.suffix}")
                
        except Exception as e:
            raise FileServiceError(f"Failed to import project: {str(e)}")
    
    def _import_json(self, file_path: Path) -> Project:
        """Import project from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # Remove export metadata
        project_data.pop("exported_at", None)
        project_data.pop("last_saved", None)
        
        # Generate new ID if needed
        if "id" not in project_data:
            project_data["id"] = str(uuid.uuid4())
        
        return Project(**project_data)
    
    def _import_yaml(self, file_path: Path) -> Project:
        """Import project from YAML file."""
        try:
            import yaml  # type: ignore
        except ImportError:
            raise FileServiceError("YAML import requires PyYAML package")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            project_data = yaml.safe_load(f)
        
        # Remove export metadata
        project_data.pop("exported_at", None)
        project_data.pop("last_saved", None)
        
        # Generate new ID if needed
        if "id" not in project_data:
            project_data["id"] = str(uuid.uuid4())
        
        return Project(**project_data)
    
    def _create_backup(self, file_path: Path):
        """Create a backup of an existing file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".backup_{timestamp}.json")
        shutil.copy2(file_path, backup_path)
    
    def cleanup_backups(self, keep_count: int = 5):
        """
        Clean up old backup files, keeping only the most recent ones.
        
        Args:
            keep_count: Number of backups to keep per project
        """
        try:
            for project_dir in self.projects_directory.iterdir():
                if project_dir.is_dir():
                    # Find all backup files
                    backup_files = list(project_dir.glob("*.backup_*.json"))
                    
                    if len(backup_files) > keep_count:
                        # Sort by modification time (oldest first)
                        backup_files.sort(key=lambda f: f.stat().st_mtime)
                        
                        # Remove oldest backups
                        for backup_file in backup_files[:-keep_count]:
                            backup_file.unlink()
                            
        except Exception as e:
            raise FileServiceError(f"Failed to cleanup backups: {str(e)}")
    
    def get_project_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored projects.
        
        Returns:
            Dictionary with statistics
        """
        try:
            stats = {
                "total_projects": 0,
                "total_vms": 0,
                "total_size_bytes": 0,
                "oldest_project": None,
                "newest_project": None
            }
            
            projects = self.list_projects()
            
            if projects:
                stats["total_projects"] = len(projects)
                stats["total_vms"] = sum(p["vm_count"] for p in projects)
                stats["total_size_bytes"] = sum(p["file_size"] for p in projects)
                
                # Find oldest and newest
                sorted_by_created = sorted(projects, key=lambda p: p.get("created_at", ""))
                stats["oldest_project"] = sorted_by_created[0]["name"] if sorted_by_created else None
                stats["newest_project"] = sorted_by_created[-1]["name"] if sorted_by_created else None
            
            return stats
            
        except Exception as e:
            raise FileServiceError(f"Failed to get project stats: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the file service.
        
        Returns:
            Dictionary with health status
        """
        health = {
            "status": "healthy",
            "issues": [],
            "directories_exist": True,
            "writable": True
        }
        
        try:
            # Check directories exist
            for directory in [self.base_directory, self.projects_directory, self.exports_directory]:
                if not directory.exists():
                    health["issues"].append(f"Directory missing: {directory}")
                    health["directories_exist"] = False
            
            # Check write permissions
            test_file = self.base_directory / "health_check_test.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception:
                health["issues"].append("Cannot write to base directory")
                health["writable"] = False
            
            # Set overall status
            if health["issues"]:
                health["status"] = "unhealthy"
            
            return health
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "directories_exist": False,
                "writable": False
            }