import os
import shutil
from pathlib import Path

PLUGIN = {
    'name': 'mobile_dev',
    'description': 'Restore Android Keystores/AVD configs and Xcode Provisioning Profiles/Simulator profiles'
}


def restore(context):
    base_src = context.files_dir / 'mobile_dev'
    android_dest = Path.home() / '.android'
    xcode_dest = Path.home() / 'Library' / 'MobileDevice' / 'Provisioning Profiles'
    prod_keys_dest = Path.home() / 'Desktop' / 'Android_Prod_Keys'

    if not base_src.exists():
        print('  [SKIP] No Mobile Dev data found.')
        return

    if context.dry_run:
        print(f'  [DRY-RUN] Would restore debug.keystore to {android_dest}')
        print(f'  [DRY-RUN] Would restore Android AVD configurations to {android_dest / "avd"}')
        print(f'  [DRY-RUN] Would restore Provisioning Profiles to {xcode_dest}')
        print(f'  [DRY-RUN] Would place production keys (.jks) in {prod_keys_dest}')
        print(f'  [DRY-RUN] Would restore emulator recreation script to {android_dest / "recreate_emulators.sh"}')
        return

    try:
        # 1. Debug Keystore
        debug_src = base_src / 'android' / 'debug.keystore'
        if debug_src.exists():
            android_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(debug_src, android_dest / 'debug.keystore')
            print('  [OK] Android debug.keystore restored.')

        # 2. Android AVD Configs
        avd_src = base_src / 'android_avd'
        if avd_src.exists():
            avd_target_dir = android_dest / 'avd'
            avd_target_dir.mkdir(parents=True, exist_ok=True)

            for ini_file in avd_src.glob('*.ini'):
                target_ini = avd_target_dir / ini_file.name
                with open(ini_file, 'r', encoding='utf-8', errors='ignore') as f_in:
                    lines = f_in.readlines()

                with open(target_ini, 'w', encoding='utf-8') as f_out:
                    for line in lines:
                        if line.strip().startswith('path='):
                            avd_folder = f'{ini_file.stem}.avd'
                            new_path = avd_target_dir / avd_folder
                            f_out.write(f'path={new_path}\n')
                        else:
                            f_out.write(line)

            for avd_folder in avd_src.glob('*.avd'):
                if avd_folder.is_dir():
                    target_folder = avd_target_dir / avd_folder.name
                    target_folder.mkdir(parents=True, exist_ok=True)
                    for conf_file in avd_folder.glob('*.ini'):
                        shutil.copy2(conf_file, target_folder / conf_file.name)

            print('  [OK] Android AVD configuration profiles restored.')

        # 3. Provisioning Profiles
        xcode_src = base_src / 'xcode' / 'Provisioning Profiles'
        if xcode_src.exists():
            xcode_dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(xcode_src, xcode_dest, dirs_exist_ok=True)
            print('  [OK] Xcode Provisioning Profiles restored.')

        # 4. Production Keystores
        prod_src = base_src / 'android_prod_keys'
        if prod_src.exists():
            prod_keys_dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(prod_src, prod_keys_dest, dirs_exist_ok=True)
            print(f'  [OK] Android production keys extracted to {prod_keys_dest}')

        # 5. Restore Recreate Guide and Script to ~/.android/
        for script_name in ['recreate_emulators.sh', 'recreate_emulators.md']:
            script_src = base_src / script_name
            if script_src.exists():
                android_dest.mkdir(parents=True, exist_ok=True)
                script_dst = android_dest / script_name
                shutil.copy2(script_src, script_dst)
                if script_name.endswith('.sh'):
                    try:
                        os.chmod(script_dst, 0o755)
                    except Exception:
                        pass
        if (android_dest / 'recreate_emulators.sh').exists():
            print(f'  [OK] Emulator recreation script restored to {android_dest / "recreate_emulators.sh"}')

    except Exception as e:
        print(f'  [ERROR] Mobile Dev error: {e}')


