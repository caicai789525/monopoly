import pygame
from game import Game

# 初始化 Pygame
pygame.init()

# 设置窗口尺寸
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("大富翁游戏")

# 游戏设置
num_players = 2
initial_money = 1500
game = Game(num_players, initial_money)

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# 字体设置，使用 Windows 系统自带的黑体
font = pygame.font.SysFont("SimHei", 36)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not game.game_over:
                current_player = game.get_current_player()
                if not current_player.in_jail:
                    steps, is_double = game.roll_dice()
                    current_player.move(steps)
                    game.handle_tile(current_player)
                    winner = game.check_bankruptcy()
                    if winner:
                        game.game_over = True
                    else:
                        game.next_player()
                else:
                    if current_player.jail_turns > 0:
                        current_player.jail_turns -= 1
                        if is_double:
                            current_player.in_jail = False
                        else:
                            game.next_player()

    # 绘制界面
    screen.fill(WHITE)
    if not game.game_over:
        current_player = game.get_current_player()
        text = font.render(f"轮到 {current_player.name} 投掷骰子", True, BLACK)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    else:
        winner = game.players[0]
        text = font.render(f"{winner.name} 获胜！", True, BLACK)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))

    pygame.display.flip()

pygame.quit()
