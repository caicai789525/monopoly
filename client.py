import pygame
import socket
import threading
from game import Game
from board import Board

# 初始化 Pygame
pygame.init()

# 设置窗口尺寸
WIDTH, HEIGHT = 1200, 1200
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("大富翁游戏")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
LIGHT_GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)

# 字体设置
font = pygame.font.SysFont("SimHei", 20)

# 连接服务器
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5555))

# 游戏设置
num_players = 2
initial_money = 1500
game = None
room_id = None
password = ""
current_input = ""
input_rect = None
input_type = None
input_active = False
waiting_for_game = False
created_room_id = None

# 按钮设置，将按钮移到中间
button_width = 200
button_height = 50
button_x = (WIDTH - button_width) // 2
roll_button = pygame.Rect(button_x, HEIGHT - 200, button_width, button_height)
buy_button = pygame.Rect(button_x, HEIGHT - 270, button_width, button_height)
upgrade_button = pygame.Rect(button_x, HEIGHT - 340, button_width, button_height)

# 玩家颜色
player_colors = [RED, BLUE, GREEN, YELLOW]

# 投掷动画相关
rolling = False
roll_animation_frames = 20
roll_animation_count = 0

# 操作日志列表
action_logs = []


def receive_messages():
    global game, num_players, room_id, waiting_for_game, created_room_id
    while True:
        try:
            data = client.recv(1024).decode('utf-8')
            if not data:
                break
            parts = data.split('|')
            command = parts[0]
            if command == 'ROOM_CREATED':
                created_room_id = int(parts[1])
                print(f"房间创建成功，房间号: {created_room_id}")
                waiting_for_game = True
            elif command == 'ROOM_JOINED':
                print("成功加入房间")
                waiting_for_game = True
            elif command == 'ROOM_FULL_OR_NOT_EXIST':
                print("房间已满或不存在")
                waiting_for_game = False
            elif command == 'GAME_START':
                game = Game(num_players, initial_money)
                print("游戏开始")
                waiting_for_game = False
        except Exception as e:
            print(f"Error receiving messages: {e}")
            break


receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()


def main_menu():
    global num_players, current_input, input_rect, input_type, input_active, waiting_for_game, created_room_id, password
    create_room_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50)
    join_room_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 50)
    num_players_input = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 - 120, 100, 50)
    num_players_text = ""
    room_id_input = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 + 90, 100, 50)
    room_id_text = ""
    password_input = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 + 160, 100, 50)
    password_text = ""

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if create_room_button.collidepoint(event.pos):
                    try:
                        num_players = int(num_players_text)
                        client.sendall(f"CREATE_ROOM|{num_players}|{password_text}".encode('utf-8'))
                    except ValueError:
                        print("请输入有效的玩家数")
                elif join_room_button.collidepoint(event.pos):
                    try:
                        room_id = int(room_id_text)
                        client.sendall(f"JOIN_ROOM|{room_id}|{password_text}".encode('utf-8'))
                    except ValueError:
                        print("请输入有效的房间号")
                elif num_players_input.collidepoint(event.pos):
                    input_type = "num_players"
                    input_rect = num_players_input
                    current_input = num_players_text
                    input_active = True
                elif room_id_input.collidepoint(event.pos):
                    input_type = "room_id"
                    input_rect = room_id_input
                    current_input = room_id_text
                    input_active = True
                elif password_input.collidepoint(event.pos):
                    input_type = "password"
                    input_rect = password_input
                    current_input = password_text
                    input_active = True
                else:
                    input_active = False
            elif event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_BACKSPACE:
                        current_input = current_input[:-1]
                    elif event.unicode:
                        if input_type in ["num_players", "room_id"]:
                            if event.unicode.isdigit():
                                current_input += event.unicode
                        else:
                            current_input += event.unicode

                    if input_type == "num_players":
                        num_players_text = current_input
                    elif input_type == "room_id":
                        room_id_text = current_input
                    elif input_type == "password":
                        password_text = current_input

        screen.fill(WHITE)

        # 绘制按钮
        pygame.draw.rect(screen, BLUE, create_room_button)
        pygame.draw.rect(screen, BLUE, join_room_button)

        # 绘制输入框
        pygame.draw.rect(screen, LIGHT_GRAY if input_active and input_rect == num_players_input else WHITE,
                         num_players_input, 2)
        pygame.draw.rect(screen, LIGHT_GRAY if input_active and input_rect == room_id_input else WHITE, room_id_input, 2)
        pygame.draw.rect(screen, LIGHT_GRAY if input_active and input_rect == password_input else WHITE, password_input,
                         2)

        # 绘制文本
        create_room_text = font.render("创建房间", True, WHITE)
        join_room_text = font.render("加入房间", True, WHITE)
        num_players_label = font.render("玩家数: ", True, BLACK)
        num_players_display = font.render(num_players_text, True, BLACK)
        room_id_label = font.render("房间号: ", True, BLACK)
        room_id_display = font.render(room_id_text, True, BLACK)
        password_label = font.render("房间密码: ", True, BLACK)
        password_display = font.render("*" * len(password_text), True, BLACK)

        if created_room_id is not None:
            room_id_display_text = font.render(f"创建的房间号: {created_room_id}", True, BLACK)
            screen.blit(room_id_display_text, (WIDTH // 2 - room_id_display_text.get_width() // 2, HEIGHT // 2 + 250))

        if waiting_for_game:
            waiting_text = font.render("等待其他玩家加入...", True, BLACK)
            screen.blit(waiting_text, (WIDTH // 2 - waiting_text.get_width() // 2, HEIGHT // 2 + 200))

        screen.blit(create_room_text,
                    (create_room_button.centerx - create_room_text.get_width() // 2,
                     create_room_button.centery - create_room_text.get_height() // 2))
        screen.blit(join_room_text,
                    (join_room_button.centerx - join_room_text.get_width() // 2,
                     join_room_button.centery - join_room_text.get_height() // 2))
        screen.blit(num_players_label,
                    (num_players_input.x - num_players_label.get_width() - 10,
                     num_players_input.centery - num_players_label.get_height() // 2))
        screen.blit(num_players_display,
                    (num_players_input.x + 5, num_players_input.centery - num_players_display.get_height() // 2))
        screen.blit(room_id_label,
                    (room_id_input.x - room_id_label.get_width() - 10,
                     room_id_input.centery - room_id_label.get_height() // 2))
        screen.blit(room_id_display,
                    (room_id_input.x + 5, room_id_input.centery - room_id_display.get_height() // 2))
        screen.blit(password_label,
                    (password_input.x - password_label.get_width() - 10,
                     password_input.centery - password_label.get_height() // 2))
        screen.blit(password_display,
                    (password_input.x + 5, password_input.centery - password_display.get_height() // 2))

        pygame.display.flip()

        if game:
            break

    return


def draw_buttons():
    # 绘制投掷按钮
    pygame.draw.rect(screen, BLUE, roll_button)
    roll_text = font.render("投掷骰子", True, WHITE)
    screen.blit(roll_text, (roll_button.centerx - roll_text.get_width() // 2, roll_button.centery - roll_text.get_height() // 2))

    # 绘制购买按钮
    pygame.draw.rect(screen, GREEN, buy_button)
    buy_text = font.render("购买地块", True, WHITE)
    screen.blit(buy_text, (buy_button.centerx - buy_text.get_width() // 2, buy_button.centery - buy_text.get_height() // 2))

    # 绘制升级按钮
    pygame.draw.rect(screen, RED, upgrade_button)
    upgrade_text = font.render("升级地块", True, WHITE)
    screen.blit(upgrade_text, (upgrade_button.centerx - upgrade_text.get_width() // 2, upgrade_button.centery - upgrade_text.get_height() // 2))


def draw_players():
    num_tiles = len(game.board.tiles)
    side_length = num_tiles // 4
    map_size = min(WIDTH, HEIGHT) * 0.8
    tile_size = int(map_size / side_length)
    x_offset = (WIDTH - map_size) // 2
    y_offset = (HEIGHT - map_size) // 2

    for index, player in enumerate(game.players):
        pos = player.position
        if pos < side_length:  # 上边
            x_coord = x_offset + pos * tile_size + 5 + index * 10
            y_coord = y_offset + 5
        elif pos < 2 * side_length - 1:  # 右边
            x_coord = x_offset + (side_length - 1) * tile_size - 15
            y_coord = y_offset + (pos - side_length + 1) * tile_size + 5 + index * 10
        elif pos < 3 * side_length - 2:  # 下边
            x_coord = x_offset + (3 * side_length - 3 - pos) * tile_size + 5 + index * 10
            y_coord = y_offset + (side_length - 1) * tile_size - 15
        else:  # 左边
            x_coord = x_offset + 5
            y_coord = y_offset + (4 * side_length - 4 - pos) * tile_size + 5 + index * 10
        pygame.draw.circle(screen, player_colors[index % len(player_colors)], (x_coord, y_coord), 8)


def draw_action_logs():
    log_y = 10
    for log in action_logs[-5:]:
        log_text = font.render(log, True, BLACK)
        screen.blit(log_text, (10, log_y))
        log_y += 30


main_menu()

running = True
while running:
    if game:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if roll_button.collidepoint(event.pos) and not rolling and not game.game_over:
                    rolling = True
                    roll_animation_count = 0
                elif buy_button.collidepoint(event.pos) and not game.game_over:
                    current_player = game.get_current_player()
                    tile = game.board.get_tile(current_player.position)
                    if tile["type"] == "property" and tile.get("owner") is None:
                        if current_player.buy_property(tile):
                            action_logs.append(f"{current_player.name} 购买了 {tile['name']}")
                elif upgrade_button.collidepoint(event.pos) and not game.game_over:
                    current_player = game.get_current_player()
                    tile = game.board.get_tile(current_player.position)
                    if tile["type"] == "property" and tile.get("owner") == current_player:
                        if current_player.upgrade_property(tile):
                            action_logs.append(f"{current_player.name} 升级了 {tile['name']}")

        if rolling:
            roll_animation_count += 1
            if roll_animation_count >= roll_animation_frames:
                rolling = False
                current_player = game.get_current_player()
                if not current_player.in_jail:
                    steps, is_double = game.roll_dice()
                    current_player.move(steps)
                    result = game.handle_tile(current_player)
                    if result:
                        action_logs.append(result)
                    winner = game.check_bankruptcy()
                    if winner:
                        game.game_over = True
                    else:
                        game.next_player()
                    message = f"{current_player.name} 投掷骰子，前进 {steps} 步"
                    client.sendall(message.encode('utf-8'))
                    action_logs.append(message)
                else:
                    if current_player.jail_turns > 0:
                        current_player.jail_turns -= 1
                        if is_double:
                            current_player.in_jail = False
                        else:
                            game.next_player()

        screen.fill(WHITE)

        num_tiles = len(game.board.tiles)
        # 每边除去角上地块的数量
        side_length = (num_tiles - 4) // 4
        map_size = min(WIDTH, HEIGHT) * 0.8
        tile_size = int(map_size / (side_length + 2))
        x_offset = (WIDTH - map_size) // 2
        y_offset = (HEIGHT - map_size) // 2

        # 绘制地图
        for i in range(num_tiles):
            if i == 0:  # 左上角
                x_coord = x_offset
                y_coord = y_offset
            elif i < side_length + 1:  # 上边
                x_coord = x_offset + (i) * tile_size
                y_coord = y_offset
            elif i == side_length + 1:  # 右上角
                x_coord = x_offset + (side_length + 1) * tile_size
                y_coord = y_offset
            elif i < 2 * side_length + 2:  # 右边
                x_coord = x_offset + (side_length + 1) * tile_size
                y_coord = y_offset + (i - side_length - 1) * tile_size
            elif i == 2 * side_length + 2:  # 右下角
                x_coord = x_offset + (side_length + 1) * tile_size
                y_coord = y_offset + (side_length + 1) * tile_size
            elif i < 3 * side_length + 3:  # 下边
                x_coord = x_offset + (3 * side_length + 3 - i) * tile_size
                y_coord = y_offset + (side_length + 1) * tile_size
            elif i == 3 * side_length + 3:  # 左下角
                x_coord = x_offset
                y_coord = y_offset + (side_length + 1) * tile_size
            else:  # 左边
                x_coord = x_offset
                y_coord = y_offset + (4 * side_length + 4 - i) * tile_size

            tile = game.board.get_tile(i)
            pygame.draw.rect(screen, BLUE, (x_coord, y_coord, tile_size, tile_size), 1)
            text = font.render(tile["name"], True, BLACK)
            screen.blit(text, (x_coord + 5, y_coord + 5))

            owner = tile.get("owner")
            if owner:
                owner_text = font.render(f"业主: {owner.name}", True, BLACK)
                screen.blit(owner_text, (x_coord + 5, y_coord + 25))

        draw_players()
        draw_buttons()
        draw_action_logs()

        if not game.game_over:
            current_player = game.get_current_player()
            turn_text = font.render(f"轮到 {current_player.name} 操作", True, BLACK)
            screen.blit(turn_text, (WIDTH // 2 - turn_text.get_width() // 2, HEIGHT - 50))
        else:
            winner = game.players[0]
            win_text = font.render(f"{winner.name} 获胜！", True, BLACK)
            screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT - 50))

        pygame.display.flip()
    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

client.close()
pygame.quit()