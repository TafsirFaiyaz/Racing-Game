from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time


# --- GLOBAL STATE ---
# Define track width for the racing path
TRACK_WIDTH = 10.0

# Lists to store track control points, track points, objects, particles
CONTROL_POINTS = []
TRACK_POINTS = []
objects = []
particles = []
trees = []

# Game state variables
game_finished = [False, False]  
current_level = 0  
start_delay_time = 0
level_completed = False  
level_complete_time = 0  
paused = False  
health = [5.0, 5.0]
round_winners = []  
finish_times = [None, None]

# Car state for two players
position = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]  
orientation = [0.0, 0.0]  
velocity = [0.0, 0.0] 
top_speed = 0.3  
acceleration = 0.005  
base_handling = 0.06  
handling = [base_handling, base_handling]  
slippery_end_time = [0, 0]  
BOOSTED_TOP_SPEED = top_speed * 2.0 
max_speed = [top_speed, top_speed]  
boost_end_time = [0, 0] 
car_colors = [(1, 0, 0), (0, 0, 1)]  
camera_mode = [1, 1]  

# Input state for key presses
keys = {
    'p1_accel': False,  
    'p1_left': False,   
    'p1_right': False,  
    'p2_accel': False,  
    'p2_left': False,   
    'p2_right': False,  
    'enter': False,     
}


def generate_track():
    samples = 600
    TRACK_POINTS.clear()
    
    for i in range(samples):
        t = i / float(samples)
        x = 0.0
        y = 0.0
        z = t * 150.0
        TRACK_POINTS.append((x, y, z))


def generate_trees():
    trees.clear()
    num_trees_per_side = 30
    
    for i in range(num_trees_per_side):
        z = random.uniform(0, 150)
        x_left = -7.0 + random.uniform(-1.0, 1.0)
        x_right = 7.0 + random.uniform(-1.0, 1.0)
        
        trees.append((x_left, 0.0, z))
        trees.append((x_right, 0.0, z))


def generate_objects():
    num_cube = 40
    num_boost = 10
    num_speed_down = 10
    num_slippery = 15
    
    total_obj = num_cube + num_boost + num_speed_down + num_slippery
    objects.clear()
    
    N = len(TRACK_POINTS)
    picks = random.sample(range(10, N - 10), total_obj)
    kinds = ['obs'] * num_cube + ['boost'] * num_boost + ['speed_down'] * num_speed_down + ['slippery'] * num_slippery
    random.shuffle(kinds)
    
    for idx, kind in zip(picks, kinds):
        x, y, z = TRACK_POINTS[idx]
        x = random.uniform(-TRACK_WIDTH / 2 + 0.25, TRACK_WIDTH / 2 - 0.25)
        objects.append({'type': kind, 'pos': (x, y, z), 'active': True})


def draw_track():
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.2, 0.2)
    
    for i in range(len(TRACK_POINTS) - 1):
        x1, y1, z1 = TRACK_POINTS[i]
        x2, y2, z2 = TRACK_POINTS[i + 1]
        w = TRACK_WIDTH / 2
        glVertex3f(x1 + w, y1, z1)
        glVertex3f(x1 - w, y1, z1)
        glVertex3f(x2 - w, y2, z2)
        glVertex3f(x2 + w, y2, z2)
    
    glEnd()


def draw_car(color):
    glColor3f(*color)
    glPushMatrix()
    glScalef(1.0, 0.3, 0.5)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glColor3f(0.7, 0.7, 1.0)
    glPushMatrix()
    glTranslatef(0.0, 0.35, 0.0)
    glScalef(0.5, 0.25, 0.3)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glColor3f(0.0, 0.0, 0.0)
    wheel_radius = 0.2
    wheel_width = 0.1
    wheel_offset_x = 0.6
    wheel_offset_z = 0.35
    
    for x in [-wheel_offset_x, wheel_offset_x]:
        for z in [-wheel_offset_z, wheel_offset_z]:
            glPushMatrix()
            glTranslatef(x, -0.05, z)
            glRotatef(90, 0, 1, 0)
            glutSolidTorus(wheel_width / 2, wheel_radius, 20, 40)
            glPopMatrix()


def draw_objects():
    for obj in objects:
        if not obj['active']:
            continue
        
        x, y, z = obj['pos']
        glPushMatrix()
        glTranslatef(x, y + 0.01, z)
        
        if obj['type'] == 'obs':
            glColor3f(0.5, 0.5, 0.5)
            glScalef(0.25, 0.25, 0.25)
            glutSolidCube(2.0)
            
        elif obj['type'] == 'boost':
            glColor3f(1, 1, 0)
            glutSolidSphere(0.25, 16, 16)
            
        elif obj['type'] == 'speed_down':
            glColor3f(0, 1, 0)
            glutSolidSphere(0.25, 16, 16)
            
            
        elif obj['type'] == 'slippery':
            glColor3f(0.6, 0.4, 0)
            
            glBegin(GL_QUADS)
            
            glVertex3f(-0.5, 0, -0.5)
            glVertex3f(0.5, 0, -0.5)
            glVertex3f(0.5, 0, 0.5)
            glVertex3f(-0.5, 0, 0.5)
            
            glEnd()
        
        glPopMatrix()


def draw_tree(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.0, 0.6, 0.0)
    
    glBegin(GL_TRIANGLES)
    
    glVertex3f(-1.0, 0.0, 0.0)
    glVertex3f(1.0, 0.0, 0.0)
    glVertex3f(0.0, 3.0, 0.0)
    
    glVertex3f(0.0, 0.0, -1.0)
    glVertex3f(0.0, 0.0, 1.0)
    glVertex3f(0.0, 3.0, 0.0)
    
    glEnd()
    glPopMatrix()


def draw_trees():
    for tree_pos in trees:
        draw_tree(*tree_pos)


def draw_particles():
    
    if current_level == 1:
        glColor3f(0.5, 0.5, 1.0)
        glBegin(GL_LINES)
        
        for p in particles:
            x, y, z = p['pos']
            glVertex3f(x, y, z)
            glVertex3f(x, y - 1.0, z)
            
        glEnd()


def draw_sky():
    
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    
    if current_level == 0:
        glColor3f(0.5, 0.8, 0.9)
        glVertex3f(-100, 100, -100)
        glVertex3f(100, 100, -100)
        glColor3f(0.67, 0.85, 0.9)
        glVertex3f(100, 0, -100)
        glVertex3f(-100, 0, -100)
        
    elif current_level == 1:
        glColor3f(0.4, 0.4, 0.4)
        glVertex3f(-100, 100, -100)
        glVertex3f(100, 100, -100)
        glColor3f(0.6, 0.6, 0.6)
        glVertex3f(100, 0, -100)
        glVertex3f(-100, 0, -100)
    
    glEnd()
    glEnable(GL_DEPTH_TEST)


def draw_text(x, y, text):
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 800, 0, 600, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_pause_overlay():
    
    if paused:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, 800, 0, 600, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glColor3f(1, 1, 1)
        text = "PAUSED"
        
        glRasterPos2f(400 - len(text) * 14 / 2, 300)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
            
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


def show_overall_winner():
    p1_wins = round_winners.count(0)
    p2_wins = round_winners.count(1)
    
    if p1_wins > p2_wins:
        winner_text = "Player 1 Won!"
    
    elif p2_wins > p1_wins:
        winner_text = "Player 2 Won!"
        
    else:
        winner_text = "It's a Tie!"
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 800, 0, 600, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1, 1, 1)
    
    draw_text(400 - len(winner_text) * 9 / 2, 300, winner_text)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def aabb_collide(min1, max1, min2, max2):
    
    x_overlap = min1[0] < max2[0] and max1[0] > min2[0]
    y_overlap = min1[1] < max2[1] and max1[1] > min2[1]
    z_overlap = min1[2] < max2[2] and max1[2] > min2[2]
    
    return x_overlap and y_overlap and z_overlap


def check_collisions(player_id):
    
    global velocity, max_speed, boost_end_time, handling, health
    
    cx, cy, cz = position[player_id]
    car_min = (cx - 0.1, cy - 0.1, cz - 0.1)
    car_max = (cx + 0.1, cy + 0.1, cz + 0.1)
    
    t = time.time() 
    
    if player_id == 0:          #For speed down object to affect the opponent
        opponent_id = 1 
    else:
        opponent_id = 0 
    
    for obj in objects:
        
        if not obj['active']:
            continue
        
        x, y, z = obj['pos']
        
        o_min = (x - 0.3, y - 0.05, z - 0.3)
        o_max = (x + 0.3, y + 0.05, z + 0.3)
        
        if aabb_collide(car_min, car_max, o_min, o_max):
            
            if obj['type'] == 'obs':
                health[player_id] -= 1.0
                
                if health[player_id] == -1:
                    velocity[player_id] = max_speed[player_id]
                    health[player_id] = 0
                
                elif health[player_id] == 0:
                    health[player_id] = 0
                    max_speed[player_id] *= 0.3
                    
                else:
                    max_speed[player_id] *= 0.9
                    velocity[player_id] = 0.0
                    
            elif obj['type'] == 'boost':
                max_speed[player_id] = BOOSTED_TOP_SPEED
                boost_end_time[player_id] = t + 2000
                
            elif obj['type'] == 'speed_down':
                velocity[opponent_id] *= 0.2
                
            elif obj['type'] == 'slippery':
                handling[player_id] = base_handling * 0.3
                slippery_end_time[player_id] = t + 2000
                
            obj['active'] = False
    
    if boost_end_time[player_id] and t > boost_end_time[player_id]:     # Reset boost effect
        max_speed[player_id] = top_speed
        boost_end_time[player_id] = 0
    
    if slippery_end_time[player_id] and t > slippery_end_time[player_id]:
        handling[player_id] = base_handling
        slippery_end_time[player_id] = 0


def check_car_collision():
    p1_x, p1_y, p1_z = position[0]
    p2_x, p2_y, p2_z = position[1]
    dx = p1_x - p2_x
    dz = p1_z - p2_z
    dist_squared = dx * dx + dz * dz
    
    if dist_squared < 0.04:
        loser = random.choice([0, 1])
        velocity[loser] = 0.0


def update_physics():
    global position, velocity, game_finished, level_completed, level_complete_time, current_level, round_winners
    
    if paused or (level_completed and current_level == 1):
        return
    
    # Check if 2 seconds have passed since level start
    if time.time() - start_delay_time < 2.0:
        return
    
    check_car_collision()
    
    for player_id in range(2):
        if game_finished[player_id]:
            continue
        
        check_collisions(player_id)
        
        accel_key = 'p1_accel' if player_id == 0 else 'p2_accel'
        left_key = 'p1_left' if player_id == 0 else 'p2_left'
        right_key = 'p1_right' if player_id == 0 else 'p2_right'
        
        if keys[accel_key]:
            velocity[player_id] += acceleration
            
        if keys[accel_key]:
            velocity[player_id] += acceleration
        else:
            if velocity[player_id] > 0:
                velocity[player_id] -= acceleration / 2 
            else: 
                velocity[player_id] = 0
        
        velocity[player_id] = max(0, min(max_speed[player_id], velocity[player_id]))     # Velocity dont cross max speed and dont go negative
        
        if keys[left_key]:
            position[player_id][0] += handling[player_id]
        if keys[right_key]:
            position[player_id][0] -= handling[player_id]
        
        new_x = max(-TRACK_WIDTH / 2 + 0.1, min(TRACK_WIDTH / 2 - 0.1, position[player_id][0]))   # Stay within track bounds
        
        if new_x != position[player_id][0]:         # If out of bounds, speed penalty
            velocity[player_id] *= 0.9
            
        position[player_id][0] = new_x
        position[player_id][2] += velocity[player_id]
        
        if position[player_id][2] >= 150.0:
            position[player_id][2] = 150.0 
            game_finished[player_id] = True
            finish_times[player_id] = time.time()  # Record finish time
    
    if all(game_finished) and not level_completed:
        
        level_completed = True
        
        if finish_times[0] < finish_times[1]:
            round_winners.append(0)  
        elif finish_times[1] < finish_times[0]:
            round_winners.append(1)  
            
        else:
            round_winners.append(-1) # Tie
    
    
    if level_completed and keys['enter'] and current_level == 0:
        next_level()
    
    for p in particles:
        p['pos'][0] += p['vel'][0]
        p['pos'][1] += p['vel'][1]
        p['pos'][2] += p['vel'][2]
        
        if p['pos'][1] < -1:
            p['pos'] = [random.uniform(-5, 5), 20, random.uniform(0, 150)]
            if current_level == 1:
                p['vel'] = [0, random.uniform(-2.5, -1.5), 0]


def set_level_properties(level):
    
    global base_handling, handling, particles
    
    if level == 0:
        base_handling = 0.06
        particles = []
        
    elif level == 1:
        base_handling = 0.03
        particles = [{'pos': [random.uniform(-10, 10), 20, random.uniform(-10, 10)],
                      'vel': [0, random.uniform(-1.0, -0.5), 0]} for i in range(150)]
        
    handling = [base_handling, base_handling]

def next_level():
    global current_level, game_finished, position, velocity, max_speed, boost_end_time, level_completed, start_delay_time, health, slippery_end_time, finish_times
    
    current_level += 1
    game_finished = [False, False]
    position = [[-TRACK_WIDTH / 4, 0.0, 0.0], [TRACK_WIDTH / 4, 0.0, 0.0]]
    velocity = [0.0, 0.0]
    max_speed = [top_speed, top_speed]
    boost_end_time = [0, 0]
    slippery_end_time = [0, 0]
    health = [5.0, 5.0]
    level_completed = False
    finish_times = [None, None] 
    set_level_properties(current_level)
    generate_objects()
    generate_trees()
    start_delay_time = time.time()



def setup_viewport(player_id, width, height):
    if player_id == 0:
        glViewport(0, 0, width // 2, height)
    else:
        glViewport(width // 2, 0, width // 2, height)


def draw_player_view(player_id, width, height):
    setup_viewport(player_id, width, height)
    
    if current_level == 0:
        glClearColor(0.529, 0.808, 0.922, 1.0)
        
    elif current_level == 1:
        glClearColor(0.5, 0.5, 0.5, 1.0)
    
    if player_id == 0:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
    else:
        glClear(GL_DEPTH_BUFFER_BIT)
    
    if not (all(game_finished) and current_level == 1):     # Game finish na hoile 3D view draw hobe
        
        glLoadIdentity()
        px, py, pz = position[player_id]
        cos_o = math.cos(orientation[player_id])
        sin_o = math.sin(orientation[player_id])
        
        if camera_mode[player_id] == 0:
            eye_x = px + 0.3 * sin_o
            eye_y = py + 0.1
            eye_z = pz + 0.3 * cos_o
            
            center_x = px + 0.8 * sin_o
            center_y = py + 0.1
            center_z = pz + 0.8 * cos_o
            
            gluLookAt(eye_x, eye_y, eye_z, center_x, center_y, center_z, 0, 1, 0)
            
        else:
            eye_x = px - 4.0 * sin_o
            eye_y = py + 2.5
            eye_z = pz - 6.0 * cos_o
            
            center_x = px
            center_y = py + 0.5
            center_z = pz + 5.0
            
            gluLookAt(eye_x, eye_y, eye_z, center_x, center_y, center_z, 0, 1, 0)
        
        draw_sky()
        
        glColor3f(0.0, 0.5, 0.0)            # Ground Field
        glBegin(GL_QUADS)
        glVertex3f(-10, -0.01, 0)
        glVertex3f(10, -0.01, 0)
        glVertex3f(10, -0.01, 150)
        glVertex3f(-10, -0.01, 150)
        glEnd()
        
        draw_track()
        draw_trees()
        draw_particles()
        draw_objects()
        
        for i in range(2):
            glPushMatrix()
            glTranslatef(*position[i])
            draw_car(car_colors[i])
            glPopMatrix()
    
    viewport_width = width // 2
    viewport_height = height
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, viewport_width, 0, viewport_height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    if not (all(game_finished) and current_level == 1):                 # Text drawing part
        
        glColor3f(*car_colors[player_id])
        player_text = f"Player {player_id + 1}"
        x_pos = 10
        y_pos = viewport_height - 20
        
        glRasterPos2f(x_pos, y_pos)
        
        for char in player_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        speed_text = f"Speed: {int(velocity[player_id] * 1000)}"
        glRasterPos2f(x_pos, y_pos - 20)
        for char in speed_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        health_text = f"Health: {int(health[player_id])}/5"
        glRasterPos2f(x_pos, y_pos - 60)
        for char in health_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        level_names = ["Sunny", "Rainy"]
        level_text = f"Level: {current_level + 1} ({level_names[current_level]})"
        glRasterPos2f(x_pos, y_pos - 40)
        for char in level_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        if game_finished[player_id] and current_level == 0:
            finish_text = "FINISHED! Press Enter"
            glColor3f(1, 1, 0)
            x_pos = viewport_width // 2 - 50
            y_pos = viewport_height // 2
            glRasterPos2f(x_pos, y_pos)
            for char in finish_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    if all(game_finished) and current_level == 1:
        show_overall_winner()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    if player_id == 1:      
        
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glColor3f(1, 1, 1)
        glBegin(GL_LINES)
        glVertex2f(width // 2, 0)
        glVertex2f(width // 2, height)
        glEnd()
        
        draw_pause_overlay()
        
        if all(game_finished) and current_level == 0:
            glColor3f(1, 1, 1)
            progression_text = "Press Enter for Next Level"
            text_width = len(progression_text) * 9
            x_pos = width // 2 - text_width // 2
            y_pos = height // 2
            glRasterPos2f(x_pos, y_pos)
            for char in progression_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        if all(game_finished) and current_level == 1:
            show_overall_winner()
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


def display():
    width = glutGet(GLUT_WINDOW_WIDTH)
    height = glutGet(GLUT_WINDOW_HEIGHT)
    draw_player_view(0, width, height)
    draw_player_view(1, width, height)
    glutSwapBuffers()


def reshape(width, height):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (width / 2) / height, 0.1, 200)
    glMatrixMode(GL_MODELVIEW)


def idle():
    update_physics()
    glutPostRedisplay()


def special_down(k, x, y):
    if k == GLUT_KEY_UP:
        keys['p2_accel'] = True
    elif k == GLUT_KEY_LEFT:
        keys['p2_left'] = True
    elif k == GLUT_KEY_RIGHT:
        keys['p2_right'] = True


def special_up(k, x, y):
    if k == GLUT_KEY_UP:
        keys['p2_accel'] = False
    elif k == GLUT_KEY_LEFT:
        keys['p2_left'] = False
    elif k == GLUT_KEY_RIGHT:
        keys['p2_right'] = False


def keyboard_down(k, x, y):
    global camera_mode, paused
    if k == b'c' or k == b'C':
        camera_mode[0] = (camera_mode[0] + 1) % 2
    elif k == b'v' or k == b'V':
        camera_mode[1] = (camera_mode[1] + 1) % 2
    elif k == b'w' or k == b'W':
        keys['p1_accel'] = True
    elif k == b'a' or k == b'A':
        keys['p1_left'] = True
    elif k == b'd' or k == b'D':
        keys['p1_right'] = True
    elif k == b'\r':
        keys['enter'] = True
    elif k == b'p' or k == b'P':
        paused = not paused


def keyboard_up(k, x, y):
    if k == b'w' or k == b'W':
        keys['p1_accel'] = False
    elif k == b'a' or k == b'A':
        keys['p1_left'] = False
    elif k == b'd' or k == b'D':
        keys['p1_right'] = False
    elif k == b'\r':
        keys['enter'] = False


def init():
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, 1500 / 900, 0.1, 500)
    glMatrixMode(GL_MODELVIEW)


def init_game():
    global current_level, start_delay_time
    current_level = 0
    set_level_properties(current_level)
    generate_track()
    generate_objects()
    generate_trees()
    start_delay_time = time.time()


def init_players():
    global position
    position[0][0] = -TRACK_WIDTH / 4
    position[1][0] = TRACK_WIDTH / 4


glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(1920, 1080)
glutCreateWindow(b"3D Car Racing Game")
init()
init_game()
init_players()
glutDisplayFunc(display)
glutReshapeFunc(reshape)
glutIdleFunc(idle)
glutSpecialFunc(special_down)
glutSpecialUpFunc(special_up)
glutKeyboardFunc(keyboard_down)
glutKeyboardUpFunc(keyboard_up)
glutMainLoop()