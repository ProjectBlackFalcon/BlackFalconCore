# Examples for orders

These are the messages exchanged between the commander and the low level API.

For the strategies, see the strategies.md in the swarm_manager folder.

### Connect
```json5
{
    "command": "connect",
    "parameters": {
        "name": "Mystinu", 
        "username": "blackfalcon0", 
        "password": "...", 
        "serverId": 208
    }
}
```

### Disconnect
```json5
{
    "command": "disconnect",
    "parameters": {
        "name": "Mystinu"
    }
}
```

### Move
```json5
{
    "command": "move",
    "parameters": {
        "isUsingNewMovementSystem": "Boolean (isUsingNewMovementSystem from map_info)",
        "cells": ["List of cells (rawCells from map_info)"]
    }
}
```
Each cell is a list of bools/ints in the following order: 
- mov (bool)
- nonWalkableDuringFight (bool)
- floor (int)
- movZone (int)
- los (bool)
- speed (int)

### Change map
```json5
{
    "command": "change_map",
    "parameters": {
        "direction": "e, n, w, or s"
    }
}
```