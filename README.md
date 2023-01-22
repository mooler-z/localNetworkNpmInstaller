## Local Network npm installer

    The internet was cut off in the place I am in
    so when I am working on a node project with ppl
    and they don't have a particular npm package
    we used these scripts to make my machine an npm
    package machine then they can install them
    

The script **HEAVILY** relies on recursion and the rest is details.


## This script is for the machine with the node_modules
    - this machine should first host the node_modules folder with somekind of server(mine was http-server)
```sh
python3 npm_server.py
```

## This script is for the end user machine
```sh
python3 client.py
```
The prompt is pretty intuitive!