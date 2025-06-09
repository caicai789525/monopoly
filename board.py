import json

class Board:
    def __init__(self):
        with open('map_data.json', 'r', encoding='utf-8') as f:
            map_data = json.load(f)
        self.tiles = map_data['tiles']

    def get_tile(self, position):
        return self.tiles[position % len(self.tiles)]