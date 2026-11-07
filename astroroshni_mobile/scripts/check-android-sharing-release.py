#!/usr/bin/env python3
"""Test sharing's native argument conversion using a built AAB and its R8 mapping.

Requires one connected Android device/emulator (or --serial). No app install,
login, provider request or sharing to another person is performed. This catches
release-only bridge failures; it does not test receiving apps or the share UI.
Run after ./gradlew :app:bundlePlayRelease.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--aab", type=Path, default=ROOT / "android/app/build/outputs/bundle/playRelease/app-play-release.aab")
parser.add_argument("--mapping", type=Path, default=ROOT / "android/app/build/outputs/mapping/playRelease/mapping.txt")
parser.add_argument("--serial")
args = parser.parse_args()
mapping = args.mapping.read_text()


def block(name):
    match = re.search(r"(?m)^" + re.escape(name) + r" -> ([^:]+):\n((?:[ #\t].*\n)*)", mapping)
    if not match:
        raise RuntimeError(f"Missing R8 mapping for {name}")
    return match.group(1), match.group(2)


def member(owner, name, method=False, parameters=None):
    arguments = re.escape(parameters) if parameters is not None else r"[^\n]*?"
    suffix = r"\(" + arguments + r"\)(?::[\d:]+)?" if method else ""
    matches = set(re.findall(r" " + re.escape(name) + suffix + r" -> (\S+)", block(owner)[1]))
    if len(matches) != 1:
        raise RuntimeError(f"Ambiguous R8 member {owner}.{name}: {matches}")
    return matches.pop()


module = "expo.modules.sharing.SharingModule"
function = "expo.modules.kotlin.functions.AnyFunction"
any_type = "expo.modules.kotlin.types.AnyType"
provider = "expo.modules.kotlin.types.TypeConverterProviderImpl"
converter = "expo.modules.kotlin.types.TypeConverter"
names = [
    block(module)[0], member(module, "definition", True),
    block(function)[0], member(function, "desiredArgsTypes"),
    block(any_type)[0], member(any_type, "kType"),
    block(provider)[0], member(provider, "INSTANCE"), member(provider, "obtainTypeConverter", True),
    block(converter)[0], member(converter, "convert", True), block("expo.modules.kotlin.AppContext")[0],
    block("kotlin.jvm.internal.Reflection")[0], member("kotlin.jvm.internal.Reflection", "typeOf", True, "java.lang.Class"),
]
sdk = Path(os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or Path.home() / "Library/Android/sdk")
build_tools = sorted((sdk / "build-tools").glob("*/d8"), key=lambda p: [int(v) for v in re.findall(r"\d+", p.parent.name)])
if not build_tools:
    raise RuntimeError("Set ANDROID_HOME to an SDK with Android build-tools")
java_home = os.environ.get("JAVA_HOME")
javac = str(Path(java_home) / "bin/javac") if java_home else shutil.which("javac")
adb = [str(sdk / "platform-tools/adb")] + (["-s", args.serial] if args.serial else [])
remote = "/data/local/tmp/astroroshni-sharing-test-" + uuid.uuid4().hex


def run(command):
    subprocess.run([str(arg) for arg in command], check=True)


with tempfile.TemporaryDirectory(prefix="astroroshni-sharing-test-") as temp:
    temp = Path(temp)
    run([javac, "--release", "8", "-d", temp, ROOT / "tests/android/SharingReleaseProbe.java"])
    run([build_tools[-1], "--output", temp / "probe.jar", temp / "SharingReleaseProbe.class"])
    with zipfile.ZipFile(args.aab) as bundle, zipfile.ZipFile(temp / "release.jar", "w") as dex:
        for entry in bundle.namelist():
            if entry.startswith("base/dex/") and entry.endswith(".dex"):
                dex.writestr(Path(entry).name, bundle.read(entry))
            elif entry.startswith("base/root/") and not entry.endswith("/"):
                # Kotlin reflection requires the kotlin_builtins resources too.
                dex.writestr(entry.removeprefix("base/root/"), bundle.read(entry))
    run(adb + ["shell", "mkdir", "-p", remote])
    try:
        run(adb + ["push", temp / "probe.jar", temp / "release.jar", remote + "/"])
        run(adb + ["shell", f"CLASSPATH={remote}/probe.jar:{remote}/release.jar", "app_process", "/system/bin", "SharingReleaseProbe"] + names)
    finally:
        run(adb + ["shell", "rm", "-rf", remote])
