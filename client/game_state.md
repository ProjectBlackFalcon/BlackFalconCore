# Specification for the game_state maintained by the listener

````json
{
    "name": "Mystinu",
    "id": 1,
    "actor_id": 1542684254,
    "username": "blackfalcon0",
    "password": "...",
    "server": "Julith",
    "level": 69,
    "pos": [0, 0],
    "cell": 420,
    "worldmap": 1,
    "map_id" : 21654232,
    "kamas": 1000000,
    "weight": 122,
    "max_weight": 2000,
    "inventory": [],
    "in_haven_bag": false,
    "npc_dialog_open": false,
    "npc_current_question": [],
    "npc_possible_replies": [],
    "zaap_dialog_open": false,
    "zaap_destinations": [ 
         { 
            "type":0,
            "mapId":191105026.0,
            "subAreaId":95,
            "level":10,
            "cost":0
         },
         { 
            "type":0,
            "mapId":120062979.0,
            "subAreaId":30,
            "level":20,
            "cost":140
         }
    ],
    "currently_walking": false,
    "map_mobs": [
        {
            "contextualId":-20004.0,
            "disposition":{ 
               "cellId":542,
               "direction":7
            },
            "staticInfos":{ 
                "mainCreatureLightInfos":{ 
                  "genericId":493,
                  "grade":4,
                  "level":14
                },
                "underlings":[ 
                    { 
                        "genericId":492,
                        "grade":2,
                        "level":12
                    }
                ]
            }
        }
    ],
    "map_npc": [
        {
            "contextualId":-20000.0,
            "disposition":{ 
               "cellId":286,
               "direction":3
            },
            "npcId":1088
        }
    ],
    "map_players": [],
    "map_elements": [
        {  
            "elementId":516111,
            "elementTypeId":316,
            "enabledSkills":[
                {  
                    "skillId":360,
                    "skillInstanceUid":91092864
                }
            ],
            "disabledSkills":[],
            "onCurrentMap": true
        }
    ],
    "stated_elements": [
        { 
            "elementId":489497,
            "elementCellId":172,
            "elementState":1,
            "onCurrentMap":true
        }
    ],
    "storage_open": false,
    "storage_content": [],
    "jobs": {  
        "26": {
            "jobId": 26,
            "jobLevel":1,
            "jobXP":10,
            "jobXpLevelFloor":0,
            "jobXpNextLevelFloor":20,
            "skills": [
                {  
                  "skillId":300,
                  "time":30,
                  "min":1,
                  "max":1
                }
            ]
        }
    }
}
````