# Plugin Configuration Feature - Implementation Guide

## ✅ Completed Backend Changes

### 1. Updated Plugin Model (`backend/src/models/plugin.py`)
Added `configuration` field to store plugin-specific Ruby code:
- `Plugin` model: Added `configuration: Optional[str]` field
- `PluginCreate` model: Added `configuration` field
- `PluginUpdate` model: Added `configuration` field

### 2. New File-Based Plugin Service (`backend/src/services/plugin_service.py`)
**REPLACED** the old single-file approach with individual plugin files:

**Old structure:**
```
data/plugins.json  (all plugins in one file)
```

**New structure:**
```
data/plugins/
├── uuid-1.json  (plugin 1)
├── uuid-2.json  (plugin 2)
└── uuid-3.json  (plugin 3)
```

**Key changes:**
- Each plugin stored in `data/plugins/{plugin_id}.json`
- Scales better for large configurations
- Easier to manage and track in git
- Consistent with project storage pattern

### 3. Migration Script (`backend/migrate_plugins.py`)
Created migration script to convert existing `plugins.json` to separate files:
- Creates backup of original file
- Migrates each plugin to individual file
- Adds `configuration` field (null) to existing plugins
- Renames old file to `plugins.json.old`

**To run migration:**
```bash
cd backend
python migrate_plugins.py
```

### 4. Updated Vagrantfile Template (`backend/src/services/vagrantfile_generator.py`)
Added plugin configuration section after plugin declaration:

```ruby
Vagrant.configure("2") do |config|
  # Configure required plugins
  config.vagrant.plugins = [
    { name: "vagrant-sshconfigmanager", version: "~> 1.0" }
  ]

  # Plugin-specific configuration
  # Configuration for vagrant-sshconfigmanager
  config.sshconfigmanager.enabled = true
  config.sshconfigmanager.ssh_config_dir = "~/.ssh/config.d/vagrant"
  config.sshconfigmanager.manage_includes = false
  # ... (rest of configuration)

  # VMs...
end
```

The configuration is automatically included if the plugin has a `configuration` field set.

## 🔧 TODO: Frontend Changes

You need to add the configuration textarea to these frontend modals:

### 1. Settings Page - Create Plugin Modal
**Location:** Find where users create new plugins (Settings page)

**Add this field after "Default Version":**
```html
<!-- Plugin Configuration -->
<div class="form-group">
  <label for="plugin-configuration" class="form-label">
    Plugin Configuration
    <span class="text-gray-500 text-sm ml-2">(Optional)</span>
  </label>
  <div class="mb-2 text-sm text-gray-600">
    <p>Plugin-specific configuration that will be added to the Vagrantfile.</p>
    <p class="text-xs mt-1">Example for vagrant-sshconfigmanager:</p>
    <code class="text-xs bg-gray-100 px-2 py-1 rounded">
      config.sshconfigmanager.enabled = true<br>
      config.sshconfigmanager.ssh_config_dir = "~/.ssh/config.d/vagrant"
    </code>
  </div>
  <textarea
    id="plugin-configuration"
    x-model="newPlugin.configuration"
    class="form-textarea font-mono text-sm"
    rows="8"
    placeholder="config.plugin_name.option = value&#10;config.plugin_name.another_option = true"
  ></textarea>
  <p class="text-xs text-gray-500 mt-1">
    Ruby code that will be inserted into the Vagrantfile. Leave empty if not needed.
  </p>
</div>
```

**Update the data model:**
```javascript
newPlugin: {
    name: '',
    description: '',
    source_url: '',
    documentation_url: '',
    default_version: '',
    configuration: '',  // ADD THIS
    is_deprecated: false
}
```

### 2. Settings Page - Edit Plugin Modal
**Add the same configuration textarea to the edit modal.**

**Update the edit data model:**
```javascript
editingPlugin: {
    ...
    configuration: '',  // ADD THIS
    ...
}
```

### 3. API Calls
The backend already supports the `configuration` field in:
- `POST /api/plugins` (create)
- `PUT /api/plugins/{plugin_id}` (update)
- `GET /api/plugins/{plugin_id}` (get)
- `GET /api/plugins` (list)

No API changes needed! Just include `configuration` in the request body.

## 📝 Example Plugin Configurations

### vagrant-sshconfigmanager
```ruby
config.sshconfigmanager.enabled = true
config.sshconfigmanager.ssh_config_dir = "~/.ssh/config.d/vagrant"
config.sshconfigmanager.manage_includes = false
config.sshconfigmanager.auto_create_dir = true
config.sshconfigmanager.cleanup_empty_dir = true
config.sshconfigmanager.auto_remove_on_destroy = true
config.sshconfigmanager.update_on_reload = true
config.sshconfigmanager.refresh_on_provision = true
config.sshconfigmanager.keep_config_on_halt = true
config.sshconfigmanager.project_isolation = true
```

### vagrant-hostmanager
```ruby
config.hostmanager.enabled = true
config.hostmanager.manage_host = true
config.hostmanager.manage_guest = false
config.hostmanager.ignore_private_ip = false
config.hostmanager.include_offline = true
```

### vagrant-proxyconf
```ruby
if Vagrant.has_plugin?("vagrant-proxyconf")
  config.proxy.http = "http://proxy.example.com:8080"
  config.proxy.https = "http://proxy.example.com:8080"
  config.proxy.no_proxy = "localhost,127.0.0.1,.example.com"
end
```

## 🚀 Deployment Steps

1. **Run migration script:**
   ```bash
   cd backend
   python migrate_plugins.py
   ```

2. **Update frontend modals** (see TODO section above)

3. **Build and restart containers:**
   ```bash
   make build
   make restart
   ```

4. **Test:**
   - Create a new plugin with configuration
   - Edit existing plugin to add configuration
   - Generate Vagrantfile and verify configuration is included
   - Check that configuration renders properly in the Vagrantfile

## 📂 File Changes Summary

### Backend (✅ Complete)
- `backend/src/models/plugin.py` - Added `configuration` field
- `backend/src/services/plugin_service.py` - NEW file-based storage
- `backend/src/services/plugin_service.old.py` - Backup of old service
- `backend/src/services/vagrantfile_generator.py` - Updated template
- `backend/migrate_plugins.py` - Migration script

### Frontend (🔧 TODO)
- Settings page - Add configuration textarea to create plugin modal
- Settings page - Add configuration textarea to edit plugin modal
- Update JavaScript data models to include `configuration` field

## 🎯 Benefits

1. **Scalability:** Large plugin configurations don't bloat a single file
2. **Git-friendly:** Changes to one plugin don't affect others in diffs
3. **Performance:** Load only needed plugins
4. **Consistency:** Follows same pattern as projects
5. **Safety:** Corruption of one file doesn't affect all plugins
6. **Flexibility:** Users can define complex plugin configurations

## ⚠️ Important Notes

- The `configuration` field is optional - plugins without configuration work as before
- Configuration is raw Ruby code - will be inserted into Vagrantfile as-is
- Users are responsible for correct Ruby syntax
- The configuration appears in Vagrantfile after plugin declaration but before VM definitions
- Empty/null configuration fields are ignored (no output in Vagrantfile)

