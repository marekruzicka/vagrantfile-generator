# Data Models — Vagrantfile Generator

This document summarizes the main data models used by the backend and provides JSON Schemas for fast reference and API / UI validation.

Resources covered:
- Box
- Plugin (catalog) and PluginConfiguration (per-VM)
- GlobalTrigger / TriggerConfig
- Provisioner (VM-level) and GlobalProvisioner
- Project (root model) and VirtualMachine (nested in Project)

Note: many resources include `is_shared`, `owner_id` and `source_id` fields to support the multi-user/shared resource semantics.
New resources created by the API will include `is_shared` and `owner_id` metadata in the stored JSON files; when returned via public-mode APIs, the backend ensures `is_shared` and `owner_id` are present in responses (shared resources have `owner_id: null`).

---

## Box
File: `backend/src/models/box.py`

Summary:
- Holds Vagrant box metadata, provider and optional source URL.
- Fields: id, name, description, provider, version, url, created_at, updated_at, is_shared, owner_id, source_id.

JSON Schema:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Box",
  "type": "object",
  "required": ["id", "name", "description", "created_at", "updated_at"],
  "properties": {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "description": {"type": "string"},
    "provider": {"type": "string", "default": "libvirt"},
    "version": {"type": ["string", "null"]},
    "url": {"type": ["string", "null"]},
    "created_at": {"type": "string"},
    "updated_at": {"type": "string"},
    "is_shared": {"type": ["boolean", "null"]},
    "owner_id": {"type": ["string", "null"]},
    "source_id": {"type": ["string", "null"]}
  }
}
```

Example:
```json
{
  "id": "box-001",
  "name": "generic/ubuntu2204",
  "description": "Ubuntu 22.04 base image",
  "provider": "libvirt",
  "version": "~> 1.0",
  "created_at": "2025-01-01T12:00:00",
  "updated_at": "2025-01-10T08:00:00",
  "is_shared": true
}
```

---

## Plugin and PluginConfiguration
Files: `backend/src/models/plugin.py`, `backend/src/models/plugin_configuration.py`

Summary:
- `Plugin` — catalog entry, can be shared; includes descriptions and default configuration Ruby code.
- `PluginConfiguration` — configuration applied to a VM (or globally) with optional version and plugin `config` dict.

Plugin JSON Schema:
```json
{
  "title": "Plugin",
  "type": "object",
  "required": ["id", "name", "created_at", "updated_at"],
  "properties": {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "description": {"type": ["string", "null"]},
    "source_url": {"type": ["string", "null"]},
    "documentation_url": {"type": ["string", "null"]},
    "default_version": {"type": ["string", "null"]},
    "configuration": {"type": ["string", "null"]},
    "is_deprecated": {"type": "boolean"},
    "created_at": {"type": "string"},
    "updated_at": {"type": "string"},
    "is_shared": {"type": ["boolean", "null"]},
    "owner_id": {"type": ["string", "null"]},
    "source_id": {"type": ["string", "null"]}
  }
}
```

PluginConfiguration JSON Schema (applied to VM or globally):
```json
{
  "title": "PluginConfiguration",
  "type": "object",
  "required": ["name"],
  "properties": {
    "name": {"type": "string"},
    "version": {"type": ["string", "null"]},
    "config": {"type": "object"},
    "scope": {"type": "string", "enum": ["vm", "global"]},
    "is_deprecated": {"type": "boolean"}
  }
}
```

Example:
```json
{
  "name": "vagrant-vbguest",
  "version": "~> 0.30.0",
  "config": {"auto_update": false},
  "scope": "vm"
}
```

---

## Trigger (GlobalTrigger / TriggerConfig)
File: `backend/src/models/global_trigger.py`

Summary:
- Represents lifecycle triggers added in settings and applied to project's VMs via `trigger_config`.
- `TriggerConfig` has `timing` (before/after), `stage` (like `provision`), `name`, `info`, `warn` and either `run` (host) or `run_remote_inline` (inside VM). `on_error` can be `halt` or `continue`.

JSON Schema (GlobalTrigger):
```json
{
  "title": "GlobalTrigger",
  "type": "object",
  "required": ["id", "name", "trigger_config"],
  "properties": {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "description": {"type": ["string", "null"]},
    "trigger_config": {
      "type": "object",
      "required": ["timing", "stage"],
      "properties": {
        "timing": {"type": "string", "enum": ["before", "after"]},
        "stage": {"type": "string"},
        "name": {"type": ["string", "null"]},
        "info": {"type": ["string", "null"]},
        "warn": {"type": ["string", "null"]},
        "run": {"type": ["string", "null"]},
        "run_remote_inline": {"type": ["string", "null"]},
        "on_error": {"type": "string", "enum": ["halt", "continue"], "default": "continue"}
      }
    },
    "created_at": {"type": "string"},
    "updated_at": {"type": "string"},
    "is_shared": {"type": ["boolean", "null"]},
    "owner_id": {"type": ["string", "null"]}
  }
}
```

Notes:
- Validation enforces a non-empty `stage` and that one of `run` or `run_remote_inline` is present.

Example:
```json
{
  "id": "trigger-001",
  "name": "ProvisionDB",
  "trigger_config": {
    "timing": "after",
    "stage": "provision",
    "run_remote_inline": "sudo systemctl start postgresql",
    "on_error": "halt"
  }
}
```

---

## Provisioner (VM-level) and GlobalProvisioner
Files: `backend/src/models/provisioner.py`, `backend/src/models/global_provisioner.py`

Summary:
- VM-level `Provisioner`: typed via `ProvisionerType`. `shell` requires exactly one of `script_path` or `inline`. `args` and `privileged` control runtime.
- `GlobalProvisioner`: a global shell script applied to many VMs; stores script content or external path with run controls.

Provisioner JSON Schema (VM-level):
```json
{
  "title": "Provisioner",
  "type": "object",
  "required": ["type"],
  "properties": {
    "type": {"type": "string", "enum": ["shell", "ansible", "puppet", "chef"]},
    "script_path": {"type": ["string", "null"]},
    "inline": {"type": ["string", "null"]},
    "args": {"type": "array", "items": {"type":"string"}},
    "privileged": {"type": "boolean"},
    "config": {"type": "object"}
  }
}
```

Global Provisioner JSON Schema:
```json
{
  "title": "GlobalProvisioner",
  "type": "object",
  "required": ["id", "name", "type"],
  "properties": {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "description": {"type": ["string", "null"]},
    "type": {"type": "string", "enum": ["shell"]},
    "scope": {"type": "string", "enum": ["global"]},
    "shell_config": {
      "type": "object",
      "properties": {
        "script": {"type": "string"},
        "privileged": {"type": "boolean"},
        "run": {"type": "string", "enum": ["once", "always", "never"]},
        "path": {"type": ["string", "null"]}
      }
    }
  }
}
```

Example (VM-level shell provisioner):
```json
{
  "type": "shell",
  "script_path": "scripts/bootstrap.sh",
  "args": ["--verbose"],
  "privileged": true
}
```

---

## Project
File: `backend/src/models/project.py`

Summary:
- Project is the root container for VMs and global resources.
- Fields: id, name, description, version, created_at, updated_at, vms, global_plugins, global_provisioners, global_triggers, deployment_status.
- VMs must have unique names and the project must contain at least one VM before generation.

Project JSON Schema (simplified; `vms` references `VirtualMachine` schema):
```json
{
  "title": "Project",
  "type": "object",
  "required": ["id", "name", "created_at", "updated_at"],
  "properties": {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "description": {"type": "string"},
    "version": {"type": "string"},
    "created_at": {"type": "string"},
    "updated_at": {"type": "string"},
    "vms": {"type": "array", "items": {"$ref": "#/definitions/VirtualMachine"}},
    "global_plugins": {"type": "array", "items": {"type": "string"}},
    "global_provisioners": {"type": "array", "items": {"type": "string"}},
    "global_triggers": {"type": "array", "items": {"type": "string"}},
    "deployment_status": {"type": "string", "enum": ["draft", "ready"]}
  },
  "definitions": {
    "VirtualMachine": {
      "type": "object",
      "required": ["name", "box"],
      "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "box": {"type": "string"},
        "hostname": {"type": ["string", "null"]},
        "memory": {"type": "number"},
        "cpus": {"type": "number"},
        "network_interfaces": {"type": "array", "items": {"type": "object"}},
        "synced_folders": {"type": "array", "items": {"type": "object"}},
        "provisioners": {"type": "array", "items": {"$ref": "#/definitions/Provisioner"}},
        "plugins": {"type": "array", "items": {"$ref": "#/definitions/PluginConfiguration"}}
      }
    },
    "Provisioner": {
      "type": "object",
      "properties": {
        "type": {"type": "string"},
        "script_path": {"type": ["string", "null"]},
        "inline": {"type": ["string", "null"]}
      }
    },
    "PluginConfiguration": {"type": "object"}
  }
}
```

Example:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "my-project",
  "description": "Sample project",
  "version": "1.0.0",
  "vms": [
    {
      "name": "web",
      "box": "ubuntu/jammy64",
      "memory": 2048,
      "cpus": 2,
      "network_interfaces": [],
      "provisioners": [],
      "plugins": []
    }
  ],
  "global_plugins": [],
  "global_provisioners": [],
  "global_triggers": [],
  "deployment_status": "draft"
}
```
