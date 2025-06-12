import random
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
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        return dice1 + dice2, dice1 == dice2

    def handle_jail(self, player):
        """处理玩家在监狱中的状态"""
        if player.in_jail:
            if player.get_out_of_jail_free_cards > 0:
                player.get_out_of_jail_free_cards -= 1
                player.in_jail = False
                player.jail_turns = 0
                return f"{player.name} 使用出狱卡"
            elif player.jail_turns > 0:
                player.jail_turns -= 1
                if player.jail_turns == 0:
                    player.in_jail = False
                    player.pay(50)
                    return f"{player.name} 支付 50 元保释金出狱"
                return f"{player.name} 仍在监狱（剩余 {player.jail_turns} 回合）"
            return f"{player.name} 仍在监狱"
        return None

    def handle_tile(self, player):
        tile = self.board.get_tile(player.position)
        if tile["type"] == "start":
            player.receive(200)
            return f"{player.name} 获得 200 元"
        elif tile["type"] == "property":
            if tile["owner"] is None:
                return f"{player.name} 可购买 {tile['name']}"
            elif tile["owner"] != player:
                rent = tile["rent"]
                player.pay(rent)
                tile["owner"].receive(rent)
                return f"{player.name} 支付租金 {rent} 元给 {tile['owner'].name}"
            elif tile["owner"] == player:
                return f"{player.name} 可升级 {tile['name']}"
        elif tile["type"] == "chance":
            card_text = self.card_system.draw_chance_card(player, self)
            return f"{player.name} 抽到机会卡: {card_text}"
        elif tile["type"] == "community":
            card_text = self.card_system.draw_community_card(player, self)
            return f"{player.name} 抽到社区福利卡: {card_text}"
        elif tile["type"] == "tax":
            player.pay(tile["amount"])
            return f"{player.name} 支付税收 {tile['amount']} 元"
        elif tile["type"] == "go_to_jail":
            self.card_system.send_to_jail(player)
            return f"{player.name} 前往监狱"
        elif tile["type"] == "jail":
            return f"{player.name} 访问监狱"
        elif tile["type"] == "free_parking":
            return f"{player.name} 在自由停车"
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