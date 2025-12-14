import pygame
import sys
import os
import time

# Try importing OpenCV + numpy for video background
use_video = True
try:
    import cv2
    import numpy as np
except ImportError:
    print("⚠️ OpenCV not installed, falling back to static background.")
    use_video = False

# Initialize pygame
pygame.init()
pygame.mixer.init()

# --- Screen setup ---
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bahubali: Path to love")

# --- Sounds ---
pygame.mixer.music.load("bg.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

collision_sound = pygame.mixer.Sound("collision.mpeg")
win_sound = pygame.mixer.Sound("winning.mpeg")

# --- Background (video or static) ---
if use_video and os.path.exists("video.mp4"):
    video = cv2.VideoCapture("video.mp4")
else:
    background = pygame.image.load("background.jpg")
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    use_video = False

# --- Front page image ---
front_image = pygame.image.load("intro.jpg")
front_image = pygame.transform.scale(front_image, (WIDTH, HEIGHT))

# --- Button setup ---
button_color = (255, 215, 0)
button_hover = (255, 255, 100)
button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 100, 200, 60)

def draw_button(text, rect, hover=False):
    font = pygame.font.SysFont("Arial", 32, bold=True)
    color = button_hover if hover else button_color
    pygame.draw.rect(screen, color, rect, border_radius=15)
    label = font.render(text, True, (0, 0, 0))
    screen.blit(label, (rect.centerx - label.get_width()//2,
                        rect.centery - label.get_height()//2))

# --- Game constants ---
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 5
PLAYER_SIZE = 90
clock = pygame.time.Clock()

# --- Load images ---
player_img = pygame.image.load("bahu.png")
player_img = pygame.transform.scale(player_img, (PLAYER_SIZE, PLAYER_SIZE))

platform_img = pygame.image.load("platform.png")
platform_img = pygame.transform.scale(platform_img, (200, 20))

obstacle_img = pygame.image.load("bala1.png")
obstacle_img = pygame.transform.scale(obstacle_img, (200, 90))

goal_img = pygame.image.load("deva.png")
goal_img = pygame.transform.scale(goal_img, (100, 100))

# --- Objects ---
player = pygame.Rect(100, HEIGHT - 180, PLAYER_SIZE, PLAYER_SIZE)
vel_x, vel_y = 0, 0
gravity_reversed = False
can_flip = True
flip_cooldown = 0

platforms = [
    pygame.Rect(0, HEIGHT - 50, WIDTH, 50),
    pygame.Rect(150, HEIGHT - 150, 200, 20),
    pygame.Rect(400, HEIGHT - 250, 200, 20),
    pygame.Rect(200, HEIGHT - 350, 200, 20),
    pygame.Rect(500, HEIGHT - 450, 200, 20),
    pygame.Rect(300, HEIGHT - 550, 200, 20),
]

obstacles = [
    pygame.Rect(160, HEIGHT - 190, 40, 40),
    pygame.Rect(520, HEIGHT - 490, 40, 40),
]
obstacle_directions = [1, -1]
obstacle_speed = 3

goal = pygame.Rect(720, 40, 40, 40)

# --- Game state ---
game_over = False
win = False
show_front = True   # <--- start at front page
score = 0
start_time = 0

def reset_game():
    global player, vel_x, vel_y, gravity_reversed, game_over, win, can_flip, flip_cooldown, obstacles, obstacle_directions, score, start_time
    player.x, player.y = 100, HEIGHT - 80
    vel_x, vel_y = 0, 0
    gravity_reversed = False
    game_over = False
    win = False
    can_flip = True
    flip_cooldown = 0
    obstacles[0].x, obstacles[0].y = 160, HEIGHT - 190
    obstacles[1].x, obstacles[1].y = 520, HEIGHT - 490
    obstacle_directions[:] = [1, -1]
    score = 0
    start_time = time.time()

def on_ground():
    """Check if player is standing on a platform."""
    for plat in platforms:
        if not gravity_reversed and player.bottom == plat.top and player.centerx in range(plat.left, plat.right):
            return True
        if gravity_reversed and player.top == plat.bottom and player.centerx in range(plat.left, plat.right):
            return True
    return False

# --- Main loop ---
running = True
while running:
    if show_front:   # --- FRONT PAGE ---
        screen.blit(front_image, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        hover = button_rect.collidepoint(mouse_pos)
        draw_button("Start Game", button_rect, hover)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    show_front = False
                    reset_game()

        pygame.display.flip()
        clock.tick(FPS)
        continue

    # --- BACKGROUND ---
    if use_video:
        ret, frame = video.read()
        if not ret:
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = video.read()
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_surface = pygame.surfarray.make_surface(np.rot90(frame))
        screen.blit(frame_surface, (0, 0))
    else:
        screen.blit(background, (0, 0))

    # --- Events ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not (game_over or win):
                if can_flip and on_ground():
                    gravity_reversed = not gravity_reversed
                    can_flip = False
                    flip_cooldown = 15
            if event.key == pygame.K_r and game_over:
                reset_game()
            if event.key == pygame.K_n and win:
                reset_game()

    # --- Controls ---
    keys = pygame.key.get_pressed()
    vel_x = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        vel_x = -PLAYER_SPEED
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        vel_x = PLAYER_SPEED

    # --- Game logic ---
    if not game_over and not win:
        vel_y += -GRAVITY if gravity_reversed else GRAVITY
        player.x += vel_x
        player.y += vel_y

        if player.x < 0: player.x = 0
        if player.x > WIDTH - player.width: player.x = WIDTH - player.width

        for plat in platforms:
            if player.colliderect(plat):
                if not gravity_reversed and vel_y > 0:
                    player.bottom = plat.top
                    vel_y = 0
                elif gravity_reversed and vel_y < 0:
                    player.top = plat.bottom
                    vel_y = 0

        for i, obs in enumerate(obstacles):
            obs.x += obstacle_directions[i] * obstacle_speed
            if obs.left <= 0 or obs.right >= WIDTH:
                obstacle_directions[i] *= -1

        if player.colliderect(goal):
            if not win:
                win_sound.play()
            win = True

        for obs in obstacles:
            if player.colliderect(obs):
                if not game_over:
                    collision_sound.play()
                game_over = True

        if player.y > HEIGHT + 100 or player.y < -100:
            game_over = True

        # --- Update score ---
        score = int(time.time() - start_time)

    if not can_flip:
        flip_cooldown -= 1
        if flip_cooldown <= 0:
            can_flip = True

    # --- Draw objects ---
    screen.blit(player_img, player)
    for plat in platforms: screen.blit(platform_img, plat)
    for obs in obstacles: screen.blit(obstacle_img, obs)
    screen.blit(goal_img, goal)

    # --- UI ---
    font = pygame.font.SysFont("Arial", 28)

    # live score
    score_text = font.render(f"Score: {score}", True, (255, 0, 0))
    screen.blit(score_text, (10, 10))

    if game_over:
        text = font.render("Game Over! Press R to restart", True, (255, 255, 255))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 30))

        final_text = font.render(f"Your Score: {score}", True, (255, 215, 0))
        screen.blit(final_text, (WIDTH//2 - final_text.get_width()//2, HEIGHT//2 + 20))

    elif win:
        text = font.render("You Win! Press N to play again", True, (255, 255, 255))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 30))

        final_text = font.render(f"Your Score: {score}", True, (255, 215, 0))
        screen.blit(final_text, (WIDTH//2 - final_text.get_width()//2, HEIGHT//2 + 20))

    pygame.display.flip()
    clock.tick(FPS)

# --- Cleanup ---
if use_video:
    video.release()
pygame.quit()

sys.exit()
