# Ideas / ToDo
This is in no particular order, just using it to store ideas.

## Contents
- ~~[Plugin specific configuration](#plugin-specific-configuration)~~ (done)
- [Provisioners](#provisioners) - partialy done (global shell available)
- [Triggers](#triggers) - partialy done (global triggers available)
- [Networking rework](#networking-rework)
- [Fix labels](#fix-labels)
- ~~[Support for networking in Bulk Edit](#support-for-networking-in-bulk-edit)~~ (done)
- [Rewrite footer logic](#rewrite-footer-logic)

## Fix labels
Labels are somehow implemented, but never worked properly (at all :))
This could propbably be utilized with local provisioners and triggers -> apply based on tags.
- per project
- add labels to Vagrantfile as comments next to objects they apply to

## Support for networking in Bulk Edit
- already have something like that for bulk create, so just add support to Bulk Edit modal

## Rewrite footer logic
- order of links
  - based on file: name 1_name.md, 1_1_name.md, 2_name.md
- support for tabs on large pages (modals)
    - H1 defines tabs

## Provisioners
- ✅ Add general support for provisioners.
### Scope
  - ✅ global (all vms within a project) - DONE
  - local (selected vms only) - ToDo later
### Types
  1. ✅ shell - DONE
  2. ansible - ToDo later

Provisioners are defined globally in Settings (like plugin templates), then added to individual projects (like project plugins).
- ✅ Settings section for defining provisioner templates
- ✅ Project detail page section for adding/removing provisioners
- ✅ Add/Edit modal with shell provisioner type

#### Shell
- Add New Provisioner modal tab
  - Provisioner Name (required)
  - Description (optional)
  - Script (required, default "echo 'Vagrant shell provisioner'")
```ruby
$script = <<-SCRIPT
echo 'Vagrant shell provisioner'
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.provision "shell", inline: $script
end
```

#### Ansible
- Add New Provisioner modal tab
  - Provisioner Name (required)
  - Description (optional)
  - Playbook (required)
  - tags (optional)
  - skip_tags (optional)
  - extra_vars (optional)
  - vault_password_file (optional)

```ruby
Vagrant.configure("2") do |config|
  # Ansible provisioner - global
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "common.yml"
    ansible.tags = ["tag1", "tag2"]
    ansible.skip_tags  = "debug"
    ansible.vault_password_file = ".vault_pass.txt"
    ansible.extra_vars = {
      "root_pw" => "heslo",
      "nfs_server_ip" => "1.2.3.4",
      "nfs_export_path" => "/srv/vms/_shared_data",
      "nfs_mountpoint" => "/mnt/shared",
      "proxy_url" => ""
    }
  end
end
```

## Triggers
Pretty much same as above (no idea how)
Probably create global "trigger code snippets" like:
- rhc connect (after up)
- rhc disconnect (before destroy)

And handle them same way as plugins, or allow free text on the project level.
```ruby
# Triggers for RHC connect
config.trigger.after :up do |trigger|
  trigger.info = "Register VMs to RedHat Insights inventory"
  trigger.run_remote = {
    inline: "timeout 30s bash -c 'sudo rhc connect -o #{ENV['DEVENV_ORG_ID']} -a #{ENV['DEVENV_ACTIVATION_KEY']}'"
  }
  trigger.on_error = :continue
end
```
```ruby
# Triggers for RHC disconnect
config.trigger.before :destroy do |trigger|
  trigger.info = "Unregister VMs from RedHat Insights inventory"
  trigger.run_remote = {
    inline: "timeout 30s bash -c 'sudo rhc disconnect'"
  }
  trigger.on_error = :continue
end
```

## Networking rework
### Private network
Create networks on the project level and assign them to VMs, instead of assign IPs to VMs.
- have to keep track of already assigned IPs
    - already have that for static IPs
    might not be so difficult after all
- new network API
- proper subnet handling

## Plugin specific configuration
Extend plugins so they could contain plugin specific configuration.
```ruby
Vagrant.configure("2") do |config|
  ## Vagrant plugins settings
  # Hostmanager
  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.manage_guest = false

  # SSHConfigManager
  config.sshconfigmanager.enabled = false
  config.sshconfigmanager.ssh_config_dir = "~/.ssh/config.d"
  config.sshconfigmanager.manage_includes = true

  # Proxy
  if defined?(proxy_url) && !proxy_url.to_s.empty?
    config.proxy.http = proxy_url
    config.proxy.https = proxy_url
    config.proxy.no_proxy = no_proxy
  end
end
```
- Add additional input box (default config) to create_plugin modal.
- Update the Vagrantfile template

