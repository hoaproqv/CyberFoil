#!/usr/bin/env python3
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Package CyberFoil into a standalone installer NSP")
    parser.add_argument("--nro", default="cyberfoil.nro", help="Path to cyberfoil.nro")
    parser.add_argument("--hacbrewpack", default=None, help="Path to hacbrewpack binary")
    parser.add_argument("--out", default="CyberFoil.nsp", help="Output NSP file path")
    parser.add_argument("--titleid", default="010932CF662BC000", help="Title ID for NSP")
    parser.add_argument("--titlename", default="Bichen Shop Game", help="Title Name")
    parser.add_argument("--titlepublisher", default="Bichen Shop", help="Title Publisher")
    parser.add_argument("--host", default="bichen.kozow.com", help="Remote host")
    parser.add_argument("--port", type=int, default=6868, help="Remote port")
    parser.add_argument("--protocol", default="http", help="Remote protocol")
    parser.add_argument("--workdir", default="build_nsp", help="Temporary build directory")
    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    nro_path = os.path.abspath(args.nro)
    if not os.path.isfile(nro_path):
        print(f"ERROR: NRO file not found at {nro_path}", file=sys.stderr)
        sys.exit(1)

    template_dir = os.path.join(repo_root, "tools", "installer_template")
    if not os.path.isdir(template_dir):
        print(f"ERROR: installer_template directory not found at {template_dir}", file=sys.stderr)
        sys.exit(1)

    # Locate hacbrewpack
    hacbrewpack = args.hacbrewpack
    if not hacbrewpack:
        # Check in common paths
        possible = [
            "hacbrewpack",
            "hacbrewpack.exe",
            os.path.join(repo_root, "hacBrewPack", "hacbrewpack"),
            os.path.join(repo_root, "hacBrewPack", "hacbrewpack.exe"),
            os.path.expandvars(r"%APPDATA%\Python\Python39\site-packages\nton\bin\hacbrewpack.exe"),
            os.path.expanduser("~/.local/bin/hacbrewpack"),
        ]
        for p in possible:
            found = shutil.which(p) or (os.path.isfile(p) and p)
            if found:
                hacbrewpack = found
                break

    if not hacbrewpack or not (shutil.which(hacbrewpack) or os.path.isfile(hacbrewpack)):
        print("ERROR: hacbrewpack executable could not be found. Please specify with --hacbrewpack", file=sys.stderr)
        sys.exit(1)

    print(f"Using hacbrewpack: {hacbrewpack}")
    print(f"Packaging NRO: {nro_path} ({os.path.getsize(nro_path)} bytes)")

    # Prepare build directory
    build_dir = os.path.abspath(args.workdir)
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir, exist_ok=True)

    exefs_dir = os.path.join(build_dir, "exefs")
    logo_dir = os.path.join(build_dir, "logo")
    control_dir = os.path.join(build_dir, "control")
    romfs_dir = os.path.join(build_dir, "romfs")
    nsp_out_dir = os.path.join(build_dir, "hacbrewpack_nsp")
    os.makedirs(nsp_out_dir, exist_ok=True)

    # 1. Copy exefs
    shutil.copytree(os.path.join(template_dir, "exefs"), exefs_dir)

    # 2. Copy logo
    shutil.copytree(os.path.join(template_dir, "logo"), logo_dir)

    # 3. Copy control
    shutil.copytree(os.path.join(template_dir, "control"), control_dir)

    # Update icon in control if available
    icon_source = os.path.join(repo_root, "romfs", "images", "icon.jpg")
    icon_target = os.path.join(control_dir, "icon_AmericanEnglish.dat")
    if os.path.isfile(icon_source):
        try:
            from PIL import Image
            img = Image.open(icon_source)
            resized = img.resize((256, 256), Image.Resampling.LANCZOS).convert("RGB")
            resized.save(icon_target, format="JPEG", quality=95)
            print("Prepared 256x256 icon from romfs/images/icon.jpg")
        except Exception as e:
            print(f"Warning: PIL failed to resize icon: {e}; using existing icon")

    # 4. Prepare romfs
    shutil.copytree(os.path.join(template_dir, "romfs"), romfs_dir)
    cf_dir = os.path.join(romfs_dir, "switch", "CyberFoil")
    os.makedirs(os.path.join(cf_dir, "logs"), exist_ok=True)
    os.makedirs(os.path.join(cf_dir, "remote_icons"), exist_ok=True)
    remotes_dir = os.path.join(cf_dir, "remotes")
    os.makedirs(remotes_dir, exist_ok=True)

    # Copy cyberfoil.nro
    shutil.copy2(nro_path, os.path.join(cf_dir, "cyberfoil.nro"))

    # Write config.json
    remote_url = f"{args.protocol}://{args.host}:{args.port}/"
    config_data = {
        "autoUpdate": True,
        "deletePrompt": False,
        "gAuthKey": "AIzaSyBMqv4dXnTJOGQtZZS3CBjvf748QvxSzF0",
        "gayMode": True,
        "httpUserAgent": "",
        "httpUserAgentMode": "default",
        "ignoreReqVers": True,
        "languageSetting": 99,
        "lastNetUrl": remote_url,
        "mtpExposeAlbum": False,
        "offlineDbAutoCheckOnStartup": True,
        "offlineDbManifestUrl": "https://github.com/luketanti/CyberFoil-DB/releases/latest/download/offline_db_manifest.json",
        "oledMode": True,
        "overClock": True,
        "remoteAllBaseOnly": True,
        "remoteHideInstalled": True,
        "remoteHideInstalledSection": True,
        "remoteLegacyMode": False,
        "remotePass": "",
        "remoteRememberSelection": False,
        "remoteSelection": [],
        "remoteStartGridMode": False,
        "remoteUrl": remote_url,
        "remoteUser": "",
        "soundEnabled": True,
        "usbAck": False,
        "validateNCAs": False,
        "verboseInstallLogging": False
    }
    with open(os.path.join(cf_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)

    # Write remote shop file
    remote_shop = {
        "remote": {
            "favourite": True,
            "host": args.host,
            "password": "",
            "path": "/",
            "port": args.port,
            "protocol": args.protocol,
            "title": args.titlename,
            "username": ""
        }
    }
    with open(os.path.join(remotes_dir, "BichenShop.json"), "w", encoding="utf-8") as f:
        json.dump(remote_shop, f, indent=4)

    # 5. Write keys.dat
    keys_dat = os.path.join(build_dir, "keys.dat")
    with open(keys_dat, "w", encoding="utf-8") as f:
        f.write("header_key = aeaab1ca08adf9befa80c98f980e1a1ef4c2b9da1d033efbb9df3cf6f3eb1ffb\n")
        f.write("key_area_key_application_00 = 04040404040404040404040404040404\n")

    # 6. Run hacbrewpack
    cmd = [
        hacbrewpack,
        "-k", keys_dat,
        "--titleid", args.titleid,
        "--titlename", args.titlename,
        "--titlepublisher", args.titlepublisher,
        "--exefsdir", exefs_dir,
        "--romfsdir", romfs_dir,
        "--logodir", logo_dir,
        "--controldir", control_dir,
        "--nspdir", nsp_out_dir
    ]
    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=build_dir)
    if res.returncode != 0:
        print(f"ERROR: hacbrewpack exited with code {res.returncode}", file=sys.stderr)
        sys.exit(res.returncode)

    # Find created NSP
    generated_nsps = glob.glob(os.path.join(nsp_out_dir, "*.nsp"))
    if not generated_nsps:
        print("ERROR: No NSP found in output directory!", file=sys.stderr)
        sys.exit(1)

    gen_nsp = generated_nsps[0]
    out_final = os.path.abspath(args.out)
    shutil.copy2(gen_nsp, out_final)
    print(f"SUCCESS: Created standalone NSP: {out_final} ({os.path.getsize(out_final)} bytes)")

if __name__ == "__main__":
    main()
