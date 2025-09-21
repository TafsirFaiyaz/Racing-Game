# Import required OpenGL libraries for 3D rendering and GLUT for window/input handling
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time


# --- GLOBAL STATE ---
# Define track width for the racing path
TRACK_WIDTH = 10.0

# Lists to store track control points, spline points, objects, particles, and trees
CONTROL_POINTS = []
SPLINE_POINTS = []
objects = []
particles = []
trees = []

# Game state variables
game_finished = [False, False]  # Tracks if each player has finished the race
current_level = 0  # Current level (0: Sunny, 1: Rainy, 2: Snowy)
countdown_state = None  # Countdown state: None, 3, 2, 1, 'GO!', 'racing'
finish_times = [None, None]

countdown_start_time = 0  # Timestamp when countdown starts
round_winners = []  # Stores winners of each round
level_completed = False  # Flag for level completion

level_complete_time = 0  # Timestamp when level is completed
paused = False  # Pause state for the game
health = [5.0, 5.0]  # Health for Player 1 and Player 2

# Car state for two players
position = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]  # Player positions (x, y, z)
orientation = [0.0, 0.0]  # Car orientations (radians)
velocity = [0.0, 0.0]  # Current speed for each player

top_speed = 0.3  # Base maximum speed
acceleration = 0.005  # Acceleration rate
base_handling = 0.06  # Base handling responsiveness

handling = [base_handling, base_handling]  # Current handling for each player
slippery_end_time = [0, 0]  # Time when slippery effect ends
BOOSTED_TOP_SPEED = top_speed * 2.0  # Boosted speed multiplier

max_speed = [top_speed, top_speed]  # Current max speed for each player
boost_end_time = [0, 0]  # Time when boost effect ends
car_colors = [(1, 0, 0), (0, 0, 1)]  # Colors: Red for P1, Blue for P2
camera_mode = [1, 1]  # Camera mode: 0 = first-person, 1 = third-person

# Input state for key presses
keys = {
    'p1_accel': False,  # Player 1 accelerate (W)
    'p1_left': False,   # Player 1 steer left (A)
    'p1_right': False,  # Player 1 steer right (D)
    'p2_accel': False,  # Player 2 accelerate (Up arrow)
    'p2_left': False,   # Player 2 steer left (Left arrow)
    'p2_right': False,  # Player 2 steer right (Right arrow)
    'enter': False,     # Enter key for advancing levels
    'restart': False    # R key for restarting game
}


def generate_track():
    """
    Generate a simple straight track along the z-axis using spline points.
    Stores points in SPLINE_POINTS list.
    """
    samples = 600
    SPLINE_POINTS.clear()
    
    for i in range(samples):
        t = i / float(samples)
        x = 0.0
        y = 0.0
        z = t * 150.0
        SPLINE_POINTS.append((x, y, z))


def generate_trees():
    """
    Generate trees on both sides of the track at random positions.
    Stores tree positions in the trees list.
    """
    trees.clear()
    num_trees_per_side = 30
    
    for _ in range(num_trees_per_side):
        z = random.uniform(0, 150)
        x_left = -6.0 + random.uniform(-1.0, 1.0)
        x_right = 6.0 + random.uniform(-1.0, 1.0)
        trees.append((x_left, 0.0, z))
        trees.append((x_right, 0.0, z))


# --- OBJECT PLACEMENT ---
def generate_objects():
    """
    Place objects (obstacles, boosts, etc.) randomly along the track.
    Stores objects in the objects list with type and position.
    """
    num_obs = 50
    num_boost = 10
    num_speed_down = 5
    num_slippery = 15
    objects.clear()
    
    N = len(SPLINE_POINTS)
    picks = random.sample(range(10, N - 10), num_obs + num_boost + num_speed_down + num_slippery)
    kinds = ['obs'] * num_obs + ['boost'] * num_boost + ['speed_down'] * num_speed_down + ['slippery'] * num_slippery
    random.shuffle(kinds)
    
    for idx, kind in zip(picks, kinds):
        x, y, z = SPLINE_POINTS[idx]
        x = random.uniform(-TRACK_WIDTH / 2 + 0.25, TRACK_WIDTH / 2 - 0.25)
        objects.append({'type': kind, 'pos': (x, y, z), 'active': True})


# --- DRAW ROUTINES ---
def draw_track():
    """
    Draw the track as a series of quads for the asphalt and white lines for boundaries.
    Includes dashed center line for visual guidance.
    """
    # Draw asphalt track
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.2, 0.2)  # Dark gray for asphalt
    
    for i in range(len(SPLINE_POINTS) - 1):
        x1, y1, z1 = SPLINE_POINTS[i]
        x2, y2, z2 = SPLINE_POINTS[i + 1]
        nx, nz = -1, 0  # Normal for flat track
        w = TRACK_WIDTH / 2
        
        glVertex3f(x1 + nx * w, y1, z1 + nz * w)
        glVertex3f(x1 - nx * w, y1, z1 - nz * w)
        glVertex3f(x2 - nx * w, y2, z2 - nz * w)
        glVertex3f(x2 + nx * w, y2, z2 + nz * w)
    
    glEnd()

    # Draw white side lines and dashed center line
    glColor3f(1.0, 1.0, 1.0)  # White color
    glLineWidth(2.0)
    glBegin(GL_LINES)
    
    for i in range(len(SPLINE_POINTS) - 1):
        z1 = SPLINE_POINTS[i][2]
        z2 = SPLINE_POINTS[i + 1][2]
        
        # Left side line
        glVertex3f(-4.8, 0.01, z1)
        glVertex3f(-4.8, 0.01, z2)
        
        # Right side line
        glVertex3f(4.8, 0.01, z1)
        glVertex3f(4.8, 0.01, z2)
        
        # Dashed center line
        if (i % 10) < 5:
            glVertex3f(0.0, 0.01, z1)
            glVertex3f(0.0, 0.01, z2)
    
    glEnd()
    glLineWidth(1.0)


def draw_cube():
    """
    Draw a simple cube for obstacles and other objects.
    """
    glBegin(GL_QUADS)
    vertices = [
        (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
        (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)
    ]
    faces = [
        (0, 1, 2, 3), (4, 5, 6, 7), (3, 2, 6, 7),
        (0, 1, 5, 4), (0, 3, 7, 4), (1, 2, 6, 5)
    ]
    
    for face in faces:
        for vertex in face:
            glVertex3f(*vertices[vertex])
    
    glEnd()


def draw_car(color):
    """
    Draw a car model with a body, cabin, and wheels.
    Args:
        color: RGB tuple for the car's body color
    """
    # Draw car body
    glColor3f(*color)
    glPushMatrix()
    glScalef(1.0, 0.3, 0.5)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Draw cabin
    glColor3f(0.7, 0.7, 1.0)
    glPushMatrix()
    glTranslatef(0.0, 0.35, 0.0)
    glScalef(0.5, 0.25, 0.3)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Draw wheels
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
    """
    Draw track objects (obstacles, boosts, speed-downs, slippery patches).
    """
    for obj in objects:
        if not obj['active']:
            continue
        
        x, y, z = obj['pos']
        glPushMatrix()
        glTranslatef(x, y + 0.01, z)
        
        if obj['type'] == 'obs':
            glColor3f(0.5, 0.5, 0.5)
            glScalef(0.25, 0.25, 0.25)
            draw_cube()
            
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
    """
    Draw a tree with a trunk and simple pyramid-shaped foliage.
    Args:
        x, y, z: Position of the tree
    """
    glPushMatrix()
    glTranslatef(x, y, z)
    
    # Draw trunk
    glColor3f(0.5, 0.35, 0.05)  # Brown
    glPushMatrix()
    glTranslatef(0, 0.5, 0)
    glScalef(0.2, 1.0, 0.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Draw foliage (pyramid shape using triangles)
    glColor3f(0.0, 0.6, 0.0)  # Dark green
    glBegin(GL_TRIANGLES)
    # Front
    glVertex3f(-1.0, 0.0, 0.0)
    glVertex3f(1.0, 0.0, 0.0)
    glVertex3f(0.0, 3.0, 0.0)
    # Back (corrected to avoid duplicate vertices)
    glVertex3f(1.0, 0.0, 0.0)
    glVertex3f(-1.0, 0.0, 0.0)
    glVertex3f(0.0, 3.0, 0.0)
    # Left
    glVertex3f(0.0, 0.0, -1.0)
    glVertex3f(0.0, 0.0, 1.0)
    glVertex3f(0.0, 3.0, 0.0)
    # Right
    glVertex3f(0.0, 0.0, 1.0)
    glVertex3f(0.0, 0.0, -1.0)
    glVertex3f(0.0, 3.0, 0.0)
    glEnd()
    
    glPopMatrix()


def draw_trees():
    """
    Draw all trees in the scene.
    """
    for tree_pos in trees:
        draw_tree(*tree_pos)


def draw_particles():
    """
    Draw weather particles (rain or snow) based on the current level.
    """
    if current_level == 1:  # Rainy level
        glColor3f(0.5, 0.5, 1.0)
        glBegin(GL_LINES)
        for p in particles:
            x, y, z = p['pos']
            glVertex3f(x, y, z)
            glVertex3f(x, y - 1.0, z)
        glEnd()
        
    elif current_level == 2:  # Snowy level
        glColor3f(1.0, 1.0, 1.0)
        glPointSize(3.0)
        glBegin(GL_POINTS)
        for p in particles:
            x, y, z = p['pos']
            glVertex3f(x, y, z)
            
        glEnd()
        glPointSize(1.0)


def draw_sun():
    """
    Draw a sun with rays for the sunny level.
    """
    glPushMatrix()
    glTranslatef(0, 15, 150)
    glColor3f(1.0, 1.0, 0.0)
    glutSolidSphere(2.0, 20, 20)
    glBegin(GL_LINES)
    
    for i in range(12):
        angle = math.radians(i * 30)
        x = math.cos(angle) * 4.0
        y = math.sin(angle) * 4.0
        glVertex3f(0, 0, 0)
        glVertex3f(x, y, 0)
    
    glEnd()
    glPopMatrix()


def draw_sky():
    """
    Draw a gradient sky background based on the current level.
    """
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    
    if current_level == 0:  # Sunny
        glColor3f(0.529, 0.808, 0.922)  # Light blue at top
        glVertex3f(-100, 100, -100)
        glVertex3f(100, 100, -100)
        glColor3f(0.678, 0.847, 0.902)  # Lighter blue at bottom
        glVertex3f(100, 0, -100)
        glVertex3f(-100, 0, -100)
        
    elif current_level == 1:  # Rainy
        glColor3f(0.4, 0.4, 0.4)  # Dark gray at top
        glVertex3f(-100, 100, -100)
        glVertex3f(100, 100, -100)
        glColor3f(0.6, 0.6, 0.6)  # Lighter gray at bottom
        glVertex3f(100, 0, -100)
        glVertex3f(-100, 0, -100)
        
    elif current_level == 2:  # Snowy
        glColor3f(0.7, 0.7, 0.7)  # Gray at top
        glVertex3f(-100, 100, -100)
        glVertex3f(100, 100, -100)
        glColor3f(0.9, 0.9, 0.9)  # Almost white at bottom
        glVertex3f(100, 0, -100)
        glVertex3f(-100, 0, -100)
    
    glEnd()
    glEnable(GL_DEPTH_TEST)


def draw_text(x, y, text):
    """
    Draw 2D text on the screen using GLUT bitmap characters.
    Args:
        x, y: Screen coordinates for text position
        text: String to display
    """
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


def draw_countdown():
    """
    Display the countdown timer (3, 2, 1, GO!) at the start of each level.
    Updates countdown_state based on elapsed time.
    """
    global countdown_state, countdown_start_time
    
    if countdown_state is None or countdown_state == 'racing':
        return
    
    current_time = time.time()
    elapsed = current_time - countdown_start_time
    
    if countdown_state == 3 and elapsed > 1:
        countdown_state = 2
        countdown_start_time = current_time
        
    elif countdown_state == 2 and elapsed > 1:
        countdown_state = 1
        countdown_start_time = current_time
        
    elif countdown_state == 1 and elapsed > 1:
        countdown_state = 'GO!'
        countdown_start_time = current_time
        
    elif countdown_state == 'GO!' and elapsed > 1:
        countdown_state = 'racing'
    
    if countdown_state != 'racing':
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, 800, 0, 600, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glColor3f(1, 1, 1)
        
        text = str(countdown_state) if countdown_state != 'GO!' else 'GO!'
        glRasterPos2f(400 - len(text) * 14 / 2, 300)
        
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


def draw_pause_overlay():
    """
    Display a 'PAUSED' overlay when the game is paused.
    """
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
    """
    Display the overall winner after all levels are completed.
    """
    p1_wins = round_winners.count(0)
    p2_wins = round_winners.count(1)
    winner_text = "Player 1 Won!" if p1_wins > p2_wins else "Player 2 Won!" if p2_wins > p1_wins else "It's a Tie!"
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    glOrtho(0, 800, 0, 600, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    
    glLoadIdentity()
    glColor3f(1, 1, 1)
    draw_text(400 - len(winner_text) * 9 / 2, 300, winner_text)
    draw_text(400 - len("Press R to Restart") * 7 / 2, 280, "Press R to Restart")
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# --- PHYSICS & COLLISION ---
def aabb_collide(min1, max1, min2, max2):
    """
    Check for collision between two axis-aligned bounding boxes.
    Args:
        min1, max1: Min and max coordinates of first box
        min2, max2: Min and max coordinates of second box
    Returns:
        Boolean indicating if the boxes intersect
    """
    return all(min1[i] < max2[i] and max1[i] > min2[i] for i in range(3))


def check_collisions(player_id):
    """
    Check for collisions between a player and track objects.
    Updates player state (health, speed, handling) based on collisions.
    Args:
        player_id: 0 for Player 1, 1 for Player 2
    """
    global velocity, max_speed, boost_end_time, handling, health
    
    cx, cy, cz = position[player_id]
    car_min = (cx - 0.1, cy - 0.1, cz - 0.1)
    car_max = (cx + 0.1, cy + 0.1, cz + 0.1)
    
    
    t = glutGet(GLUT_ELAPSED_TIME)
    opponent_id = 1 if player_id == 0 else 0
    
    
    for obj in objects:
        
        if not obj['active']:
            continue
        
        x, y, z = obj['pos']
        
        
        if obj['type'] == 'slippery':
            o_min = (x - 0.5, y - 0.1, z - 0.5)
            o_max = (x + 0.5, y + 0.1, z + 0.5)
            
        else:
            o_min = (x - 0.125, y - 0.125, z - 0.125)
            o_max = (x + 0.125, y + 0.125, z + 0.125)
        
        
        if aabb_collide(car_min, car_max, o_min, o_max):
            
            if obj['type'] == 'obs':
                
                health[player_id] -= 1.0
                max_speed[player_id] *= 0.9
                velocity[player_id] = 0.0
                
                if health[player_id] <= 0:
                    
                    health[player_id] = 0
                    max_speed[player_id] *= 0.1
                    
            elif obj['type'] == 'boost':
                
                max_speed[player_id] = BOOSTED_TOP_SPEED
                boost_end_time[player_id] = t + 2000
                
                
            elif obj['type'] == 'speed_down':
                velocity[opponent_id] *= 0.2
                
            elif obj['type'] == 'slippery':
                
                handling[player_id] = base_handling * 0.3
                slippery_end_time[player_id] = t + 2000
                
            obj['active'] = False
    
    if boost_end_time[player_id] and t > boost_end_time[player_id]:
        
        max_speed[player_id] = top_speed if health[player_id] > 0 else max_speed[player_id]
        boost_end_time[player_id] = 0
    
    if slippery_end_time[player_id] and t > slippery_end_time[player_id]:
        
        handling[player_id] = base_handling
        slippery_end_time[player_id] = 0


def check_car_collision():
    """
    Check for collisions between the two player cars.
    Randomly selects a loser to stop and pushes cars apart.
    """
    p1_x, p1_y, p1_z = position[0]
    p2_x, p2_y, p2_z = position[1]
    
    dx = p1_x - p2_x
    dz = p1_z - p2_z

    dist_squared = dx * dx + dz * dz
    
    if dist_squared < 0.04:
        
        loser = random.choice([0, 1])
        velocity[loser] = 0.0
        
        push_dir = 0.05 if dx < 0 else -0.05
        
        position[0][0] += push_dir
        position[1][0] -= push_dir


def update_physics():
    """
    Update game physics: car movement, collisions, and particle positions.
    Handles level completion and progression logic.
    """
    global position, velocity, game_finished, level_completed, level_complete_time, current_level, round_winners, countdown_state
    
    if paused or countdown_state != 'racing':
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
            
        else:
            
            velocity[player_id] -= acceleration / 2 if velocity[player_id] > 0 else 0
        
        velocity[player_id] = max(0, min(max_speed[player_id], velocity[player_id]))
        
        if keys[left_key]:
            
            position[player_id][0] += handling[player_id]
            
        if keys[right_key]:
            
            position[player_id][0] -= handling[player_id]
        
        new_x = max(-TRACK_WIDTH / 2 + 0.1, min(TRACK_WIDTH / 2 - 0.1, position[player_id][0]))
        
        
        if new_x != position[player_id][0]:
            velocity[player_id] *= 0.9
            
        position[player_id][0] = new_x
        position[player_id][2] += velocity[player_id]
        
        if position[player_id][2] >= 150.0:
            finish_times[player_id] = time.time()
            game_finished[player_id] = True
    
    if all(game_finished) and not level_completed:
        
        level_completed = True
        level_complete_time = glutGet(GLUT_ELAPSED_TIME)
        
        if finish_times[0] < finish_times[1]:
            round_winners.append(0)  
        elif finish_times[1] < finish_times[0]:
            round_winners.append(1)  
            
        else:
            round_winners.append(-1) # Tie
    
    if level_completed and keys['enter'] and current_level < 2:
        next_level()
    
    if level_completed and current_level == 2 and keys['restart']:
        restart_game()
    
    for p in particles:
        p['pos'][0] += p['vel'][0]
        p['pos'][1] += p['vel'][1]
        p['pos'][2] += p['vel'][2]
        
        
        avg_z = (position[0][2] + position[1][2]) / 2
        
        if p['pos'][1] < -1:
            
            p['pos'] = [random.uniform(-5, 5), 20, random.uniform(max(0, avg_z - 20), min(150, avg_z + 20))]
            
            if current_level == 1:
                p['vel'] = [0, random.uniform(-2.5, -1.5), 0]
                
            elif current_level == 2:
                p['vel'] = [random.uniform(-0.02, 0.02), random.uniform(-0.7, -0.3), random.uniform(-0.02, 0.02)]


# --- LEVEL MANAGEMENT ---
def set_level_properties(level):
    """
    Set properties (handling, particles) for the current level.
    Args:
        level: Integer (0: Sunny, 1: Rainy, 2: Snowy)
    """
    global base_handling, handling, particles
    
    if level == 0:
        base_handling = 0.06
        particles = []
        
    elif level == 1:
        
        base_handling = 0.03
        particles = [{'pos': [random.uniform(-10, 10), 20, random.uniform(-10, 10)],
                      'vel': [0, random.uniform(-1.0, -0.5), 0]} for _ in range(150)]
        
    elif level == 2:
        
        base_handling = 0.12
        particles = [{'pos': [random.uniform(-10, 10), 20, random.uniform(-10, 10)],
                      'vel': [random.uniform(-0.02, 0.02), random.uniform(-0.7, -0.3), random.uniform(-0.02, 0.02)]} for _ in range(150)]
    
    handling = [base_handling, base_handling]


def next_level():
    """
    Advance to the next level, resetting game state and generating new objects.
    """
    global current_level, game_finished, position, velocity, max_speed, boost_end_time, level_completed, countdown_state, countdown_start_time, health, slippery_end_time, finish_times
    
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
    
    countdown_state = 3
    countdown_start_time = time.time()


def restart_game():
    """
    Restart the entire game, resetting all levels and state.
    """
    global current_level, round_winners, countdown_state, countdown_start_time, health
    
    current_level = -1
    round_winners = []
    health = [5.0, 5.0]
    next_level()


# --- SPLIT SCREEN RENDERING ---
def setup_viewport(player_id, width, height):
    """
    Set up the viewport for split-screen rendering.
    Args:
        player_id: 0 for left side (Player 1), 1 for right side (Player 2)
        width, height: Window dimensions
    """
    if player_id == 0:
        glViewport(0, 0, width // 2, height)
        
    else:
        glViewport(width // 2, 0, width // 2, height)


def draw_player_view(player_id, width, height):
    """
    Render the view for a single player, including the track, cars, and HUD.
    Args:
        player_id: 0 for Player 1, 1 for Player 2
        width, height: Window dimensions
    """
    setup_viewport(player_id, width, height)
    
    # Set background color based on level
    if current_level == 0:
        glClearColor(0.529, 0.808, 0.922, 1.0)
        # Sunny
    elif current_level == 1:
        glClearColor(0.5, 0.5, 0.5, 1.0)
        # Rainy
    elif current_level == 2:
        glClearColor(0.8, 0.8, 0.8, 1.0) 
        # Snowy
    
    if player_id == 0:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
    else:
        glClear(GL_DEPTH_BUFFER_BIT)
    
    glLoadIdentity()
    px, py, pz = position[player_id]
    cos_o = math.cos(orientation[player_id])
    sin_o = math.sin(orientation[player_id])
    
    # Set up camera
    if camera_mode[player_id] == 0:  # First-person
        eye_x = px + 0.3 * sin_o
        eye_y = py + 0.1
        eye_z = pz + 0.3 * cos_o
        
        center_x = px + 0.8 * sin_o
        center_y = py + 0.1
        center_z = pz + 0.8 * cos_o
        
        gluLookAt(eye_x, eye_y, eye_z, center_x, center_y, center_z, 0, 1, 0)
    else:  # Third-person
        eye_x = px - 4.0 * sin_o
        eye_y = py + 2.5
        eye_z = pz - 6.0 * cos_o
        
        center_x = px
        center_y = py + 0.5
        center_z = pz + 5.0
        
        
        gluLookAt(eye_x, eye_y, eye_z, center_x, center_y, center_z, 0, 1, 0)
    
    # Draw scene components
    draw_sky()
    
    glColor3f(0.0, 0.5, 0.0)
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
    
    if current_level == 0:
        draw_sun()
    
    # Draw HUD
    viewport_width = width // 2
    viewport_height = height
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, viewport_width, 0, viewport_height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
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
    
    level_names = ["Sunny", "Rainy", "Snowy"]
    level_text = f"Level: {current_level + 1} ({level_names[current_level]})"
    glRasterPos2f(x_pos, y_pos - 40)
    
    for char in level_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    if game_finished[player_id] and current_level < 2:
        
        finish_text = "FINISHED! Press Enter"
        glColor3f(1, 1, 0)
        x_pos = viewport_width // 2 - 50
        y_pos = viewport_height // 2
        
        glRasterPos2f(x_pos, y_pos)
        for char in finish_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    # Draw center line and overlays for Player 2's view
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
        
        draw_countdown()
        draw_pause_overlay()
        
        if all(game_finished) and current_level < 2:
            
            glColor3f(1, 1, 1)
            progression_text = "Press Enter for Next Level"
            text_width = len(progression_text) * 9
            x_pos = width // 2 - text_width // 2
            y_pos = height // 2
            
            glRasterPos2f(x_pos, y_pos)
            for char in progression_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        if all(game_finished) and current_level == 2:
            show_overall_winner()
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


# --- GLUT CALLBACKS ---
def display():
    """
    Main display callback to render the split-screen views for both players.
    """
    width = glutGet(GLUT_WINDOW_WIDTH)
    height = glutGet(GLUT_WINDOW_HEIGHT)
    draw_player_view(0, width, height)
    draw_player_view(1, width, height)
    glutSwapBuffers()


def reshape(width, height):
    """
    Handle window resizing by updating the projection matrix.
    Args:
        width, height: New window dimensions
    """
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (width / 2) / height, 0.1, 200)
    glMatrixMode(GL_MODELVIEW)


def idle():
    """
    Idle callback to update physics and trigger redraw.
    """
    update_physics()
    glutPostRedisplay()


def special_down(k, x, y):
    """
    Handle special key presses (arrow keys) for Player 2.
    Args:
        k: Key code
        x, y: Mouse coordinates (unused)
    """
    if k == GLUT_KEY_UP:
        keys['p2_accel'] = True
    elif k == GLUT_KEY_LEFT:
        keys['p2_left'] = True
    elif k == GLUT_KEY_RIGHT:
        keys['p2_right'] = True


def special_up(k, x, y):
    """
    Handle special key releases for Player 2.
    Args:
        k: Key code
        x, y: Mouse coordinates (unused)
    """
    if k == GLUT_KEY_UP:
        keys['p2_accel'] = False
    elif k == GLUT_KEY_LEFT:
        keys['p2_left'] = False
    elif k == GLUT_KEY_RIGHT:
        keys['p2_right'] = False


def keyboard_down(k, x, y):
    """
    Handle keyboard presses for Player 1 and game controls.
    Args:
        k: Key code
        x, y: Mouse coordinates (unused)
    """
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
    elif k == b'r' or k == b'R':
        keys['restart'] = True
    elif k == b'p' or k == b'P':
        paused = not paused


def keyboard_up(k, x, y):
    """
    Handle keyboard releases for Player 1 and game controls.
    Args:
        k: Key code
        x, y: Mouse coordinates (unused)
    """
    if k == b'w' or k == b'W':
        keys['p1_accel'] = False
    elif k == b'a' or k == b'A':
        keys['p1_left'] = False
    elif k == b'd' or k == b'D':
        keys['p1_right'] = False
    elif k == b'\r':
        keys['enter'] = False
    elif k == b'p' or k == b'P':
        keys['restart'] = False


# --- INITIALIZATION ---
def init():
    """
    Initialize OpenGL settings for depth testing and projection.
    """
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, 1500 / 900, 0.1, 500)
    glMatrixMode(GL_MODELVIEW)


def init_game():
    """
    Initialize game state, track, objects, and countdown.
    """
    global current_level, countdown_state, countdown_start_time
    
    current_level = 0
    set_level_properties(current_level)

    generate_track()
    generate_objects()
    generate_trees()
    
    countdown_state = 3
    countdown_start_time = time.time()


def init_players():
    """
    Initialize player positions at the start of the track.
    """
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
