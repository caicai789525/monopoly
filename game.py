from board import Board
from player import Player
from card import CardSystem

class Game:
    def __init__(self, num_players, initial_money):
        self.board = Board()
        self.players = [Player(f"玩家 {i + 1}", initial_money) for i in range(num_players)]
        self.card_system = CardSystem()
        self.current_player_index = 0
        self.game_over = False

    def get_current_player(self):
        return self.players[self.current_player_index]

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def roll_dice(self):
        import random
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        return dice1 + dice2, dice1 == dice2

    def handle_tile(self, player):
        tile = self.board.get_tile(player.position)
        if tile["type"] == "property":
            if tile["owner"] is None:
                return "可购买"
            elif tile["owner"] != player:
                rent = tile["rent"]
                player.pay(rent)
                tile["owner"].receive(rent)
                return f"支付租金 {rent} 元给 {tile['owner'].name}"
            elif tile["owner"] == player:
                return "可升级"
        elif tile["type"] == "chance":
            card_text = self.card_system.draw_chance_card(player)
            return f"抽到机会卡: {card_text}"
        elif tile["type"] == "community":
            card_text = self.card_system.draw_community_card(player)
            return f"抽到社区福利卡: {card_text}"
        elif tile["type"] == "tax":
            player.pay(tile["amount"])
            return f"支付税收 {tile['amount']} 元"
        elif tile["type"] == "go_to_jail":
            self.card_system.send_to_jail(player)
            return "前往监狱"
        return ""

    def check_bankruptcy(self):
        bankrupt_players = []
        for player in self.players:
            if player.is_bankrupt():
                bankrupt_players.append(player)
                for prop in player.properties:
                    prop["owner"] = None
        for player in bankrupt_players:
            self.players.remove(player)
        if len(self.players) == 1:
            self.game_over = True
            return self.players[0]
        return None


class Player:
    def __init__(self, name, initial_money):
        self.name = name
        self.money = initial_money
        self.position = 0
        self.properties = []
        self.in_jail = False
        self.jail_turns = 0

    def move(self, steps):
        self.position = (self.position + steps) % len(Board().tiles)

    def pay(self, amount):
        self.money -= amount

    def receive(self, amount):
        self.money += amount

    def is_bankrupt(self):
        return self.money < 0

    def buy_property(self, tile):
        if self.money >= tile["price"]:
            self.money -= tile["price"]
            self.properties.append(tile)
            tile["owner"] = self
            return True
        return False

    def upgrade_property(self, tile):
        if tile in self.properties and self.money >= tile["upgrade_price"]:
            self.money -= tile["upgrade_price"]
            tile["rent"] *= 2
            return True
        return False