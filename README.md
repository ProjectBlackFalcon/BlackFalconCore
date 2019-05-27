# BlackFalconCore

### The core of the black falcon bot project.

This repository is the central intelligence of the bot swarm. 

It's role is to schedule and run the bots, handle intelligence bricks, manage configurations, handle data streams and batches, and provide a high level REST API to interact with the swarm.

## The architecture

### Architecture goals
 - We should be able to distribute bots on multiple hosts
 - Bots should be able to interact with each other in game
 - Each bot should be as slim as possible in terms of performance footprint (RAM, CPU)
 - Limit the complexity of the architecture as much as possible

![lel](https://trello-attachments.s3.amazonaws.com/5ce57f181041ba0b5ae4c693/5ce962d91c07d78f9cb266b7/80fac944fa2a6132451858f407883080/Archi.drawio.svg)


### Swarm API 
Provides a single language agnostic acces point to the swarm. This will typically be used to issue high level commands or fetch data about the swarm.

Querying is going to be REST or GraphQL

### Swarm manager
The swarm manager is responsible for managing the bots. It does all the descision making for the swarm but will offload computation heavy stuff to the Swarm nodes. It is also going to act as a load balancer / reverse proxy.

### Swarm node
Each node is localized on a physical host and it's responsibility is to forward orders coming from the swarm manager to the appropriate bot. It may eventually offload the swarm manager of some processing (e.g. pathfinding). The common assets for all the bots are also loaded there at the host level. It means these are common for all the bot instances on this node, which greatly reduces the memory footprint, allowing us to run more bots on the same machine.

This is going to be as slim as possible, essentially only forwarding messages with the exception of when the order requires processing power.

It exposes an API using JSON over websocket to provide a high level entry point to use the bots.

### Intelligence bricks
These are going to be modules which implement bot behaviour. For example, the `core` brick will implement movements, connection / disconnection, interactions with activables and NPC. The `harvester` brick will implement all the logic for harvesting resources and will depend on the `core` brick.

### Static assets
Read only assets which only need to be loaded once. This includes maps, items, etc.

### Dynamic assets
Assets that may be updated by a bot as it does its thing. This includes bot information, treasure hunt clues, known paths, etc.

### Clients 
The websocket clients. Very slim.

### Bot API
Uses JSON over websocket. This is the translator between the game and the rest of the code. It parses the data packets from the game to JSON and vice-versa.

### Bot
The actual bot in-game.
