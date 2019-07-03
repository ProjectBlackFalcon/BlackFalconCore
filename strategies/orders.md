# Examples for orders

These are the messages exchanged between the commander and the low level API.

For the strategies, see the strategies.md in the swarm_manager folder.

### Connect
```json
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
```json
{
  "command": "disconnect",
  "parameters": {
      "name": "Mystinu"
  }
}
```

### Move
```json
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
```json
{
  "command": "change_map",
  "parameters": {
      "direction": "e, n, w, or s"
  }
}
```

### Enter havenbag
````json
{
  "command": "enter_havenbag"
}
````

### Exit havenbag
````json
{
  "command": "exit_havenbag"
}
````

### Use interactive
````json
{
  "command": "use_interactive",
  "parameters": {
    "element_id": 451616161,
    "skill_uid": 789624
  }
}
````

### Travel by zaap
````json
{
  "command": "travel_by_zaap",
  "parameters": {
    "target_map_id": 2153165165121
  }
}
````
TODO: fix parameters

### Open NPC
````json
{
  "command": "open_npc",
  "parameters": {
     "map_id": 166516844,
     "npc_id": 651946516
  }
}
````

### Close NPC
````json
{
  "command": "close_npc"
}
````

### Answer NPC
````json
{
  "command": "answer_npc",
  "parameters": {
    "reply_id": 11611
  }
}
````