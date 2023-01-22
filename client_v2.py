#!/usr/bin/python3

from sys import argv, exit
from urllib.request import urlopen
from urllib.parse import urlencode
import json
from os.path import exists, join, basename, dirname, normpath, dirname, splitext
from os import listdir, mkdir, makedirs, getcwd, remove
from shutil import rmtree
from datetime import datetime as dt
from time import sleep

PC_SERVER_IP = "http://192.168.12.1:5000/npm"  # "http://127.0.0.1:5000/npm"
WIFI_SERVER_IP = "http://192.168.1.5:5000/npm"  # "http://192.168.12.1:5000/npm"
NPM_PORT = "8088"


def npm_init(path):
    print('''\nThis utility will walk you through creating a package.json file.
It only covers the most common items, and tries to guess sensible defaults.
          
Press ^C at any time to quit.\n''')

    package_name = input("package name: ({}) ".format(
        basename(path))).lower() or basename(path).lower()
    version = input("version: (1.0.0) ") or "1.0.0"
    description = input("description: ")
    entry_point = input("entry point: (index.js) ") or "index.js"
    # test_command = input("test command: ")
    # git_repository = input("git repository: ")
    # keywords = input("keywords: ")
    author = input("author: ")
    license = input("license: (ISC) ") or "ISC"

    package_json = {
        "name": package_name,
        "version": version,
        "description": description,
        "main": entry_point,
        "scripts": {
            "test": "echo \"Error: no test specified\" && exit 1"
        },
        "author": author,
        "license": license
    }

    print("About to write to {}/package.json:\n".format(path))
    print("{")
    print('  name": "{}",'.format(package_name))
    print('  "version": "{}",'.format(version))
    print('  "description": "{}",'.format(description))
    print('  "main": "{}",'.format(entry_point))
    print('''  "scripts": {
        "test": "echo Error: no test specified && exit 1"
  },''')
    print('  "author": "{}",'.format(author))
    print('  "license": "{}",'.format(license))
    print('}\n')

    sure = input("Is this OK? (yes) ").lower() or 'yes'
    if sure == "yes":
        with open(join(path, 'package.json'), 'w') as w_package:
            json.dump(package_json, w_package, indent=2)
            print("Created package.json file in {}".format(path))
    else:
        print("Aborted.\n")


def prompt_user_package():
    packs = input("Enter packages space separated>> ")
    packs = [i.replace(" ", "")
             for i in packs.split(" ") if i.replace(" ", "")]
    return packs


def prompt_project_path():
    path = input("Enter project's absolute path\npath>> ")
    if not path:
        print("Please enter project's path")
        main()

    if not exists(path):
        print("{} doesn't exist".format(path))
        main()
    return path


def check_ips():
    res = 0
    address = ""
    try:
        address = WIFI_SERVER_IP
        res = urlopen(WIFI_SERVER_IP).status
    except Exception as e:
        print(e)
        print("server {} is not running".format(address))
        res = urlopen(PC_SERVER_IP).status
        address = PC_SERVER_IP

    return res, address


def load_json(path):
    if exists(path):
        with open(path, 'r') as package_json:
            return json.loads(package_json.read())


def sep_dirs(path, dirs=[]):
    if not dirname(path):
        return [path] + dirs
    else:
        return sep_dirs(dirname(path), [basename(path)] + dirs)


def update_deps(proj_path, dep):
    pack, version = dep
    pjp = join(proj_path, 'package.json')
    package_json = load_json(pjp)
    deps = package_json.get("dependencies", {})
    deps[pack] = version
    package_json["dependencies"] = deps
    with open(pjp, 'w') as pj:
        json.dump(package_json, pj, indent=2)


def copy_file(address, url, path):
    try:
        # print("\t|-_->", normpath(basename(path)))
        r = urlopen("{}/{}".format(address, url))
        with open(path, 'wb') as file:
            file.write(r.read())
    except Exception as e:
        print("*"*9, e, "*"*9)


def create_dirs(data):
    address = data["address"].split(":")
    address = ":".join(address[:2]) + ":" + NPM_PORT
    proj_path = normpath(data["proj_path"])
    node_mod = join(proj_path, "node_modules")
    if not exists(node_mod):
        mkdir(node_mod)

    for pack, files in data["trees"].items():
        if files["files"]:
            pack = join(proj_path, pack)
            version = files["version"]
            packs_len = len(files["files"])
            for nfile, file in enumerate(files["files"]):
                _file = normpath(file)
                arr_dir = sep_dirs(dirname(_file))
                folder = join(node_mod, *arr_dir)
                if not exists(folder):
                    makedirs(folder)

                if basename(pack) in data["new_packs"]:
                    update_deps(proj_path, (basename(pack), version))
                    
                copy_file(address, file, join(folder, basename(_file)))
        else:
            print("[x] {} was not found!".format(pack))
            
        print("[%s] %s\r" % ("■"*(nfile+1//packs_len), file), end="")
        sleep(0.0009)

    else:
        print("\r", end="")
        print("Done copying %s\r" % " ".join(data["new_packs"]), end="")


def send_request(recurse=False, path="", proj_path=""):
    res, address = check_ips()
    if res == 200:
        if not recurse:
            if not exists(proj_path):
                print("{} doesn't exists! thumbass".format(proj_path))
                return send_request()

            if not exists(join(proj_path, 'package.json')):
                npm_init(proj_path)

        _ = list(load_json(join(proj_path, 'package.json')).get(
            'dependencies', {}).keys())
        print("{} are the installed packages".format(_))
        packs = prompt_user_package()
        if not packs:
            print("Please enter packages")
            return send_request(recurse=True, path=proj_path)
        else:
            try:
                r = urlopen(address, " ".join(packs).encode())
                r = r.read()
                return {
                    "address": address,
                    "proj_path": proj_path,
                    "trees": json.loads(r),
                    "new_packs": packs
                }
            except:
                print("server {} is not running".format(address))
    else:
        print("{} is not running".format(address))
        return


def prompt_user():
    packs = input("Enter space separated>> ")
    packs = [i.replace(" ", "")
             for i in packs.split(" ") if i.replace(" ", "")]
    return packs


def get_first_parent(path):
    if not dirname(path):
        return path
    else:
        return get_first_parent(dirname(path))


def check_nested_nodemod(package, global_packages):
    packages = []
    path = join(global_packages, package)
    if exists(join(path, 'node_modules')):
        _packs = [i for i in listdir(
            join(path, 'node_modules')) if i[0] != '.']
        _path = join(path, 'node_modules')
        if _packs:
            for _pack in _packs:
                __packs = get_deps(join(_path, _pack))
                if __packs:
                    packages += list(__packs.keys())
                packages += [_pack]
    return list(set(packages))


def get_deps(path):
    if exists(path):
        if exists(join(path, 'package.json')):
            return load_json(join(path, 'package.json')).get('dependencies', [])


def get_all_deps(arr, global_packages, deps=[]):
    if not len(arr):
        return deps
    else:
        res = get_deps(join(global_packages, arr[0]))
        if res:
            _deps = list(res.keys())
        else:
            _deps = []

        arr += check_nested_nodemod(arr[0], global_packages)

        _deps = [i for i in _deps if i not in arr[1:] and i not in deps]
        return get_all_deps((arr+_deps)[1:], global_packages, list(set(_deps+deps+[arr[0]])))


def delete_packs(packs, project_path):
    for pack in packs:
        if dirname(pack):
            pack = get_first_parent(pack)
        pack_path = join(project_path, 'node_modules', pack)
        if exists(pack_path):
            rmtree(pack_path)

    if exists(join(project_path, 'node_modules')) and not listdir(join(project_path, 'node_modules')):
        rmtree(join(project_path, 'node_modules'))


def update_json(deps, project_path):
    prev = load_json(join(project_path, 'package.json'))
    prev['dependencies'] = deps
    with open(join(project_path, 'package.json'), 'w') as update:
        json.dump(prev, update, indent=2)


def get_common_packages(victim, packs, global_packages):
    victim_packs = set(get_all_deps([victim], global_packages))
    intersections = []
    for pack in packs:
        inters = set(get_all_deps([pack], global_packages))
        intersections += list(victim_packs.intersection(inters))
    return list(set(intersections))


def remove_packs(_p, global_packages, project_path):
    if _p:
        print("Removable Packages>> {}".format(list(_p.keys())))
        packs = prompt_user()
        packs = [i for i in packs if i in list(_p.keys())]
        if packs:
            for pack in packs:
                if _p.get(pack, []):
                    del _p[pack]
                    intersections = get_common_packages(
                        pack, list(_p.keys()), global_packages)
                    packages = [i for i in get_all_deps(
                        packs, global_packages) if i not in intersections]
                    delete_packs(packages, project_path)
            update_json(_p, project_path)
            main(proj_path=project_path)
        else:
            print("\nNo package was selected\n")
            remove_packs(_p, global_packages, project_path)
    else:
        print("There are no packages to remove")
        main(proj_path=project_path)


def get_path(his):
    if exists(his):
        with open(his, 'r') as r:
            return json.loads(r.read())
    else:
        return


def save_path(obj, path):
    with open(path, 'w') as his:
        json.dump(obj, his)


def main(proj_path=""):
    _ = join(getcwd(), "npm_server.json")
    his = get_path(_)
    if his:
        proj_path = his.get('path', {})
        if not proj_path:
            print("No path was found")
            remove(_)
            main()
        print("Project path: {}".format(proj_path))

    if not proj_path:
        proj_path = prompt_project_path()
        if exists(proj_path):
            save_path({"path": proj_path}, _)
        else:
            print("{} doesn't exist".format(proj_path))
            main()

    if True:
        which = '''
        Enter 'a' to add package(s)
        Enter 'r' to remove package(s)
        Enter 'c' to change project path
        Enter 'q' to exuut\n
        '''
        which = input(which+"(a/r/q) >>>").lower()
        if which == 'a':
            trees = send_request(proj_path=proj_path)
            start = dt.now()
            create_dirs(trees)
            if len(trees["new_packs"]) <= 1:
                print("-"*50)
                print("Done copying {} package in {}s".format(len(trees["new_packs"]), dt.now() - start))
                print("-"*50)
            else:
                print("-"*50)
                print("Done copying {} packages in {}s".format(len(trees["new_packs"]), dt.now() - start))
                print("-"*50)
            main(proj_path=proj_path)
        elif which == 'r':
            if exists(join(proj_path, 'package.json')):
                deps = load_json(join(normpath(proj_path), "package.json")).get(
                    "dependencies", {})
                if not deps:
                    print("There are no packages")
                    main(proj_path=proj_path)
                remove_packs(deps, join(normpath(proj_path),
                                        "node_modules"), proj_path)
        elif which == 'c':
            remove(_)
            main()
        elif which == 'q':
            print('bye')
            exit()
        else:
            main(proj_path=proj_path)


if __name__ == "__main__":
    main()
