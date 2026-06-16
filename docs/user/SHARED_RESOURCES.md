# Shared Resources in Public Mode

When running in **public mode** (`DEPLOYMENT_MODE=public`), system resources are separated into shared (read-only) and user-owned (editable) categories.

## Storage Structure

```
backend/data/
├── shared/              # Read-only for all users
│   ├── boxes/
│   ├── plugins/
│   ├── provisioners/
│   ├── triggers/
│   └── projects/
└── users/               # User-specific writable resources
    └── {user-id}/
        ├── boxes/
        ├── plugins/
        ├── provisioners/
        ├── triggers/
        └── projects/
```

## Resource Ownership

Each resource has two metadata fields:

- **`is_shared`** — `true` for system resources, `false` for user-created
- **`owner_id`** — `null` for shared resources, user ID for owned resources

## Permission Rules

| Operation  | Shared resources      | User-owned resources |
| ---------- | --------------------- | -------------------- |
| View       | ✅ All users          | ✅ Owner only        |
| Use in project | ✅ All users       | ✅ Owner only        |
| Edit       | ❌ Read-only          | ✅ Owner only        |
| Delete     | ❌ Read-only          | ✅ Owner only        |
| Copy       | ✅ Copy to my resources | N/A                |

## UI Indicators

Shared resources are visually distinct:

- **Amber border and background** on resource cards
- **"Shared" badge** with lock icon
- **Edit/Delete buttons hidden** — replaced by "Copy to My Resources" button
- **Favorites system** — star important shared resources to keep them visible
- **Global toggle** — hide/show all shared resources via Settings switch

## Adding Shared Resources (Admin)

To add new shared resources, place JSON files in the appropriate `/data/shared/{type}/` directory:

- Boxes: `/data/shared/boxes/{box-id}.json`
- Plugins: `/data/shared/plugins/{plugin-id}.json`
- Provisioners: `/data/shared/provisioners/{provisioner-id}.json`
- Triggers: `/data/shared/triggers/{trigger-id}.json`

Set `"is_shared": true` and `"owner_id": null` in each file. Restart the backend or reload to make them visible.

> **Note:** There is currently no admin UI for managing shared resources — files must be placed directly in the data directory.

## Migration: Self-Hosted → Public

Existing self-hosted data in `/data/shared/` automatically becomes read-only shared resources when switching to public mode. No manual migration required.

For box data specifically: if you have a legacy `boxes.json` file, run `backend/scripts/migrate_boxes.py` to convert it to per-box files.
