import random

class CardSystem:
    def __init__(self):
        self.chance_cards = [
            {"text": "获得 100 元", "action": lambda player: player.receive(100)},
            {"text": "移动到起点", "action": lambda player: setattr(player, "position", 0)},
            {"text": "进监狱", "action": lambda player: self.send_to_jail(player)},
            {"text": "向前移动 3 步", "action": lambda player: player.move(3)},
            {"text": "后退 2 步", "action": lambda player: player.move(-2)}
        ]
        self.community_cards = [
            {"text": "支付 50 元税款", "action": lambda player: player.pay(50)},
            {"text": "获得 80 元奖金", "action": lambda player: player.receive(80)},
            {"text": "移动 3 步", "action": lambda player: player.move(3)},
            {"text": "所有玩家支付你 20 元", "action": self.all_players_pay},
            {"text": "支付所有玩家 10 元", "action": self.pay_all_players}
        ]

    def draw_chance_card(self, player, game):
        card = random.choice(self.chance_cards)
        if card["text"] == "所有玩家支付你 20 元" or card["text"] == "支付所有玩家 10 元":
            card["action"](player, game)
        else:
            card["action"](player)
        return card["text"]

    def draw_community_card(self, player, game):
        card = random.choice(self.community_cards)
        if card["text"] == "所有玩家支付你 20 元" or card["text"] == "支付所有玩家 10 元":
            card["action"](player, game)
        else:
            card["action"](player)
        return card["text"]

    def send_to_jail(self, player):
        player.in_jail = True
        player.jail_turns = 3
        player.position = 8

    def all_players_pay(self, player, game):
        for p in game.players:
            if p != player:
                p.pay(20)
                player.receive(20)

    def pay_all_players(self, player, game):
        for p in game.players:
            if p != player:
                player.pay(10)
                p.receive(10)