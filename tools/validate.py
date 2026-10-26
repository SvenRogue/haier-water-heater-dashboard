"""Offline config/behavior/privacy checks; never connects to Home Assistant."""
from __future__ import annotations

import ast
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from jinja2 import Environment, StrictUndefined
import yaml

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'packages' / 'haier_heater.yaml'
DASHBOARD = ROOT / 'dashboards' / 'heater.yaml'


def render(template: str, states: dict[str, str]) -> str:
    env = Environment(undefined=StrictUndefined)
    env.globals.update(
        states=lambda entity: states.get(entity, 'unknown'),
        is_state=lambda entity, value: states.get(entity, 'unknown') == value,
    )
    return env.from_string(template).render().strip()


def main() -> None:
    data = yaml.safe_load(PACKAGE.read_text(encoding='utf-8'))
    switch = data['template'][0]['switch'][0]
    select = data['template'][1]['select'][0]
    native_power = 'select.example_heater_power'
    native_mode = 'select.example_heater_heatingmode'
    warm = 'switch.example_heater_heatkeepingstatus'
    onoff = 'switch.example_heater_onoffstatus'
    choices = [('800W(低)', '低档'), ('1200W(中)', '中档'), ('2000W(高)', '高档')]
    scenarios = [
        ('warm', {warm: 'on', native_mode: 'unknown', native_power: 'unknown'}, '智能温水中', False),
        ('boost', {warm: 'off', native_mode: '增容', native_power: 'unknown'}, '速热增容中', True),
        ('inactive', {warm: 'off', native_mode: 'unknown', native_power: 'unknown'}, '未启用', False),
    ] + [(label, {warm: 'off', native_mode: 'unknown', native_power: raw}, label, False)
         for raw, label in choices]
    for name, values, expected, boost in scenarios:
        values[onoff] = 'on'
        current = render(select['state'], values)
        options = ast.literal_eval(render(select['options'], values))
        assert current == expected, (name, current)
        assert current in options, (name, options)
        assert all(label in options for _, label in choices), options
        assert (render(switch['state'], values).lower() == 'true') == boost, name
        assert render(select['availability'], values).lower() == 'true', name
        assert render(switch['availability'], values).lower() == 'true', name
    offline = {onoff: 'unavailable', warm: 'unavailable'}
    for entity in (switch, select):
        assert render(entity['availability'], offline).lower() == 'false'
    online = {onoff: 'on', warm: 'on', native_mode: 'unknown', native_power: 'unknown'}
    mode_offline = dict(online, **{native_mode: 'unavailable'})
    for entity in (switch, select):
        assert render(entity['availability'], mode_offline).lower() == 'false'
    power_offline = dict(online, **{native_power: 'unavailable'})
    assert render(select['availability'], power_offline).lower() == 'false'
    assert render(switch['availability'], power_offline).lower() == 'true'
    actions = select['select_option'][0]
    command_template = actions['then'][0]['data']['option']
    env = Environment(undefined=StrictUndefined)
    for raw, label in choices:
        assert env.from_string(command_template).render(option=label) == raw
        assert env.from_string(actions['if'][0]['value_template']).render(option=label).lower() == 'true'
    for mode_label in ('智能温水中', '速热增容中', '未启用'):
        assert env.from_string(actions['if'][0]['value_template']).render(option=mode_label).lower() == 'false'
    assert switch['turn_on'][0]['data']['option'] == '增容'
    assert switch['turn_off'][0]['action'] == 'switch.turn_on'
    assert switch['turn_off'][0]['target']['entity_id'] == warm
    print('PASS: six mode scenarios, three command mappings, no-op mode labels, offline behavior')

    dashboard = yaml.safe_load(DASHBOARD.read_text(encoding='utf-8'))
    assert dashboard['views'][0]['max_columns'] == 2
    for view in dashboard['views']:
        for section in view['sections']:
            row = 0
            for card in section['cards']:
                if card['type'] == 'heading':
                    assert row == 0
                    continue
                row += card['grid_options']['columns']
                assert row <= 12, card
                row %= 12
            assert row == 0
    names = {card.get('name') for card in dashboard['views'][0]['sections'][0]['cards']}
    assert {'智能温水', '速热增容', '变速选择'} <= names
    ET.parse(ROOT / 'docs' / 'preview.svg')
    print('PASS: YAML, native dashboard grid, required controls, SVG syntax')

    # Detect obvious accidental private data; this is not a full secret scanner.
    patterns = {
        'private IPv4': r'\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|127(?:\.\d{1,3}){3})\b',
        'hardware address': r'(?i)(?<![a-z0-9])[a-f0-9]{12}(?![a-z0-9])',
        'phone number': r'(?<!\d)1[3-9]\d{9}(?!\d)',
        'local Windows path': r'(?i)[a-z]:[\\/](?:users|dsh|hermes)[\\/]',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'JWT': r'eyJ[a-zA-Z0-9_-]{12,}\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
        'GitHub token': r'gh[pousr]_[a-zA-Z0-9]{20,}',
    }
    count = 0
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or any(part in {'.git', '__pycache__', '.venv'} for part in path.relative_to(ROOT).parts):
            continue
        text = path.read_text(encoding='utf-8')
        for label, pattern in patterns.items():
            assert re.search(pattern, text) is None, (label, str(path.relative_to(ROOT)))
        count += 1
    print(f'PASS: privacy scan of {count} release files')


if __name__ == '__main__':
    main()
