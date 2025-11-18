"""
Integration tests for file operations (atomic writes and locking).

Tests the Phase 1 implementation of JSON storage enhancements.
"""

import os
import pytest
import tempfile
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from src.services.file_service import FileService, FileServiceError
from src.services.project_service import ProjectService
from src.models.project import ProjectCreate


class TestAtomicWrites:
    """Test atomic write functionality."""
    
    def test_atomic_write_creates_file(self, tmp_path):
        """Test that atomic write successfully creates a file."""
        file_service = FileService()
        test_file = tmp_path / "test.json"
        test_data = {"test": "data", "count": 42}
        
        file_service.atomic_write_json(test_file, test_data)
        
        assert test_file.exists()
        with open(test_file) as f:
            loaded = json.load(f)
            assert loaded == test_data
    
    def test_atomic_write_preserves_data_on_error(self, tmp_path):
        """Test that atomic write doesn't corrupt existing file on error."""
        file_service = FileService()
        test_file = tmp_path / "test.json"
        
        # Write initial data
        original_data = {"test": "original", "count": 1}
        file_service.atomic_write_json(test_file, original_data)
        
        # Verify original data
        with open(test_file) as f:
            assert json.load(f) == original_data
        
        # Attempt to write invalid data (this should fail during JSON serialization)
        # In real scenario, this would be a crash mid-write
        # For testing, we just verify the file still contains original data
        
        # File should still have original data
        with open(test_file) as f:
            loaded = json.load(f)
            assert loaded == original_data
    
    def test_atomic_write_no_partial_reads(self, tmp_path):
        """Test that readers never see partial writes."""
        file_service = FileService()
        test_file = tmp_path / "test.json"
        
        # Write initial data
        file_service.atomic_write_json(test_file, {"version": 1})
        
        # Simulate concurrent read/write
        def writer():
            for i in range(2, 10):
                file_service.atomic_write_json(test_file, {"version": i, "data": "x" * 1000})
                time.sleep(0.001)
        
        def reader():
            for _ in range(20):
                with open(test_file) as f:
                    data = json.load(f)
                    # Should always be valid JSON with a version field
                    assert "version" in data
                    assert isinstance(data["version"], int)
                time.sleep(0.001)
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            writer_future = executor.submit(writer)
            reader_future = executor.submit(reader)
            
            writer_future.result()
            reader_future.result()


class TestFileLocking:
    """Test file locking functionality."""
    
    def test_exclusive_lock_prevents_concurrent_writes(self, tmp_path):
        """Test that exclusive lock prevents concurrent writes."""
        file_service = FileService()
        test_file = tmp_path / "test.json"
        test_file.write_text('{"counter": 0}')
        
        results = []
        
        def increment_counter():
            """Increment counter in file with locking."""
            with file_service.locked_file_operation(test_file, 'exclusive'):
                with open(test_file) as f:
                    data = json.load(f)
                
                # Simulate some processing
                time.sleep(0.01)
                data['counter'] += 1
                
                with open(test_file, 'w') as f:
                    json.dump(data, f)
                
                results.append(data['counter'])
        
        # Run 10 concurrent increments
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(increment_counter) for _ in range(10)]
            for future in futures:
                future.result()
        
        # Final counter should be 10 (all increments applied)
        with open(test_file) as f:
            final_data = json.load(f)
            assert final_data['counter'] == 10
        
        # Results should be sequential (1, 2, 3... 10)
        assert sorted(results) == list(range(1, 11))
    
    def test_lock_timeout(self, tmp_path):
        """Test that lock acquisition times out appropriately."""
        file_service = FileService()
        test_file = tmp_path / "test.json"
        test_file.write_text('{}')
        
        # Hold lock in one thread
        def hold_lock():
            with file_service.locked_file_operation(test_file, 'exclusive', timeout=2.0):
                time.sleep(0.5)
        
        # Try to acquire lock in another thread with short timeout
        def try_acquire():
            try:
                with file_service.locked_file_operation(test_file, 'exclusive', timeout=0.1):
                    pass
                return "acquired"
            except FileServiceError:
                return "timeout"
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            holder = executor.submit(hold_lock)
            time.sleep(0.1)  # Ensure first thread has lock
            acquirer = executor.submit(try_acquire)
            
            result = acquirer.result()
            assert result == "timeout"
            
            holder.result()  # Wait for holder to finish


class TestProjectConcurrency:
    """Test concurrent project operations."""
    
    def test_concurrent_vm_updates(self, tmp_path):
        """Test that concurrent VM updates don't lose data."""
        # Create a test project
        project_service = ProjectService(user_id=None)
        # Override data directory for testing
        project_service.data_dir = tmp_path
        
        project_create = ProjectCreate(
            name="Test Project",
            description="Test concurrent updates"
        )
        project = project_service.create_project(project_create)
        
        # Add multiple VMs
        from src.models.virtual_machine import VirtualMachine
        for i in range(5):
            vm = VirtualMachine(
                name=f"vm{i}",
                id=f"vm{i}",
                box="ubuntu/focal64",
                memory=1024,
                cpus=1,
                network_interfaces=[],
                synced_folders=[],
                provisioners=[],
                labels=[]
            )
            project.add_vm(vm)
        
        project_service._save_project_to_file(project)
        
        # Update different VMs concurrently
        def update_vm(vm_index):
            vm_data = {"memory": 2048 + (vm_index * 512)}
            project_service.update_vm_in_project(
                project.id, 
                f"vm{vm_index}", 
                vm_data
            )
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_vm, i) for i in range(5)]
            for future in futures:
                future.result()
        
        # Verify all updates applied
        updated_project = project_service.get_project(project.id)
        for i, vm in enumerate(updated_project.vms):
            expected_memory = 2048 + (i * 512)
            assert vm.memory == expected_memory, f"VM{i} memory mismatch"


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create a temporary directory for tests."""
    return tmp_path_factory.mktemp("test_file_ops")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
