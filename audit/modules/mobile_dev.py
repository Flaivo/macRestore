import json
import shutil
from pathlib import Path

from shared.inventory import save_inventory
from shared.terminal import run_command

PLUGIN = {
    'name': 'mobile_dev',
    'description': 'Backup Android keystores/AVD configs and Xcode provisioning profiles/simulators',
    'requires_password': False,
    'has_restore': True,
    'restore_items': [
        'android_keys',
        'android_avds',
        'xcode_profiles',
        'ios_simulators'
    ]
}


def _parse_ini_file(filepath):
    data = {}
    if not filepath.exists():
        return data
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith(';'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    data[key.strip()] = val.strip()
    except Exception:
        pass
    return data


def backup(context):
    result = {
        'android_keystores': [],
        'android_avds': [],
        'xcode_profiles': 0,
        'ios_simulators': []
    }
    files_dest = context.files / 'mobile_dev'

    # 1. Android Keystore
    android_dir = Path.home() / '.android'
    if android_dir.exists():
        debug_key = android_dir / 'debug.keystore'
        if debug_key.exists():
            dest = files_dest / 'android' / 'debug.keystore'
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(debug_key, dest)
            context.register_artifact(dest)
            result['android_keystores'].append('debug.keystore')

    # 2. Android AVD Configs (leggeri, no dischi/qcow2)
    avd_dir = android_dir / 'avd'
    if avd_dir.exists():
        avd_dest = files_dest / 'android_avd'
        for ini_file in avd_dir.glob('*.ini'):
            ini_data = _parse_ini_file(ini_file)
            avd_name = ini_file.stem
            
            dest_ini = avd_dest / ini_file.name
            dest_ini.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ini_file, dest_ini)
            context.register_artifact(dest_ini)

            avd_folder_name = f'{avd_name}.avd'
            source_avd_folder = avd_dir / avd_folder_name
            config_data = {}

            if source_avd_folder.exists() and source_avd_folder.is_dir():
                target_avd_folder = avd_dest / avd_folder_name
                target_avd_folder.mkdir(parents=True, exist_ok=True)

                for conf_name in ['config.ini', 'hardware-qemu.ini']:
                    conf_src = source_avd_folder / conf_name
                    if conf_src.exists():
                        conf_dst = target_avd_folder / conf_name
                        shutil.copy2(conf_src, conf_dst)
                        context.register_artifact(conf_dst)

                config_ini_path = source_avd_folder / 'config.ini'
                config_data = _parse_ini_file(config_ini_path)

            image_sysdir = config_data.get('image.sysdir.1', '')
            sdk_package = ''
            if image_sysdir:
                sdk_package = image_sysdir.strip('/').replace('/', ';')

            avd_info = {
                'name': avd_name,
                'target': ini_data.get('target', config_data.get('target', '')),
                'device_name': config_data.get('hw.device.name', ''),
                'abi': config_data.get('abi.type', ''),
                'tag': config_data.get('tag.id', ''),
                'sdk_package': sdk_package,
                'skin': config_data.get('skin.name', ''),
                'ram_mb': config_data.get('hw.ramSize', '')
            }
            result['android_avds'].append(avd_info)

    # 3. Xcode Provisioning Profiles
    prov_dir = Path.home() / 'Library' / 'MobileDevice' / 'Provisioning Profiles'
    if prov_dir.exists():
        dest_prov = files_dest / 'xcode' / 'Provisioning Profiles'
        shutil.copytree(prov_dir, dest_prov, dirs_exist_ok=True)
        for prof in dest_prov.glob('*.mobileprovision'):
            context.register_artifact(prof)
        count = len(list(prov_dir.glob('*.mobileprovision')))
        result['xcode_profiles'] = count

    # 4. iOS Simulators (simctl export)
    if shutil.which('xcrun'):
        cmd_result = run_command('xcrun simctl list --json')
        if cmd_result['success'] and cmd_result['stdout']:
            try:
                simctl_data = json.loads(cmd_result['stdout'])
                devices_by_runtime = simctl_data.get('devices', {})
                sim_summary = []

                for runtime, dev_list in devices_by_runtime.items():
                    runtime_name = runtime.split('.')[-1] if '.' in runtime else runtime
                    for dev in dev_list:
                        if dev.get('isAvailable', True):
                            sim_summary.append({
                                'name': dev.get('name', ''),
                                'udid': dev.get('udid', ''),
                                'device_type': dev.get('deviceTypeIdentifier', ''),
                                'runtime': runtime,
                                'runtime_name': runtime_name,
                                'state': dev.get('state', '')
                            })

                result['ios_simulators'] = sim_summary

                sim_dest = files_dest / 'xcode' / 'simulators.json'
                sim_dest.parent.mkdir(parents=True, exist_ok=True)
                with open(sim_dest, 'w', encoding='utf-8') as f:
                    json.dump(simctl_data, f, indent=2)
                context.register_artifact(sim_dest)
            except Exception:
                pass

    # 5. Genera istruzioni e script di ricostruzione DENTRO il backup
    recreate_sh_lines = [
        '#!/usr/bin/env bash',
        '# Auto-generated by MacRestore: Emulator & Simulator Recreation Script',
        'set -e',
        '',
        'echo "=== MacRestore: Mobile Emulators Recreation ==="',
        ''
    ]

    recreate_md_lines = [
        '# Ricostruzione Emulatori Mobile (MacRestore)',
        '',
        'Questo documento descrive i passaggi per ricreare i profili degli emulatori Android e dei simulatori iOS.',
        '',
        '---',
        '',
        '## 1. Android AVD',
        ''
    ]

    if result['android_avds']:
        recreate_sh_lines.append('# --- 1. Android SDK System Images & AVD Creation ---')
        recreate_sh_lines.append('echo "[1/2] Recreating Android AVDs..."')
        recreate_md_lines.append('### AVD Rilevati nel Backup:\n')

        packages_to_install = set()
        for avd in result['android_avds']:
            name = avd.get('name')
            device = avd.get('device_name') or 'pixel'
            sdk_pkg = avd.get('sdk_package')
            tag = avd.get('tag')
            abi = avd.get('abi')

            recreate_md_lines.append(f"- **{name}**:")
            recreate_md_lines.append(f"  - Device: `{device}`")
            recreate_md_lines.append(f"  - Target/SDK: `{sdk_pkg or avd.get('target')}`")
            recreate_md_lines.append(f"  - ABI: `{abi}` | Tag: `{tag}`")

            if sdk_pkg:
                packages_to_install.add(sdk_pkg)
                recreate_sh_lines.append(f'# Install SDK image and create AVD: {name}')
                recreate_sh_lines.append(f'echo "Installing system-image {sdk_pkg}..."')
                recreate_sh_lines.append(f'sdkmanager "{sdk_pkg}" || true')
                cmd_avd = f'avdmanager create avd -n "{name}" -k "{sdk_pkg}" --device "{device}" --force'
                if tag and tag != 'default':
                    cmd_avd += f' --tag "{tag}"'
                if abi:
                    cmd_avd += f' --abi "{abi}"'
                recreate_sh_lines.append(f'echo "Creating AVD {name}..."')
                recreate_sh_lines.append(f'{cmd_avd} || echo "Could not create AVD {name} automatically. Check sdkmanager/avdmanager."')
            else:
                recreate_sh_lines.append(f'# AVD {name}: specific package not detected, manual creation.')

        recreate_md_lines.append('\n### Comandi manuali Android:\n')
        recreate_md_lines.append('```bash')
        for pkg in packages_to_install:
            recreate_md_lines.append(f'sdkmanager "{pkg}"')
        for avd in result['android_avds']:
            name = avd.get('name')
            device = avd.get('device_name') or 'pixel'
            sdk_pkg = avd.get('sdk_package')
            if sdk_pkg:
                recreate_md_lines.append(f'avdmanager create avd -n "{name}" -k "{sdk_pkg}" --device "{device}" --force')
        recreate_md_lines.append('```\n')
        recreate_md_lines.append('> Nota: Le configurazioni personalizzate (`config.ini`) vengono ripristinate in `~/.android/avd/`.\n')
    else:
        recreate_md_lines.append('Nessun AVD Android presente nel backup.\n')

    recreate_md_lines.append('---\n')
    recreate_md_lines.append('## 2. iOS Simulators\n')

    if result['ios_simulators']:
        recreate_sh_lines.append('')
        recreate_sh_lines.append('# --- 2. iOS Simulators Recreation ---')
        recreate_sh_lines.append('echo "[2/2] Recreating iOS Simulators..."')
        recreate_md_lines.append('### Simulatori Rilevati nel Backup:\n')

        for sim in result['ios_simulators']:
            name = sim.get('name')
            dev_type = sim.get('device_type')
            runtime = sim.get('runtime')
            runtime_name = sim.get('runtime_name')

            recreate_md_lines.append(f"- **{name}** (`{runtime_name}`)")
            recreate_md_lines.append(f"  - Device Type: `{dev_type}`")
            recreate_md_lines.append(f"  - Runtime ID: `{runtime}`")

            if dev_type and runtime:
                recreate_sh_lines.append(f'# Create simulator: {name}')
                recreate_sh_lines.append(f'xcrun simctl create "{name}" "{dev_type}" "{runtime}" || echo "Could not create {name} (runtime {runtime_name} may need download in Xcode)"')

        recreate_md_lines.append('\n### Comandi manuali iOS Simulators:\n')
        recreate_md_lines.append('```bash')
        for sim in result['ios_simulators']:
            name = sim.get('name')
            dev_type = sim.get('device_type')
            runtime = sim.get('runtime')
            if dev_type and runtime:
                recreate_md_lines.append(f'xcrun simctl create "{name}" "{dev_type}" "{runtime}"')
        recreate_md_lines.append('```\n')
        recreate_md_lines.append('> Nota: Se un runtime non è installato, scaricalo da Xcode -> Settings -> Platforms.\n')
    else:
        recreate_md_lines.append('Nessun simulatore iOS personalizzato nel backup.\n')

    recreate_sh_lines.append('')
    recreate_sh_lines.append('echo "=== Recreation process finished! ==="')

    sh_path = files_dest / 'recreate_emulators.sh'
    sh_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sh_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(recreate_sh_lines) + '\n')
    context.register_artifact(sh_path)

    md_path = files_dest / 'recreate_emulators.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(recreate_md_lines) + '\n')
    context.register_artifact(md_path)

    print(
        'Mobile development backup completed: '
        f"{len(result['android_keystores'])} keystores, "
        f"{len(result['android_avds'])} Android AVDs, "
        f"{result['xcode_profiles']} Xcode profiles, "
        f"{len(result['ios_simulators'])} iOS simulators detected."
    )

    save_inventory(context, 'mobile_dev', result)
    return result

