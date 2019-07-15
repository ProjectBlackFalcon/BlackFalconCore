import time

from tools import logger as log
import strategies


def goto(**kwargs):
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    target_x = strategy['parameters']['x']
    target_y = strategy['parameters']['y']
    target_cell = strategy['parameters']['cell']
    target_worldmap = strategy['parameters']['worldmap']

    logger = log.get_logger(__file__, strategy['bot'])

    path_maker = PathMaker(
        strategy=strategy,
        listener=listener,
        orders_queue=orders_queue,
        logger=logger,
        assets=assets,
        target_coord=(target_x, target_y),
        target_cell=target_cell,
        worldmap=target_worldmap,
    )
    strategy['report'] = path_maker.make_path()

    log.close_logger(logger)
    return strategy


class PathMaker:
    def __init__(self, strategy, listener, orders_queue, logger, assets, target_coord, target_cell=None, worldmap=1, harvest=False, forbid_zaaps=False):
        self.strategy = strategy
        self.listener = listener
        self.orders_queue = orders_queue
        self.logger = logger
        self.assets = assets
        self.target_coord = target_coord
        self.target_cell = target_cell
        self.target_worldmap = worldmap
        self.harvest = harvest
        self.forbid_zaaps = forbid_zaaps

    def make_path(self):
        return self.pathmaker(self.target_coord, self.target_cell, self.target_worldmap)

    def getmap(self):
        current_map = self.listener.game_state['pos']
        current_cell = self.listener.game_state['cell']
        current_worldmap = self.listener.game_state['worldmap']
        map_id = self.listener.game_state['map_id']
        return current_map, current_cell, current_worldmap, map_id

    def distance(self, pos1, pos2):
        return ((pos2[0] - pos1[0]) ** 2 + (pos2[1] - pos1[1]) ** 2) ** 0.5

    def pathmaker(self, target_coord, target_cell=None, worldmap=1, harvest=False, forbid_zaaps=False):
        start = time.time()
        current_map, current_cell, current_worldmap, map_id = self.getmap()

        if current_worldmap != worldmap:

            # Incarnam to Astrub
            if current_worldmap == 2 and worldmap == 1:
                self.pathmaker((4, -3), worldmap=2)
                report = strategies.go_to_astrub.go_to_astrub(
                    listener=self.listener,
                    orders_queue=self.orders_queue,
                    strategy={
                        'bot': self.strategy['bot'],
                    },
                    assets=self.assets
                )['report']
                if not report['success']:
                    self.logger.error('Failed to go to Astrub: {}'.format(report))
                    return {
                        'success': False,
                        'details': {'Execution time': time.time() - start, 'reason': 'Failed to go to Astrub: {}'.format(report)}
                    }
                current_map, current_cell, current_worldmap, map_id = self.getmap()

            # Astrub to Incarnam
            elif current_worldmap == 1 and worldmap == 2:
                gate_map = (6, -19)
                self.pathmaker(gate_map, target_cell=397)
                report = strategies.go_to_incarnam.go_to_incarnam(
                    listener=self.listener,
                    orders_queue=self.orders_queue,
                    strategy={
                        'bot': self.strategy['bot'],
                    },
                    assets=self.assets
                )['report']
                if not report['success']:
                    self.logger.error('Failed to go to Incarnam: {}'.format(report))
                    return {
                        'success': False,
                        'details': {'Execution time': time.time() - start, 'reason': 'Failed to go to Incarnam: {}'.format(report)}
                    }
                current_map, current_cell, current_worldmap, map_id = self.getmap()

            # Bot is in hunting hall
            elif list(current_map) == [-25, -36] and current_worldmap == -1:
                report = strategies.exit_hunting_hall.exit_hunting_hall(  # TODO: write strat for that
                    listener=self.listener,
                    orders_queue=self.orders_queue,
                    strategy={
                        'bot': self.strategy['bot'],
                    },
                    assets=self.assets
                )['report']
                if not report['success']:
                    self.logger.error('Failed to exit hunting hall: {}'.format(report))
                    return {
                        'success': False,
                        'details': {'Execution time': time.time() - start,
                                    'reason': 'Failed to exit hunting hall: {}'.format(report)}
                    }
                current_map, current_cell, current_worldmap, map_id = self.getmap()

            # Bot is in a building or underground
            elif current_worldmap == -1:
                closest_zaap = strategies.support_functions.get_closest_known_zaap(self.strategy['bot'], target_coord)
                if closest_zaap is not None:
                    report = strategies.enter_havenbag.enter_havenbag(
                        listener=self.listener,
                        strategy={'bot': self.strategy['bot']},
                        orders_queue=self.orders_queue,
                        assets=self.assets
                    )['report']

                    if report['success']:
                        report = strategies.use_zaap.use_zaap(
                            listener=self.listener,
                            orders_queue=self.orders_queue,
                            assets=self.assets,
                            strategy={
                                'bot': self.strategy['bot'],
                                'parameters': {
                                    'destination_x': closest_zaap[0],
                                    'destination_y': closest_zaap[1]
                                }
                            }
                        )['report']
                        current_map, current_cell, current_worldmap, map_id = self.getmap()
                        if not report['success']:
                            self.logger.error('Unable to use Zaap to go to {}. Reason: {}'.format(closest_zaap, report['details']))
                            return {
                                'success': False,
                                'details': {'Execution time': time.time() - start,
                                            'reason': 'Unable to use Zaap to go to {}'.format(closest_zaap)}
                            }
                    else:
                        self.logger.error('Failed to enter havenbag: {}'.format(report))
                        return {
                            'success': False,
                            'details': {'Execution time': time.time() - start,
                                        'reason': 'Failed to enter havenbag: {}'.format(report)}
                        }
                else:
                    self.logger.error('No known zaaps')
                    return {
                        'success': False,
                        'details': {'Execution time': time.time() - start,
                                    'reason': 'No known zaaps'}
                    }

            # TODO manage more worldmap changing
            else:
                self.logger.error('Worldmap change not supported')
                return {
                    'success': False,
                    'details': {'Execution time': time.time() - start,
                                'reason': 'Worldmap change not supported'}
                }

        closest_zaap = strategies.support_functions.get_closest_known_zaap(self.strategy['bot'], target_coord)
        if closest_zaap is not None and not forbid_zaaps:
            distance_zaap_target = self.distance(closest_zaap, target_coord)
            if worldmap == current_worldmap and self.distance(current_map, target_coord) > distance_zaap_target + 5:
                report = strategies.enter_havenbag.enter_havenbag(
                    listener=self.listener,
                    strategy={'bot': self.strategy['bot']},
                    orders_queue=self.orders_queue,
                    assets=self.assets
                )['report']

                if report['success']:
                    report = strategies.use_zaap.use_zaap(
                        listener=self.listener,
                        orders_queue=self.orders_queue,
                        assets=self.assets,
                        strategy={
                            'bot': self.strategy['bot'],
                            'parameters': {
                                'destination_x': closest_zaap[0],
                                'destination_y': closest_zaap[1]
                            }
                        }
                    )['report']
                    current_map, current_cell, current_worldmap, map_id = self.getmap()
                    if not report['success']:
                        self.logger.error('Unable to use Zaap to go to {}. Reason: {}'.format(closest_zaap, report['details']))
                        return {
                            'success': False,
                            'details': {'Execution time': time.time() - start,
                                        'reason': 'Unable to use Zaap to go to {}'.format(closest_zaap)}
                        }
                else:
                    # If unable to enter havenbag, than just walk to the closest zaap and use this one
                    closest_zaap_2 = strategies.support_functions.get_closest_known_zaap(self.strategy['bot'], current_map)
                    self.pathmaker(closest_zaap_2, forbid_zaaps=True)
                    if closest_zaap != closest_zaap_2:
                        report = strategies.use_zaap.use_zaap(
                            listener=self.listener,
                            orders_queue=self.orders_queue,
                            assets=self.assets,
                            strategy={
                                'bot': self.strategy['bot'],
                                'parameters': {
                                    'destination_x': closest_zaap[0],
                                    'destination_y': closest_zaap[1]
                                }
                            }
                        )['report']
                        if not report['success']:
                            self.logger.error('Unable to use Zaap to go to {}. Reason: {}'.format(closest_zaap, report['details']))
                            return {
                                'success': False,
                                'details': {'Execution time': time.time() - start,
                                            'reason': 'Unable to use Zaap to go to {}'.format(closest_zaap)}
                            }
                    current_map, current_cell, current_worldmap, map_id = self.getmap()

        if list(current_map) not in self.assets['BrakMaps'] and list(target_coord) in self.assets['BrakMaps']:
            # Bot needs to enter brak
            disc_zaaps = strategies.support_functions.get_known_zaaps(self.strategy['bot'])
            if [-26, 35] in disc_zaaps:
                success = strategies.enter_havenbag.enter_havenbag(
                    listener=self.listener,
                    strategy={'bot': self.strategy['bot']},
                    orders_queue=self.orders_queue,
                    assets=self.assets
                )['report']['success']

                if success:
                    report = strategies.use_zaap.use_zaap(
                        listener=self.listener,
                        orders_queue=self.orders_queue,
                        assets=self.assets,
                        strategy={
                            'bot': self.strategy['bot'],
                            'parameters': {
                                'destination_x': -26,
                                'destination_y': 35
                            }
                        }
                    )['report']
                    if not report['success']:
                        self.logger.error('Unable to use Zaap to go to {}. Reason: {}'.format((-26, 35), report['details']))
                        return {
                            'success': False,
                            'details': {'Execution time': time.time() - start,
                                        'reason': 'Unable to use Zaap to go to {}'.format((-26, 35))}
                        }
                current_map, current_cell, current_worldmap, map_id = self.getmap()

        if list(current_map) in self.assets['BrakMaps'] and list(target_coord) not in self.assets['BrakMaps']:
            # Bot needs to exit brak
            if list(target_coord) in self.assets['BrakMaps']:
                self.pathmaker((-20, 34))
                report = strategies.change_map.change_map(
                    listener=self.listener,
                    orders_queue=self.orders_queue,
                    assets=self.assets,
                    strategy={
                        'bot': self.strategy['bot'],
                        'parameters': {'cell': 307, 'direction': 'e'}
                    }
                )['report']
                if not report['success']:
                    self.logger.error('Failed to exit brak: {}'.format(report))
                    return {
                        'success': False,
                        'details': {'Execution time': time.time() - start,
                                    'reason': 'Failed to exit brak: {}'.format(report)}
                    }
            elif list(target_coord) in self.assets['BrakNorth']:
                self.pathmaker((-26, 31))
                report = strategies.exit_brak_north.exit_brak_north(
                    listener=self.listener,
                    orders_queue=self.orders_queue,
                    assets=self.assets,
                    strategy={'bot': self.strategy['bot']}
                )['report']
                if not report['success']:
                    self.logger.error('Failed to exit exit brak to north: {}'.format(report))
                    return {
                        'success': False,
                        'details': {'Execution time': time.time() - start,
                                    'reason': 'Failed to exit exit brak to north: {}'.format(report)}
                    }
            current_map, current_cell, current_worldmap, map_id = self.getmap()

        if list(current_map) in self.assets['WestDDTerr'] and list(target_coord) in self.assets['DDTerr']:
            # Bot needs to enter dd territory from west
            self.pathmaker((-23, -1), target_cell=387)
            report = strategies.enter_dd_territory.enter_dd_territory(
                listener=self.listener,
                orders_queue=self.orders_queue,
                assets=self.assets,
                strategy={'bot': self.strategy['bot']}
            )['report']
            if not report['success']:
                self.logger.error('Failed to enter DD territory: {}'.format(report))
                return {
                    'success': False,
                    'details': {'Execution time': time.time() - start,
                                'reason': 'Failed to enter DD territory: {}'.format(report)}
                }
            current_map, current_cell, current_worldmap, map_id = self.getmap()
        if list(current_map) in self.assets['DDTerr'] and list(target_coord) in self.assets['WestDDTerr']:
            # Bot needs to exit dd territory to the west
            self.pathmaker((-22, -1))
            report = strategies.change_map.change_map(
                listener=self.listener,
                orders_queue=self.orders_queue,
                assets=self.assets,
                strategy={
                    'bot': self.strategy['bot'],
                    'parameters': {'cell': 294, 'direction': 'w'}
                }
            )['report']
            if not report['success']:
                self.logger.error('Failed to exit DD territory: {}'.format(report))
                return {
                    'success': False,
                    'details': {'Execution time': time.time() - start,
                                'reason': 'Failed to exit DD territory: {}'.format(report)}
                }
            current_map, current_cell, current_worldmap, map_id = self.getmap()

        if list(current_map) not in self.assets['CastleAmakna'] and list(target_coord) in self.assets['CastleAmakna']:
            # Bot needs to enter the castle
            disc_zaaps = strategies.support_functions.get_known_zaaps(self.strategy['bot'])
            if [3, -5] in disc_zaaps:
                report = strategies.enter_havenbag.enter_havenbag(
                    listener=self.listener,
                    strategy={'bot': self.strategy['bot']},
                    orders_queue=self.orders_queue,
                    assets=self.assets
                )['report']

                if report['success']:
                    report = strategies.use_zaap.use_zaap(
                        listener=self.listener,
                        orders_queue=self.orders_queue,
                        assets=self.assets,
                        strategy={
                            'bot': self.strategy['bot'],
                            'parameters': {
                                'destination_x': 3,
                                'destination_y': -5
                            }
                        }
                    )['report']
                    if not report['success']:
                        self.logger.error(
                            'Unable to use Zaap to go to {}. Reason: {}'.format((-26, 35), report['details']))
                        return {
                            'success': False,
                            'details': {'Execution time': time.time() - start,
                                        'reason': 'Unable to use Zaap to go to {}'.format((-26, 35))}
                        }
                else:
                    self.logger.error('Failed to enter havenbag: {}'.format(report))
                    return {
                        'success': False,
                        'details': {'Execution time': time.time() - start,
                                    'reason': 'Failed to enter havenbag: {}'.format(report)}
                    }
                current_map, current_cell, current_worldmap, map_id = self.getmap()
            # else:
            #     self.pathmaker((3, -5), forbid_zaaps=True)
        if list(current_map) in self.assets['CastleAmakna'] and list(target_coord) not in self.assets['CastleAmakna']:
            # Bot needs to exit the castle through the northern gate
            if target_coord[1] <= current_map[1]:
                self.pathmaker((4, -8))
                report = strategies.change_map.change_map(
                    listener=self.listener,
                    orders_queue=self.orders_queue,
                    assets=self.assets,
                    strategy={
                        'bot': self.strategy['bot'],
                        'command': 'change_map',
                        'parameters': {'cell': 140, 'direction': 'w'}
                    }
                )['report']
                if not report['success']:
                    self.logger.error('Failed to exit castle: {}'.format(report))
                    return {
                        'success': False,
                        'details': {'Execution time': time.time() - start,
                                    'reason': 'Failed to exit castle: {}'.format(report)}
                    }
                current_map, current_cell, current_worldmap, map_id = self.getmap()

        if list(current_map) not in self.assets['BworkMaps'] and list(target_coord) in self.assets['BworkMaps']:
            # Bot needs to enter bwork village
            self.pathmaker((-1, 8), target_cell=383)
            report = strategies.enter_bwork.enter_bwork(
                listener=self.listener,
                orders_queue=self.orders_queue,
                assets=self.assets,
                strategy={
                    'bot': self.strategy['bot'],
                    'command': 'enter_bwork'
                }
            )['report']
            if not report['success']:
                self.logger.error('Failed to enter bwork: {}'.format(report))
                return {
                    'success': False,
                    'details': {'Execution time': time.time() - start,
                                'reason': 'Failed to enter bwork: {}'.format(report)}
                }

            current_map, current_cell, current_worldmap, map_id = self.getmap()
        if list(current_map) in self.assets['BworkMaps'] and list(target_coord) not in self.assets['BworkMaps']:
            # Bot needs to exit bwork village
            self.pathmaker((-2, 8), target_cell=260)
            report = strategies.exit_bwork.exit_bwork(
                listener=self.listener,
                orders_queue=self.orders_queue,
                assets=self.assets,
                strategy={
                    'bot': self.strategy['bot'],
                    'command': 'exit_bwork'
                }
            )['report']
            if not report['success']:
                self.logger.error('Failed to exit bwork: {}'.format(report))
                return {
                    'success': False,
                    'details': {'Execution time': time.time() - start,
                                'reason': 'Failed to exit bwork: {}'.format(report)}
                }
            current_map, current_cell, current_worldmap, map_id = self.getmap()

        if current_map == target_coord and current_cell == target_cell and worldmap == current_worldmap:
            return {
                'success': True,
                'details': {'Execution time': time.time() - start}
            }

        if current_map == target_coord and worldmap == current_worldmap and target_cell is not None:
            success = strategies.move.move(
                strategy={
                    'bot': self.strategy['bot'],
                    'command': 'move',
                    'parameters': {'cell': target_cell}
                },
                listener=self.listener,
                orders_queue=self.orders_queue,
                assets=self.assets
            )['report']['success']
            if success:
                return {
                    'success': True,
                    'details': {'Execution time': time.time() - start}
                }

        path = strategies.support_functions.get_path(self.assets['map_info'], self.assets['pathfinder_graph'], current_map, target_coord, current_cell, target_cell, worldmap)
        for map_change in path:
            report = strategies.change_map.change_map(
                listener=self.listener,
                orders_queue=self.orders_queue,
                assets=self.assets,
                strategy={
                    'command': 'change_map',
                    'bot': self.strategy['bot'],
                    'parameters': {
                        'cell': map_change['cell'],
                        'direction': map_change['direction']
                    }
                }
            )['report']
            if not report['success']:
                self.logger.error('Issue during change map: {}'.format(report))
                return {
                    'success': False,
                    'details': {'Execution time': time.time() - start,
                                'reason': 'Issue during change map: {}'.format(report)}
                }

            current_map, current_cell, current_worldmap, map_id = self.getmap()
            if current_worldmap == 1 and current_map in self.assets['zaapList']:
                strategies.support_functions.add_known_zaap(self.strategy['bot'], current_map)

            # TODO: Add harvest here
        #
        # if tuple(current_map) != tuple(target_coord):
        #     self.goto(target_coord, target_cell, worldmap)

        if target_cell is not None:
            report = strategies.move.move(
                strategy={
                    'bot': self.strategy['bot'],
                    'command': 'move',
                    'parameters': {'cell': target_cell}
                },
                listener=self.listener,
                orders_queue=self.orders_queue,
                assets=self.assets
            )['report']
            if not report['success']:
                self.logger.error('Issue during final move: {}'.format(report))
                return {
                    'success': False,
                    'details': {'Execution time': time.time() - start,
                                'reason': 'Issue during final move: {}'.format(report)}
                }
        return {
            'success': True,
            'details': {'Execution time': time.time() - start}
        }