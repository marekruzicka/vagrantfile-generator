# Roadmap
This is in no particular order, just using it to store ideas.

## Contents
- [Plugin specific configuration](#per-plugin-configuration)
- [Provisioners](#provisioners)
- [Triggers](#triggers)
- [Networking rework](#networking-rework)
- [Fix labels](#fix-labels)
- [Support for networking in Bulk Edit](#support-for-networking-in-bulk-edit)

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


## Provisioners
- Add general support for provisioners.
  1. ansible
  2. shell
No idea how to integrate it, but working on it :)
```ruby
# Ansible provisioner
config.vm.provision "ansible" do |ansible|
  ansible.playbook = "common.yml"
  ansible.skip_tags  = "debug"
  ansible.extra_vars = {
    "root_pw" => root_pw,
    "nfs_server_ip" => nfs_server_ip,
    "nfs_export_path" => nfs_export_path,
    "nfs_mountpoint" => nfs_mountpoint,
    "proxy_url" => proxy_url
  }
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

## Fix labels
Labels are somehow implemented, it never worked.
Add labels to Vagrantfile as comments.

## Support for networking in Bulk Edit
- already have something like that for bulk create, so just add support to Bulkd Edit modal
