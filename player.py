from board import Board


class Player:
    def __init__(self, name, initial_money):
        self.name = name
        self.money = initial_money
        self.position = 0
        self.properties = []
        self.in_jail = False
        self.jail_turns = 0
        self.get_out_of_jail_free_cards = 0

    def move(self, steps):
        if not self.in_jail:
            if not hasattr(Board(), 'tiles'):
                print("Board 对象缺少 tiles 属性")
                return
            self.position = (self.position + steps) % len(Board().tiles)
            if self.position < 0:
                self.position += len(Board().tiles)

    def pay(self, amount):
        self.money -= amount

    def receive(self, amount):
        self.money += amount

    def is_bankrupt(self):
        return self.money < 0
