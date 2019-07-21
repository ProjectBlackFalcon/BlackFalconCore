# Examples for strategies

These are the messages exchanged from the Swarm Manager to the commander.

For the orders exchanged between the commander and the low level API, see the orders.md in the strategies folder.


### Add bot
````json
{
  "bot": "Mystinu",
  "command": "new_bot",
  "parameters": {
    "id": 1,
    "name": "Mystinu",
    "username": "blackfalcon0",
    "password": "...",
    "server": "Julith"
  }
  
}
````

### Delete bot
````json
{
  "bot": "Mystinu",
  "command": "delete_bot" 
}
````

### Get game state
````json
{
  "bot": "Mystinu",
  "command": "get_game_state" 
}
````

### Connect
```json
{
  "bot": "Mystinu",
  "command": "connect"
}
```

### Disconnect
````json
{
  "bot": "Mystinu",
  "command": "connect"
}
````

### Go to
````json
{
  "bot": "Mystinu",
  "command": "goto",
  "parameters": {
    "x": 4,
    "y": -18,
    "cell": 256,
    "worldmap": 1
  }
}
````

### Move
````json
{
  "bot": "Mystinu",
  "command": "move",
  "parameters": {
      "cell": 348
  }
}
````

### Change map
````json
{
  "bot": "Mystinu",
  "command": "change_map",
  "parameters": {
      "cell": 549,
      "direction": "e, n, w, or s"
  }
}
````

### Enter havenbag
````json
{
  "bot": "Mystinu",
  "command": "enter_havenbag"
}
````

### Exit havenbag
````json
{
  "bot": "Mystinu",
  "command": "exit_havenbag"
}
````

### Enter bwork
````json
{
  "bot": "Mystinu",
  "command": "enter_bwork"
}
````

### Exit bwork
````json
{
  "bot": "Mystinu",
  "command": "exit_bwork"
}
````

### Enter DD territory
````json
{
  "bot": "Mystinu",
  "command": "enter_dd_territory"
}
````

### Exit brak north
````json
{
  "bot": "Mystinu",
  "command": "exit_brak_north"
}
````

### Go to astrub
````json
{
  "bot": "Mystinu",
  "command": "go_to_astrub"
}
````

### Go to incarnam
````json
{
  "bot": "Mystinu",
  "command": "go_to_incarnam"
}
````

### Exit hunting hall
````json
{
  "bot": "Mystinu",
  "command": "exit_hunting_hall"
}
````

### Use Zaap
````json
{
  "bot": "Mystinu",
  "command": "use_zaap",
  "parameters": {
    "destination_x": 1,
    "destination_y": -32
  }
}
````

### Open bank
````json
{
  "bot": "Mystinu",
  "command": "bank_open"
}
````

### Close bank
````json
{
  "bot": "Mystinu",
  "command": "bank_close"
}
````

### Enter bank
````json
{
  "bot": "Mystinu",
  "command": "bank_enter"
}
````

### Exit bank
````json
{
  "bot": "Mystinu",
  "command": "bank_exit"
}
````

### Bank get kamas
````json
{
  "bot": "Mystinu",
  "command": "bank_get_kamas",
  "parameters": {
    "quantity": 1000
  }
}
````
If quantity is not specified, all is assumed.

### Bank put kamas
````json
{
  "bot": "Mystinu",
  "command": "bank_put_kamas",
  "parameters": {
    "quantity": 1000
  }
}
````
If quantity is not specified, all is assumed.

### Bank get items
````json
{
  "bot": "Mystinu",
  "command": "bank_get_items",
  "parameters": {
    "items": [
      {
        "general_id": 425,
        "quantity": 1000
      },
      {
        "general_id": 425
      } 
    ]
  }
}
````
if `items == 'all'`, all the items are moved
If quantity is not specified, all is assumed.

### Bank put items
````json
{
  "bot": "Mystinu",
  "command": "bank_put_items",
  "parameters": {
    "items": [
      {
        "general_id": 425,
        "quantity": 1000
      },
      {
        "general_id": 425
      } 
    ]
  }
}
````
if `items == 'all'`, all the items are moved
If quantity is not specified for an item, all is assumed.

### Harvest
````json
{
  "bot": "Mystinu",
  "command": "harvest",
  "parameters": {
      "cell": 199,
      "blacklist": [421],
      "whitelist": [456]
  }
}
````
`blacklist` and `whitelist` are optional can not be used at the same time in the same harvest strategy
- `whitelist` only authorises the items listed to be harvested
- `blacklist` only authorises the items not listed to be harvested

### Harvest map
````json
{
  "bot": "Mystinu",
  "command": "harvest_map",
  "parameters": {
      "blacklist": [421],
      "whitelist": [456]
  }
}
````
`blacklist` and `whitelist` are optional can not be used at the same time in the same harvest strategy
- `whitelist` only authorises the items listed to be harvested
- `blacklist` only authorises the items not listed to be harvested
