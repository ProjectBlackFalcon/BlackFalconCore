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

### Check file message
```json
{
  "command": "check_file_message",
  "parameters": {
      "filenameHash": "1s6df51sd1fs1dfsd12f3s1df3s1",
      "type": 0,
      "value": "15sxdf42sd542xf1ds54f12dsf2"
  }
}
```

### Move
```json
{
  "command": "move",
  "parameters": {
      "isUsingNewMovementSystem": "Boolean (isUsingNewMovementSystem from map_info)",
      "cells": ["List of cells (rawCells from map_info)"],
      "target_cell": 548
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
      "direction": "e, n, w, or s",
      "target_map_id": 154654563
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
     "npc_id": 651946516,
     "action_id": 3
  }
}
````
actions_ids:
- 3: talk
- 5: swap auction house to sell mode
- 6: swap auction house to buy mode

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

### Single item to storage
````json
{
  "command": "inv_to_storage",
  "parameters": {
    "item_uid": 22850903,
    "quantity": 5
  }
}
````

### Single item from storage
````json
{
  "command": "storage_to_inv",
  "parameters": {
    "item_uid": 22850903,
    "quantity": 5
  }
}
````

### List of items to storage
````json
{
  "command": "inv_to_storage_list",
  "parameters": {
    "items_uids": [22850903, 22850904]
  }
}
````

### List of items from storage
````json
{
  "command": "storage_to_inv_list",
  "parameters": {
    "items_uids": [22850903, 22850904]
  }
}
````

### Move kamas
````json
{
  "command": "move_kamas",
  "parameters": {
    "quantity": 100000
  }
}
````
- Positive values means from inventory to storage
- Negative values means from storage to inventory


### Select category
````json
{
  "command": "auctionh_select_category",
  "parameters":{
    "category_id": 41
  }
}
````

### Select item
````json
{
  "command": "auctionh_select_item",
  "parameters":{
    "general_id": 1782
  }
}
````
Should send the `ExchangeBidHouseListMessage` AND the `ExchangeBidHousePriceMessage`

### Buy item
````json
{
  "command": "auctionh_buy_item",
  "parameters":{
    "unique_id": 43657,
    "quantity": 10,
    "price": 10000
  }
}
````
Should also send the `ExchangeBidHousePriceMessage`

### Sell item
````json
{
  "command": "auctionh_sell_item",
  "parameters":{
    "unique_id": 43657,
    "quantity": 10,
    "price": 10000
  }
}
````
Should also send the `ExchangeBidHousePriceMessage`

### Get Achievement reward
````json
{
  "command": "achievement_get",
  "parameters":{
    "actor_id": 544591118544
  }
}
````