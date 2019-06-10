import json
import numpy as np
from heapq import *
import time
import itertools
import sys

import pymongo

from credentials import credentials


def cell2coord(cell):
    return cell % 14 + int((cell // 14) / 2 + 0.5), (13 - cell % 14 + int((cell // 14) / 2))


def dist(coord_1, coord_2):
    return ((coord_2[0] - coord_1[0]) ** 2 + (coord_2[1] - coord_1[1]) ** 2) ** 0.5


def distance_cell(cell_1, cell_2):
    return dist(cell2coord(cell_1), cell2coord(cell_2))


def coord_fetch_map(map_info, coord, worldmap):
    maps = []
    for map in map_info:
        if map['coord'] == coord and map['worldMap'] == worldmap:
            maps.append(map)
    if len(maps) == 1 and maps[0] is not None:
        return maps[0]['cells']
    elif len(maps) > 1:
        for map in maps:
            if map['hasPriorityOnWorldMap']:
                return map['cells']


def flatten_map(map):
    flattened = []
    for line in map:
        flattened += line
    return flattened


def get_neighbour_cells(cell):
    neighbours = []
    for i in range(560):
        if distance_cell(cell, i) == 1:
            neighbours.append(i)
    return neighbours[:]


def get_walkable_neighbour_cells(map_info, cell, map_coords, worldmap):
    walkable_neighbours = []
    for neighbour in get_neighbour_cells(cell):
        if flatten_map(coord_fetch_map(map_info, '{};{}'.format(map_coords[0], map_coords[1]), worldmap))[neighbour] == 0:
            walkable_neighbours.append(neighbour)
    return walkable_neighbours[:]


def get_closest_walkable_neighbour_cell(map_info, target_cell, player_cell, map_coords, worldmap):
    walkable_neighbours = get_walkable_neighbour_cells(map_info, target_cell, map_coords, worldmap)
    if walkable_neighbours:
        closest = walkable_neighbours[0], 10000
    else:
        return False
    for walkable_neighbour in walkable_neighbours:
        if distance_cell(walkable_neighbour, player_cell) < closest[1]:
            closest = walkable_neighbour, distance_cell(walkable_neighbour, player_cell)

    if closest[1] < 10000:
        return closest[0]
    return False


def mongo_client():
    return pymongo.MongoClient(
        host=credentials['mongo']['host'],
        port=credentials['mongo']['port'],
        username=credentials['mongo']['username'],
        password=credentials['mongo']['password']
    )


def get_profile(bot, assets):
    client = mongo_client()

    profile = client.blackfalcon.bots.find_one({'name': bot['name']})
    if profile is None:
        profile = json.loads(json.dumps(assets['blank_bot_profile']))
        profile['name'] = bot['name']
        profile['username'] = bot['username']
        profile['password'] = bot['password']
        profile['server'] = bot['server']
        client.blackfalcon.bots.insert_one(profile)
    return profile


def update_profile(bot_name, new_profile):
    client = mongo_client()
    client.blackfalcon.bots.find_one_and_replace({'name': bot_name}, new_profile)


def get_known_zaaps(bot_name):
    client = mongo_client()
    return client.blackfalcon.bots.find_one({'name': bot_name})['known_zaaps']


def get_closest_known_zaap(bot_name, pos):
    known_zaaps = get_known_zaaps(bot_name)
    closest = None, 100000
    for zaap_pos in known_zaaps:
        if dist(pos, zaap_pos) < closest[1]:
            closest = zaap_pos, dist(pos, zaap_pos)
    return tuple(closest[0]) if closest is not None else None

def heuristic(node1, node2):
    coords_1 = [int(coord) for coord in node1['coord'].split(';')]
    coords_2 = [int(coord) for coord in node2['coord'].split(';')]
    return dist(coords_1, coords_2)

def get_path_nodes(graph, start_node_id, end_node_id):
    close_set = set()
    came_from = {}
    gscore = {start_node_id: 0}
    fscore = {start_node_id: heuristic(graph[start_node_id], graph[end_node_id])}
    oheap = []

    heappush(oheap, (fscore[start_node_id], start_node_id))

    while oheap:

        current = heappop(oheap)[1]

        if current == end_node_id:
            data = []
            while current in came_from:
                data.append(current)
                current = came_from[current]
            path = []
            coords = ''
            for node_id in data:
                if graph[node_id]['coord'] != coords:
                    path.append({'coord': graph[node_id]['coord'], 'cell': graph[node_id]['cell'],
                                 'direction': graph[node_id]['direction']})
                    coords = graph[node_id]['coord']
            return list(reversed(path))

        close_set.add(current)
        neighbours = graph[current]['neighbours']
        for neighbour in neighbours:
            tentative_g_score = gscore[current] + heuristic(graph[current], graph[neighbour])

            if neighbour in close_set and tentative_g_score >= gscore.get(neighbour, 0):
                continue

            if tentative_g_score < gscore.get(neighbour, 0) or neighbour not in [i[1] for i in oheap]:
                came_from[neighbour] = current
                gscore[neighbour] = tentative_g_score
                fscore[neighbour] = tentative_g_score + heuristic(graph[neighbour], graph[end_node_id])
                heappush(oheap, (fscore[neighbour], neighbour))

    return False

def fetch_map(map_info, coord, worldmap):
    maps = []
    for map in map_info:
        if map['coord'] == coord and map['worldMap'] == worldmap:
            maps.append(map)
    if len(maps) == 1 and maps[0] is not None:
        return maps[0]
    elif len(maps) > 1:
        for map in maps:
            if map['hasPriorityOnWorldMap']:
                return map

def cells_2_map(cells):
    maps = np.array(cells)
    shape = maps.shape
    flattened = maps.flatten()
    new_base = np.zeros((14 * shape[1] // 14 + 20 * shape[0] // 40 - 1, 14 * shape[1] // 14 + 20 * shape[0] // 40))
    new_base[new_base == 0] = -1
    for i in range(len(flattened)):
        coord = i % shape[1] + int((i // shape[1]) / 2 + 0.5), (shape[1] - 1 - i % shape[1] + int((i // shape[1]) / 2))
        new_base[coord[1]][coord[0]] = flattened[i]
    return new_base[:]

def cell_2_coord(cell):
    return (14 - 1 - cell % 14 + int((cell // 14) / 2)), cell % 14 + int((cell // 14) / 2 + 0.5)

def can_walk_to_node(map, cell, node):
    start_pos = cell_2_coord(cell)
    goal_pos = cell_2_coord(node['cell'])

    neighbors = [(1, 1), (-1, -1), (1, -1), (-1, 1), (1, 0), (0, 1), (-1, 0), (0, -1)]

    close_set = set()
    came_from = {}
    gscore = {start_pos: 0}
    fscore = {start_pos: (goal_pos[0] - start_pos[0]) ** 2 + (goal_pos[1] - start_pos[1]) ** 2}
    oheap = []

    heappush(oheap, (fscore[start_pos], start_pos))

    while oheap:

        current = heappop(oheap)[1]

        if current == goal_pos:
            data = []
            while current in came_from:
                data.append(current)
                current = came_from[current]
            return True

        close_set.add(current)
        for i, j in neighbors:
            neighbor = current[0] + i, current[1] + j
            tentative_g_score = gscore[current] + (neighbor[0] - current[0]) ** 2 + (neighbor[1] - current[1]) ** 2
            if 0 <= neighbor[0] < map.shape[0]:
                if 0 <= neighbor[1] < map.shape[1]:
                    if map[neighbor[0]][neighbor[1]] in  [1, 2]:
                        continue
                else:
                    # array bound y walls
                    continue
            else:
                # array bound x walls
                continue

            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                continue

            if tentative_g_score < gscore.get(neighbor, 0) or neighbor not in [i[1] for i in oheap]:
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score
                fscore[neighbor] = tentative_g_score + (goal_pos[0] - neighbor[0]) ** 2 + (goal_pos[1] - neighbor[1]) ** 2
                heappush(oheap, (fscore[neighbor], neighbor))

    return False


def get_path(map_info, graph, start_pos: tuple, start_cell, end_pos: tuple, end_cell, worldmap):
    start = time.time()
    potential_start_nodes_ids = []
    potential_end_nodes_ids = []
    for key, node in graph.items():
        if node['coord'] == '{};{}'.format(start_pos[0], start_pos[1]):
            cells = fetch_map(map_info, node['coord'], worldmap)['cells']
            if can_walk_to_node(cells_2_map(cells), start_cell, node):
                potential_start_nodes_ids.append(key)
        if node['coord'] == '{};{}'.format(end_pos[0], end_pos[1]):
            cells = fetch_map(map_info, node['coord'], worldmap)['cells']
            if can_walk_to_node(cells_2_map(cells), end_cell, node):
                potential_end_nodes_ids.append(key)

    couples = list(itertools.product(potential_start_nodes_ids, potential_end_nodes_ids))
    best_path, length = None, sys.maxsize
    for couple in couples:
        path = get_path_nodes(graph, couple[0], couple[1])
        if path and len(path) < length:
            best_path = path
            length = len(path)
    print(best_path[:-1], length, time.time() - start)
    return best_path
