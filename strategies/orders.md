# Examples for orders

These are the messages exchanged between the commander and the low level API.

For the strategies, see the strategies.md in the swarm_manager folder.

### Connect
````json
{
    "command": "connect",
    "parameters": {
        "name": "Mystinu", 
        "username": "blackfalcon0", 
        "password": "...", 
        "server": "Julith"
    }
}
````

### Disconnect
````json
{
    "command": "connect",
    "parameters": {
        "name": "Mystinu"
    }
}
````

### Move
````json
{
    "command": "move",
    "parameters": {
        "isUsingNewMovementSystem": "Boolean (isUsingNewMovementSystem from map_info)",
        "cells": ["List of cells (rawCells from map_info)"]
    }
}
````

### Change map
````json
{
    "command": "change_map",
    "parameters": {
        "direction": "e, n, w, or s"
    }
}
````