# Examples for strategies

These are the messages exchanged from the Swarm Manager to the commander.

For the orders exchanged between the commander and the low level API, see the orders.md in the strategies folder.

### Connect
````json
{
    "bot": "Mystinu",
    "command": "connect"
}
````

### Disconnect
````json
{
    "bot": "Mystinu",
    "command": "connect"
}
````

### Move
````json
{
    "bot": "Mystinu",
    "command": "move",
    "parameters": {
        "cell": "target cell id, between 0 and 560"
    }
}
````

### Change map
````json
{
    "bot": "Mystinu",
    "command": "change_map",
    "parameters": {
        "cell": "target cell id, between 0 and 560",
        "direction": "e, n, w, or s"
    }
}
````