import pytest

from src.models.global_provisioner import (
    AnsibleProvisionerConfig,
    GlobalProvisioner,
    GlobalProvisionerUpdate,
    ShellProvisionerConfig,
)
from src.utils.ansible import _dict_to_ruby_hash, _ruby_value, render_ansible_block


def test_render_ansible_block_renders_core_fields():
    result = render_ansible_block(
        {
            "playbook": "site.yml",
            "extra_vars": {"key": "val", "num": 42},
            "tags": "prod",
            "skip_tags": "debug",
            "verbose": "vv",
            "raw_args": "--check",
        }
    )

    assert 'config.vm.provision "ansible" do |ansible|' in result
    assert 'ansible.playbook = "site.yml"' in result
    assert "ansible.extra_vars = {" in result
    assert ':key => "val"' in result
    assert ':num => 42' in result
    assert 'ansible.tags = "prod"' in result
    assert 'ansible.skip_tags = "debug"' in result
    assert 'ansible.verbose = "vv"' in result
    assert 'ansible.raw_arguments = "--check"' in result
    assert result.endswith("end")


def test_render_ansible_block_omits_empty_optional_fields():
    result = render_ansible_block(
        {"playbook": "test.yml", "tags": "", "skip_tags": "", "raw_args": ""}
    )

    assert "ansible.tags" not in result
    assert "ansible.skip_tags" not in result
    assert "ansible.raw_arguments" not in result


def test_ruby_value_escapes_interpolation_and_quotes():
    rendered = _ruby_value('#{system("rm -rf /")}', 2)

    assert rendered.startswith('"') and rendered.endswith('"')
    assert '\\#{' in rendered
    assert '#{system' not in rendered.replace('\\#{', '')


def test_dict_to_ruby_hash_renders_nested_hashes():
    result = _dict_to_ruby_hash({"a": "b", "c": {"d": "e", "f": 1}}, indent=2)

    assert ':a => "b"' in result
    assert ':d => "e"' in result
    assert ':f => 1' in result


def test_global_provisioner_update_rejects_both_configs():
    shell = ShellProvisionerConfig(script="echo hi")
    ansible = AnsibleProvisionerConfig(playbook="site.yml")

    with pytest.raises(ValueError, match="Cannot set both shell_config and ansible_config"):
        GlobalProvisionerUpdate(shell_config=shell, ansible_config=ansible)


def test_global_provisioner_get_vagrant_config_renders_ansible_block():
    provisioner = GlobalProvisioner(
        id="p1",
        name="Ansible Provisioner",
        type="ansible",
        ansible_config=AnsibleProvisionerConfig(
            playbook="site.yml",
            extra_vars='{"env": "prod"}',
            tags="deploy",
            skip_tags="debug",
            verbose="v",
            raw_args="--check",
        ),
    )

    result = provisioner.get_vagrant_config()

    assert "# Ansible provisioner: Ansible Provisioner" in result
    assert 'ansible.playbook = "site.yml"' in result
    assert ':env => "prod"' in result
    assert 'ansible.tags = "deploy"' in result
    assert 'ansible.skip_tags = "debug"' in result
    assert 'ansible.verbose = "v"' in result
    assert 'ansible.raw_arguments = "--check"' in result
