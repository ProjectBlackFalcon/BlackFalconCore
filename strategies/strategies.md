# Examples for strategies

These are the messages exchanged from the Swarm Manager to the commander.

For the orders exchanged between the commander and the low level API, see the orders.md in the strategies folder.

### Login
````json
{
  "command": "login",
  "parameters": {
    "token": "d5s6f6ds5f4s654fds654f6s5q4df"
  }
}
````

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

### Go drop bank
````json
{
  "bot": "Mystinu",
  "command": "go_drop_bank",
  "parameters": {
    "return": {"pos": [0, 1], "cell": 456, "worldmap": 1},
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
`return` is optional and is the position the bot must go back to after dropping its inventory
if `return == 'current`, the bot will return to the position it's at before starting to go to the bank
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
`blacklist` and `whitelist` are optional can not be used at the same time in the same harvest strategy. Everything is whitelisted by default.
- `whitelist` only authorises the items listed to be harvested
- `blacklist` only authorises the items not listed to be harvested

### Harvest map
````json
{
  "bot": "Mystinu",
  "command": "harvest_map",
  "parameters": {
      "blacklist": [421],
      "whitelist": null
  }
}
````
`blacklist` and `whitelist` are optional can not be used at the same time in the same harvest strategy. Everything is whitelisted by default.
- `whitelist` only authorises the items listed to be harvested
- `blacklist` only authorises the items not listed to be harvested

### Harverst duration
````json
{
  "bot": "Mystinu",
  "command": "harvest_duration",
  "parameters": {
      "duration": 60,
      "path": [
        {"pos": [1, -3], "cell": 256, "worldmap": 2},
        {"pos": [1, -4]}
      ],
      "whitelist": [456],
      "blacklist": null
  }
}
````
`duration` is in minutes

`blacklist` and `whitelist` are optional can not be used at the same time in the same harvest strategy. Everything is whitelisted by default.
- `whitelist` only authorises the items listed to be harvested
- `blacklist` only authorises the items not listed to be harvested


### Open auction house
````json
{
  "bot": "Mystinu",
  "command": "auctionh_open",
  "parameters": {
    "mode": "buy"
  }
}
````
Modes can be `buy` or `sell`
Optional parameter, default is buy

### Close auction house
````json
{
  "bot": "Mystinu",
  "command": "auctionh_close"
}
````

### Get items prices
````json
{
  "bot": "Mystinu",
  "command": "auctionh_get_prices",
  "parameters": {
    "general_ids_list": [421, 1782]
  }
}
````

### Buy items
````json
{
  "bot": "Mystinu",
  "command": "auctionh_buy",
  "items": [
      {
        "unique_id": 154651616,
        "pack_size": 100,
        "quantity": 2
      }
  ]
}
````

### Sell items
````json
{
  "bot": "Mystinu",
  "command": "auctionh_sell",
  "items": [
      {
        "unique_id": 154651616,
        "pack_size": 100,
        "quantity": 2
      }
  ]
}
````