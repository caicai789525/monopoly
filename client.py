import pygame
import socket
import threading
import sys
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
GRAY = (150, 150, 150)

# 字体设置
font = pygame.font.SysFont("SimHei", 20)
large_font = pygame.font.SysFont("SimHei", 24)

# 连接服务器
client = None
try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 5555))
except Exception as e:
    print(f"连接服务器失败: {e}")
    pygame.quit()
    sys.exit(1)

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

# 按钮设置
button_width = 200
button_height = 50
button_x = (WIDTH - button_width) // 2
roll_button = pygame.Rect(button_x, HEIGHT - 200, button_width, button_height)
buy_button = pygame.Rect(button_x, HEIGHT - 270, button_width, button_height)
upgrade_button = pygame.Rect(button_x, HEIGHT - 340, button_width, button_height)
end_turn_button = pygame.Rect(button_x, HEIGHT - 410, button_width, button_height)
quit_button = pygame.Rect(WIDTH - 120, 10, 100, 40)

# 玩家颜色
player_colors = [RED, BLUE, GREEN, YELLOW]

# 投掷动画相关
rolling = False
roll_animation_frames = 20
roll_animation_count = 0
dice_result = None

# 操作日志列表
action_logs = []

def send_network_message(message):
    """发送网络消息到服务器"""
    try:
        if client:
            client.sendall(message.encode('utf-8'))
    except ConnectionResetError:
        error_msg = "网络连接已重置，无法发送消息"
        action_logs.append(error_msg)
        print(error_msg)
    except BrokenPipeError:
        error_msg = "管道破裂，无法发送消息"
        action_logs.append(error_msg)
        print(error_msg)
    except Exception as e:
        error_msg = f"网络错误: {str(e)}"
        action_logs.append(error_msg)
        print(error_msg)

def receive_messages():
    """接收服务器消息的线程"""
    global game, num_players, room_id, waiting_for_game, created_room_id, action_logs
    while True:
        try:
            if not client:
                break

            data = client.recv(1024).decode('utf-8')
            if not data:
                break

            parts = data.split('|')
            command = parts[0]

            if command == 'ROOM_CREATED':
                created_room_id = int(parts[1])
                action_logs.append(f"房间创建成功，房间号: {created_room_id}")
                waiting_for_game = True
            elif command == 'ROOM_JOINED':
                action_logs.append("成功加入房间")
                waiting_for_game = True
            elif command == 'ROOM_FULL_OR_NOT_EXIST':
                action_logs.append("房间已满或不存在")
                waiting_for_game = False
            elif command == 'GAME_START':
                try:
                    game = Game(num_players, initial_money)
                    action_logs.append("游戏开始！")
                    waiting_for_game = False
                except Exception as e:
                    action_logs.append(f"游戏初始化失败: {str(e)}")
            elif command == 'PLAYER_MOVE':
                player_id = int(parts[1])
                steps = int(parts[2])
                action_logs.append(f"玩家{player_id+1} 投掷骰子，前进 {steps} 步")
            elif command == 'PLAYER_BUY':
                player_id = int(parts[1])
                property_name = parts[2]
                action_logs.append(f"玩家{player_id+1} 购买了 {property_name}")
            elif command == 'PLAYER_UPGRADE':
                player_id = int(parts[1])
                property_name = parts[2]
                action_logs.append(f"玩家{player_id+1} 升级了 {property_name}")
            elif command == 'GAME_OVER':
                winner_id = int(parts[1])
                action_logs.append(f"游戏结束！玩家{winner_id+1} 获胜！")
                if game:
                    game.game_over = True

        except ConnectionResetError:
            action_logs.append("服务器断开连接")
            break
        except Exception as e:
            action_logs.append(f"接收消息错误: {e}")
            break

if client:
    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.daemon = True
    receive_thread.start()

def main_menu():
    """显示主菜单，处理房间创建和加入"""
    global num_players, current_input, input_rect, input_type, input_active, waiting_for_game, created_room_id, password, game
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
                sys.exit(0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if create_room_button.collidepoint(event.pos):
                    try:
                        num_players = int(num_players_text) if num_players_text else 2
                        send_network_message(f"CREATE_ROOM|{num_players}|{password_text}")
                    except ValueError:
                        action_logs.append("请输入有效的玩家数")
                elif join_room_button.collidepoint(event.pos):
                    try:
                        room_id = int(room_id_text) if room_id_text else 0
                        send_network_message(f"JOIN_ROOM|{room_id}|{password_text}")
                    except ValueError:
                        action_logs.append("请输入有效的房间号")
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

        # 绘制标题
        title = large_font.render("大富翁游戏", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))

        # 绘制按钮
        pygame.draw.rect(screen, BLUE, create_room_button)
        pygame.draw.rect(screen, BLUE, join_room_button)

        # 绘制输入框
        pygame.draw.rect(screen, LIGHT_GRAY if input_active and input_rect == num_players_input else WHITE,
                         num_players_input, 2)
        pygame.draw.rect(screen, LIGHT_GRAY if input_active and input_rect == room_id_input else WHITE, room_id_input, 2)
        pygame.draw.rect(screen, LIGHT_GRAY if input_active and input_rect == password_input else WHITE, password_input, 2)

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

def calculate_map_info():
    """计算地图布局参数"""
    if not game or not hasattr(game, 'board') or not game.board.tiles:
        return 0, 0, 0, 0, 0, 0

    num_tiles = len(game.board.tiles)
    side_length = num_tiles // 4
    map_size = min(WIDTH, HEIGHT) * 0.7
    base_tile_size = map_size // (side_length + 1)
    x_offset = (WIDTH - map_size) // 2
    y_offset = (HEIGHT - map_size) // 3
    return num_tiles, side_length, map_size, base_tile_size, x_offset, y_offset

def draw_players():
    """绘制玩家在地图上的位置"""
    if not game or not hasattr(game, 'players'):
        return

    num_tiles, side_length, map_size, tile_size, x_off, y_off = calculate_map_info()

    for index, player in enumerate(game.players):
        if not hasattr(player, 'position'):
            continue

        pos = player.position
        if pos < side_length:
            x = x_off + pos * tile_size + tile_size//2 + index * 8
            y = y_off + tile_size//4
        elif pos < 2 * side_length:
            x = x_off + map_size - tile_size//4
            y = y_off + (pos - side_length) * tile_size + tile_size//2 + index * 8
        elif pos < 3 * side_length:
            x = x_off + map_size - (pos - 2 * side_length + 1) * tile_size + tile_size//2
            y = y_off + map_size - tile_size//4
        else:
            x = x_off + tile_size//4
            y = y_off + map_size - (pos - 3 * side_length + 1) * tile_size + tile_size//2

        pygame.draw.circle(screen, BLACK, (int(x), int(y)), 12)
        pygame.draw.circle(screen, player_colors[index % len(player_colors)], (int(x), int(y)), 10)

def draw_tile_info(x, y, width, height, tile, is_corner=False):
    """绘制地图格子信息"""
    if not tile or not isinstance(tile, dict):
        return

    if is_corner:
        corner_size = width
        pygame.draw.rect(screen, (255, 220, 220), (x, y, corner_size, corner_size))
        pygame.draw.rect(screen, BLACK, (x, y, corner_size, corner_size), 2)

        name_font = pygame.font.SysFont("SimHei", 16)
        name_text = name_font.render(tile.get("name", "未知地块"), True, BLACK)
        screen.blit(name_text, (x + (corner_size - name_text.get_width())//2, y + 15))

        if "effect" in tile:
            effect_font = pygame.font.SysFont("SimHei", 14)
            effect_text = effect_font.render(tile["effect"], True, (150, 0, 0))
            screen.blit(effect_text, (x + (corner_size - effect_text.get_width())//2, y + 40))
        return

    if tile.get("type") == "property":
        color = (200, 255, 200) if tile.get("owner") is None else (255, 200, 200)
    elif tile.get("type") in ["chance", "community"]:
        color = (255, 255, 200)
    elif tile.get("type") == "tax":
        color = (200, 200, 255)
    else:
        color = (240, 240, 240)

    pygame.draw.rect(screen, color, (x, y, width, height))
    pygame.draw.rect(screen, BLACK, (x, y, width, height), 1)

    name = tile.get("name", "未知地块")
    font_size = 14
    if len(name) > 6:
        font_size = max(10, 14 - (len(name) - 6))
    name_font = pygame.font.SysFont("SimHei", font_size)
    name_text = name_font.render(name, True, BLACK)

    text_x = x + (width - name_text.get_width()) // 2
    text_y = y + (height - name_text.get_height()) // 2
    screen.blit(name_text, (text_x, text_y))

    info_font = pygame.font.SysFont("SimHei", 10)
    if "price" in tile:
        price_text = info_font.render(f"¥{tile['price']}", True, (0, 100, 0))
        screen.blit(price_text, (x + 5, y + height - 15))
    if "rent" in tile:
        level_text = info_font.render(f"租金:¥{tile['rent']}", True, (0, 0, 150))
        screen.blit(level_text, (x + width - 40, y + 5))

def draw_buttons():
    """绘制操作按钮"""
    pygame.draw.rect(screen, BLUE, roll_button)
    roll_text = font.render("投掷骰子", True, WHITE)
    screen.blit(roll_text, (roll_button.centerx - roll_text.get_width()//2, roll_button.centery - roll_text.get_height()//2))

    pygame.draw.rect(screen, GREEN, buy_button)
    buy_text = font.render("购买地块", True, WHITE)
    screen.blit(buy_text, (buy_button.centerx - buy_text.get_width()//2, buy_button.centery - buy_text.get_height()//2))

    pygame.draw.rect(screen, RED, upgrade_button)
    upgrade_text = font.render("升级地块", True, WHITE)
    screen.blit(upgrade_text, (upgrade_button.centerx - upgrade_text.get_width()//2, upgrade_button.centery - upgrade_text.get_height()//2))

    pygame.draw.rect(screen, YELLOW, end_turn_button)
    end_turn_text = font.render("结束回合", True, BLACK)
    screen.blit(end_turn_text, (end_turn_button.centerx - end_turn_text.get_width()//2, end_turn_button.centery - end_turn_text.get_height()//2))

    pygame.draw.rect(screen, RED, quit_button)
    quit_text = font.render("退出游戏", True, WHITE)
    screen.blit(quit_text, (quit_button.centerx - quit_text.get_width()//2, quit_button.centery - quit_text.get_height()//2))

def draw_action_logs():
    """绘制操作日志"""
    log_y = 10
    for log in action_logs[-5:]:
        log_text = font.render(log, True, BLACK)
        screen.blit(log_text, (10, log_y))
        log_y += 30

def draw_player_info():
    """绘制玩家信息"""
    if not game or not hasattr(game, 'players'):
        return

    info_x = 10
    info_y = HEIGHT - 150
    info_width = WIDTH - 20
    info_height = 140

    pygame.draw.rect(screen, LIGHT_GRAY, (info_x, info_y, info_width, info_height))
    pygame.draw.rect(screen, BLACK, (info_x, info_y, info_width, info_height), 2)

    current_player = game.get_current_player() if hasattr(game, 'get_current_player') else None
    for i, player in enumerate(game.players):
        if not hasattr(player, 'money'):
            continue

        player_x = info_x + 10 + i * (info_width // len(game.players))
        player_width = (info_width - 20) // len(game.players)

        pygame.draw.rect(screen, player_colors[i], (player_x, info_y + 10, 20, 20))

        name_text = font.render(f"玩家{i+1}", True, BLACK)
        money_text = font.render(f"¥{player.money}", True, BLACK)
        jail_text = font.render("在监狱" if player.in_jail else "", True, RED)

        screen.blit(name_text, (player_x + 30, info_y + 10))
        screen.blit(money_text, (player_x + 30, info_y + 35))
        screen.blit(jail_text, (player_x + 30, info_y + 60))

        if player == current_player:
            pygame.draw.rect(screen, BLACK, (player_x, info_y + 10, 20, 20), 2)
            current_text = font.render("当前回合", True, RED)
            screen.blit(current_text, (player_x + 30, info_y + 85))

# 启动主菜单
main_menu()

# 主游戏循环
running = True
try:
    while running:
        if game and hasattr(game, 'players') and len(game.players) > 0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    try:
                        if quit_button.collidepoint(event.pos):
                            running = False
                        elif roll_button.collidepoint(event.pos) and not rolling and not game.game_over:
                            rolling = True
                            roll_animation_count = 0
                            dice_result = None
                            print("开始投掷骰子动画...")
                        elif buy_button.collidepoint(event.pos) and not game.game_over:
                            current_player = game.get_current_player()
                            if current_player and hasattr(game, 'board'):
                                tile = game.board.get_tile(current_player.position)
                                if tile and tile.get("type") == "property" and tile.get("owner") is None:
                                    if hasattr(current_player, 'buy_property') and callable(current_player.buy_property):
                                        if current_player.buy_property(tile):
                                            action_logs.append(f"{current_player.name} 购买了 {tile['name']}")
                                            send_network_message(f"PLAYER_BUY|{game.players.index(current_player)}|{tile['name']}")
                        elif upgrade_button.collidepoint(event.pos) and not game.game_over:
                            current_player = game.get_current_player()
                            if current_player and hasattr(game, 'board'):
                                tile = game.board.get_tile(current_player.position)
                                if tile and tile.get("type") == "property" and tile.get("owner") == current_player:
                                    if hasattr(current_player, 'upgrade_property') and callable(current_player.upgrade_property):
                                        if current_player.upgrade_property(tile):
                                            action_logs.append(f"{current_player.name} 升级了 {tile['name']}")
                                            send_network_message(f"PLAYER_UPGRADE|{game.players.index(current_player)}|{tile['name']}")
                        elif end_turn_button.collidepoint(event.pos) and not game.game_over and not rolling:
                            if hasattr(game, 'next_player'):
                                game.next_player()
                                action_logs.append(f"{game.get_current_player().name} 的回合开始")
                    except Exception as e:
                        error_msg = f"处理鼠标点击事件时出错: {str(e)}"
                        action_logs.append(error_msg)
                        print(error_msg)

            if rolling:
                try:
                    roll_animation_count += 1
                    if roll_animation_count >= roll_animation_frames:
                        rolling = False
                        if game and not game.game_over and hasattr(game, 'get_current_player'):
                            current_player = game.get_current_player()
                            if current_player and hasattr(game, 'roll_dice'):
                                # 处理监狱状态
                                jail_result = game.handle_jail(current_player)
                                if jail_result:
                                    action_logs.append(jail_result)
                                if not current_player.in_jail:
                                    steps, is_double = game.roll_dice()
                                    dice_result = steps
                                    print(f"骰子结果: {steps}")

                                    if hasattr(current_player, 'move'):
                                        current_player.move(steps)
                                        print(f"玩家移动到位置: {current_player.position}")

                                        if hasattr(game, 'handle_tile'):
                                            result = game.handle_tile(current_player)
                                            if result:
                                                action_logs.append(result)

                                        if hasattr(game, 'check_bankruptcy'):
                                            winner = game.check_bankruptcy()
                                            if winner:
                                                game.game_over = True
                                                send_network_message(f"GAME_OVER|{game.players.index(winner)}")
                                            else:
                                                send_network_message(f"PLAYER_MOVE|{game.players.index(current_player)}|{steps}")
                                else:
                                    action_logs.append(f"{current_player.name} 在监狱中，无法移动")
                except Exception as e:
                    error_msg = f"处理掷骰子动画时出错: {str(e)}"
                    action_logs.append(error_msg)
                    print(error_msg)
                    rolling = False

            screen.fill(WHITE)

            num_tiles, side_length, map_size, tile_size, x_off, y_off = calculate_map_info()

            pygame.draw.rect(screen, (250, 250, 250), (x_off, y_off, map_size, map_size))
            pygame.draw.rect(screen, BLACK, (x_off, y_off, map_size, map_size), 3)

            for i in range(num_tiles):
                is_corner = i % side_length == 0
                if i < side_length:
                    if is_corner:
                        x = x_off
                        y = y_off
                        width = height = tile_size * 1.5
                    else:
                        x = x_off + tile_size * 1.5 + (i-1) * (map_size - 2*tile_size*1.5) // (side_length-1)
                        y = y_off
                        width = (map_size - 2*tile_size*1.5) // (side_length-1)
                        height = tile_size
                elif i < 2 * side_length:
                    if is_corner:
                        x = x_off + map_size - tile_size * 1.5
                        y = y_off
                        width = height = tile_size * 1.5
                    else:
                        x = x_off + map_size - tile_size
                        y = y_off + tile_size * 1.5 + (i-side_length-1) * (map_size - 2*tile_size*1.5) // (side_length-1)
                        width = tile_size
                        height = (map_size - 2*tile_size*1.5) // (side_length-1)
                elif i < 3 * side_length:
                    if is_corner:
                        x = x_off + map_size - tile_size * 1.5
                        y = y_off + map_size - tile_size * 1.5
                        width = height = tile_size * 1.5
                    else:
                        x = x_off + tile_size * 1.5 + (3*side_length-i-1) * (map_size - 2*tile_size*1.5) // (side_length-1)
                        y = y_off + map_size - tile_size
                        width = (map_size - 2*tile_size*1.5) // (side_length-1)
                        height = tile_size
                else:
                    if is_corner:
                        x = x_off
                        y = y_off + map_size - tile_size * 1.5
                        width = height = tile_size * 1.5
                    else:
                        x = x_off
                        y = y_off + tile_size * 1.5 + (4*side_length-i-1) * (map_size - 2*tile_size*1.5) // (side_length-1)
                        width = tile_size
                        height = (map_size - 2*tile_size*1.5) // (side_length-1)

                tile = game.board.get_tile(i) if hasattr(game, 'board') else None
                draw_tile_info(int(x), int(y), int(width), int(height), tile, is_corner)

            draw_players()
            draw_buttons()
            draw_action_logs()
            draw_player_info()

            if dice_result is not None:
                dice_text = large_font.render(f"骰子结果: {dice_result}", True, BLACK)
                screen.blit(dice_text, (WIDTH//2 - dice_text.get_width()//2, HEIGHT - 500))

            if not game.game_over:
                current_player = game.get_current_player() if hasattr(game, 'get_current_player') else None
                if current_player:
                    turn_text = font.render(f"轮到 {current_player.name} 操作", True, BLACK)
                    screen.blit(turn_text, (WIDTH // 2 - turn_text.get_width() // 2, HEIGHT - 50))

                    if hasattr(game, 'board'):
                        tile = game.board.get_tile(current_player.position)
                        if tile:
                            tile_info = font.render(f"当前位置: {tile.get('name', '未知')}", True, BLACK)
                            screen.blit(tile_info, (WIDTH//2 - tile_info.get_width()//2, HEIGHT - 80))
            else:
                winner = next((p for p in game.players if not p.is_bankrupt()), None) if hasattr(game, 'players') else None
                if winner:
                    win_text = large_font.render(f"{winner.name} 获胜！", True, RED)
                    screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2 - 50))

            pygame.display.flip()
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

except KeyboardInterrupt:
    print("游戏被手动终止")
except Exception as e:
    print(f"游戏运行时发生错误: {str(e)}")
    action_logs.append(f"游戏运行时发生错误: {str(e)}")
finally:
    if client:
        client.close()
    pygame.quit()
    sys.exit(0)