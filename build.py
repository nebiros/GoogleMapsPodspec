#!/usr/bin/env python
import StringIO
import glob
import itertools
import json
import shutil
import subprocess
import sys, os
import tarfile
import tempfile
import urllib2

POD_NAME = "GoogleMaps"
SYSLIB_ROOT = {
    "iOS": "/Applications/Xcode.app/Contents/Developer/Platforms/"
           "iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk",
    "Simulator": "/Applications/Xcode.app/Contents/Developer/Platforms/"
                 "iPhoneSimulator.platform/Developer/SDKs/iPhoneSimulator.sdk",
}
BUILD_DIR = tempfile.mkdtemp()
GOOGLE_MAPS_BASE_BINARY = "{build}/Subspecs/Base/Frameworks/GoogleMapsBase.framework/Versions/A/GoogleMapsBase".format(build=BUILD_DIR)
GOOGLE_MAPS_FRAMEWORK_DIR = "{build}/Subspecs/Maps/Frameworks/GoogleMaps.framework".format(build=BUILD_DIR)
GOOGLE_MAPS_BINARY = "{google_maps_framework_dir}/Versions/A/GoogleMaps".format(google_maps_framework_dir=GOOGLE_MAPS_FRAMEWORK_DIR)
GOOGLE_MAPS_CORE_BINARY = "{build}/Subspecs/Maps/Frameworks/GoogleMapsCore.framework/Versions/A/GoogleMapsCore".format(build=BUILD_DIR)
LIBTOOL_CMD = ["libtool", 
    "-dynamic", GOOGLE_MAPS_BASE_BINARY, 
    "-dynamic", GOOGLE_MAPS_BINARY, 
    "-dynamic", GOOGLE_MAPS_CORE_BINARY, 
    "-weak_framework", "UIKit", 
    "-weak_framework", "Foundation", 
    "-weak_framework", "Security", 
    "-ObjC",
    "-install_name", "@rpath/{name}.framework/{name}".format(name=POD_NAME)]


def color(string, color="cyan"):
    """
    Returns the given string surrounded by the ansi escape symbols.
    """
    string = string.encode("utf-8")
    colors = {"red": 91, "green": 92, "purple": 94, "cyan": 96, "gray": 98}
    return "\033[{}m{}\033[00m".format(colors[color], string)


def execute(cmd):
    """
    Executes the given command. It prints it first and the result.

    - parameter cmd: The command to execute
    """
    print color("$ {}".format(" ".join(cmd)), color="gray")
    print color(subprocess.check_output(cmd), color="red")


def parse_pod(name):
    """
    Returns the archive url, linked frameworks and libraries from a given pod

    - parameter name: The cocoapods name
    """
    pods_json = subprocess.check_output(["pod", "spec", "cat", name])
    pod = json.loads(pods_json)
    
    file_url = pod["source"]["http"]
    
    frameworks = []
    libraries = []
    for spec in pod["subspecs"]:
        if "frameworks" in spec:
            frameworks += spec["frameworks"]

        if "libraries" in spec:
            libraries += spec["libraries"]

    frameworks = set(frameworks)
    libraries = set(libraries) | set(['objc', 'System'])
    return (file_url, frameworks, libraries)


def link(target="x86_64", frameworks=[], libraries=[]):
    """
    Creates a dynamic library for a given arch, linked to the given
    frameworks/libraries.

    - parameter target:     The architecture (x86_64, i386, armv7, etc)
    - parameter frameworks: The needed linked frameworks
    - parameter libraries:  The needed linked libraries
    """
    is_simulator = target in ("x86_64", "i386")
    platform = "Simulator" if is_simulator else "iOS"

    # Linking dependencies
    frameworks = reduce(lambda x, y: x + ['-framework'] + [y], frameworks, [])
    libraries = map(lambda x: "-l{}".format(x), libraries)
    fpath = "-F{}/System/Library/Frameworks/".format(SYSLIB_ROOT[platform])
    lpath = "-L{}/usr/lib/".format(SYSLIB_ROOT[platform])
    syslibroot = ["-syslibroot", SYSLIB_ROOT[platform]] if is_simulator else []

    output = tempfile.mktemp()
    version = "-{}_version_min".format(
        "ios_simulator" if is_simulator else "ios"
    )

    print color(u"\u26a1\ufe0f Linking for {} {}".format(platform, target))
    extra_args = ["-o", output, fpath, lpath, "-arch_only", target,
                  version, "8.0"]
    cmd = LIBTOOL_CMD + frameworks + syslibroot + extra_args + libraries
    execute(cmd)
    return output


def main():
    file_url, frameworks, libs = parse_pod(POD_NAME)

    print color("Downloading file {file_url}...".format(file_url=file_url), color="purple")
    compressed = urllib2.urlopen(file_url).read()
    tar = tarfile.open(fileobj=StringIO.StringIO(compressed))

    print color("Extracting tar.gz ...\n", color="purple")
    tar.extractall(BUILD_DIR)

    output = "{}/{}_dynamic.dylib".format(BUILD_DIR, POD_NAME)
    targets = ["x86_64", "i386", "armv7", "armv7s", "arm64"]
    dylibs = [link(target, frameworks, libs) for target in targets]

    print color(u"\u2600\ufe0f Creating dynamic library ...")
    cmd = ["lipo", "-output", output, "-create"] + dylibs
    execute(cmd)

    framework = GOOGLE_MAPS_FRAMEWORK_DIR
    framework_version = "{framework}/Versions/A".format(framework=framework)
    info_plist_source = "Versions/Current/Info.plist".format(framework_version=framework_version)
    info_plist_target = "{framework}/Info.plist".format(framework=framework)

    print "build dir {build}".format(build=BUILD_DIR)
    print color(u"\U0001f680  Copying Info.plist ...")
    shutil.copy("{framework_version}/Resources/GoogleMaps.bundle/Info.plist".format(framework_version=framework_version), framework_version)
    print color(u"\U0001f680  Modifying Info.plist ...")
    subprocess.call(["defaults", "write", "{framework_version}/Info.plist".format(framework_version=framework_version), "CFBundleExecutable", POD_NAME])
    print color(u"\U0001f680  Symlinking Info.plist ...")
    os.symlink(info_plist_source, info_plist_target)

    resources = "{framework_version}/Resources".format(framework_version=framework_version)
    print color(u"\U0001f680  Moving bundles out of Resources ...")
    for file in os.listdir(resources):
        shutil.move("{resources}/{file}".format(resources=resources, file=file), framework_version)
        os.symlink("Versions/Current/{file}".format(file=file), "{framework}/{file}".format(framework=framework, file=file))

    print color(u"\U0001f680  Removing Resources directory and symlinks ...")
    os.rmdir(resources)
    os.remove("{framework}/Resources".format(framework=framework))

    print color(u"\U0001f680  Replacing binary and creating tar.gz ...")
    shutil.move(output, GOOGLE_MAPS_BINARY)

    tarfile_name = file_url.rsplit("/", 1)[-1]
    targz = tarfile.open(tarfile_name, "w:gz")
    os.chdir(BUILD_DIR)
    for file in glob.glob("./*"):
        targz.add(file)

    print color(u"\U0001f44d  File {} created!".format(targz.name),
                color="green")


if __name__ == "__main__":
    main()
