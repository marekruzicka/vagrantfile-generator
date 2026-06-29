"""Utilities for rendering Ansible Vagrant provisioner blocks."""

from typing import Any


def _ruby_value(value: Any, indent: int) -> str:
    """Convert a Python value to a Ruby literal."""
    if isinstance(value, dict):
        return _dict_to_ruby_hash(value, indent=indent)
    if isinstance(value, str):
        escaped = (value
            .replace('\\', '\\\\')
            .replace('#', '\\#')
            .replace('\n', '\\n')
            .replace('\r', '\\r')
            .replace('"', '\\"'))
        return f'"{escaped}"'
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    return f'"{value}"'


def _dict_to_ruby_hash(d: dict, indent: int = 2) -> str:
    """Convert a Python dict to a Ruby hash literal using symbol keys."""
    if not d:
        return "{}"

    space = " " * indent
    closing_space = " " * max(indent - 2, 0)
    lines = ["{"]
    items = list(d.items())
    for index, (key, value) in enumerate(items):
        comma = "," if index < len(items) - 1 else ""
        lines.append(f"{space}:{key} => {_ruby_value(value, indent + 2)}{comma}")
    lines.append(f"{closing_space}}}")
    return "\n".join(lines)


def render_ansible_block(config: dict) -> str:
    """Render a Vagrant Ansible provisioner block."""
    lines = ['config.vm.provision "ansible" do |ansible|']
    lines.append(f'  ansible.playbook = {_ruby_value(config["playbook"], 2)}')

    extra_vars = config.get("extra_vars")
    if isinstance(extra_vars, dict) and extra_vars:
        lines.append(f"  ansible.extra_vars = {_dict_to_ruby_hash(extra_vars, indent=4)}")

    if config.get("tags"):
        lines.append(f'  ansible.tags = {_ruby_value(config["tags"], 2)}')

    if config.get("skip_tags"):
        lines.append(f'  ansible.skip_tags = {_ruby_value(config["skip_tags"], 2)}')

    if config.get("verbose", "off") != "off":
        lines.append(f'  ansible.verbose = {_ruby_value(config["verbose"], 2)}')

    if config.get("raw_args"):
        lines.append(f'  ansible.raw_arguments = {_ruby_value(config["raw_args"], 2)}')

    lines.append("end")
    return "\n".join(lines)
