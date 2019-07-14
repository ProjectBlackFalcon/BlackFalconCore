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