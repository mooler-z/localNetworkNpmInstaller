#!/usr/bin/python3

import os
import json

from os.path import exists, join, basename, dirname, normpath
from os import listdir, mkdir, walk

from pprint import pprint

from flask import Flask
from flask import request
app = Flask(__name__)

GLOBAL_PACKAGE = normpath("/your/path/to/global/npm/packages")
GLOBAL_PACKAGE_PC_SERVER = "http://192.168.12.1:8088"
GLOBAL_PACKAGE_WIFI_SERVER = "http://192.168.1.5:8088"


def send_clean_packages(path):
    packages = []
    if os.path.exists(path):
        for pack in os.listdir(path):
            if pack[0] != '.':
                packages.append(pack)
    return packages


@app.route('/')
def hello_world():
    return "Hello, world!"


def load_json(path):
    if exists(path):
        with open(path, 'r') as package_json:
            return json.loads(package_json.read())


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


def get_deps(path):
    if exists(path):
        if exists(join(path, 'package.json')):
            return load_json(join(path, 'package.json')).get('dependencies', [])


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


def walk_get_tree(packs):
    files = {}
    for pack in packs:
        pack = normpath(pack)
        files[pack] = {
            "files": []
        }
        if exists(join(GLOBAL_PACKAGE, pack)):
            v = load_json(join(GLOBAL_PACKAGE, pack, "package.json"))[
                "version"]
            files[pack]["version"] = v
            for struct in walk(join(GLOBAL_PACKAGE, pack)):
                for file in struct[2]:
                    _global_pack = struct[0].replace(GLOBAL_PACKAGE, "")[1:]
                    _file = join(_global_pack, file)
                    files[pack]["files"].append(_file)
    return files


@app.route('/npm', methods=['GET', 'POST'])
def trial():
    if request.method == 'POST':
        packages = list(request.form)[0]
        packages = [pack.strip().lower()
                    for pack in packages.split(" ") if pack.strip().lower()]
        packages = get_all_deps(packages, GLOBAL_PACKAGE)
        trees = walk_get_tree(packages)
        return trees
    else:
        return 'I am up and running'
