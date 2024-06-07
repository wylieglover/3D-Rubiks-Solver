import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np
import random
import string
from tqdm import tqdm
import json
import time
# Convert directions to position
def convert_directions_to_position(face1, face2, face3=None):
    face_changes = {
        LEFT: (-1, 0, 0),
        RIGHT: (1, 0, 0),
        UP: (0, 1, 0),
        DOWN: (0, -1, 0),
        FRONT: (0, 0, 1),
        BACK: (0, 0, -1),
    }

    x, y, z = face1
    for face in (face2, face3):
        if face:
            dx, dy, dz = face_changes[face]
            x += dx
            y += dy
            z += dz

    return x, y, z

# Defining directions for faces
RIGHT = (2, 1, 1)
LEFT = (0, 1, 1)
UP = (1, 2, 1)
DOWN = (1, 0, 1)
FRONT = (1, 1, 2)
BACK = (1, 1, 0)

# Defining colors for faces
WHITE, GREEN, ORANGE, YELLOW, RED, BLUE = 'W', 'G', 'O', 'Y', 'R', 'B'
color_map = {
    WHITE: (1, 1, 1),
    GREEN: (0, 1, 0),
    ORANGE: (1, 0.5, 0),
    YELLOW: (1, 1, 0),
    RED: (1, 0, 0),
    BLUE: (0, 0, 1),
    None: (0, 0, 0)
}

# Key bindings for rotations
rot_slice_map = {
    K_1: (0, 0, 1), K_2: (0, 1, 1), K_3: (0, 2, 1), K_4: (1, 0, 1), K_5: (1, 1, 1),
    K_6: (1, 2, 1), K_7: (2, 0, 1), K_8: (2, 1, 1), K_9: (2, 2, 1),
    K_F1: (0, 0, -1), K_F2: (0, 1, -1), K_F3: (0, 2, -1), K_F4: (1, 0, -1), K_F5: (1, 1, -1),
    K_F6: (1, 2, -1), K_F7: (2, 0, -1), K_F8: (2, 1, -1), K_F9: (2, 2, -1),
}  

# Cube vertices
VERTICES: np.ndarray = np.array([
    (1, -1, -1), (1,  1, -1), (-1,  1, -1), (-1, -1, -1),
    (1, -1,  1), (1,  1,  1), (-1, -1,  1), (-1,  1,  1)
], dtype=np.float32)

# Cube edges for lines (3x3x3)
EDGES: np.ndarray = np.array([
    (0, 1), (0, 3), (0, 4), (2, 1),
    (2, 3), (2, 7), (6, 3), (6, 4),
    (6, 7), (5, 1), (5, 4), (5, 7)
], dtype=np.int32)

# Cube surfaces for faces (3x3x3)
SURFACES: np.ndarray = np.array([
    (0, 1, 2, 3),  # Back
    (3, 2, 7, 6),  # Left
    (6, 7, 5, 4),  # Front
    (4, 5, 1, 0),  # Right
    (1, 5, 7, 2),  # Top
    (4, 0, 3, 6)   # Bottom
], dtype=np.int32)

class Block():
    def __init__(self, id, n, scale, colors):
        self.n = n
        self.scale = scale
        self.current_id = list(id)
        self.original_id = list(id)
        self.rot = np.identity(3)
        self.colors = list(colors)

    def update(self, axis, slice, dir):
        if not self.isAffected(axis, slice, dir):
            return

        i, j = (axis+1) % 3, (axis+2) % 3
    
        if dir > 0:
            self.colors[i], self.colors[j] = self.colors[j], self.colors[i]
        else:
            self.colors[j], self.colors[i] = self.colors[i], self.colors[j]

        self.current_id[i], self.current_id[j] = (
            self.current_id[j] if dir < 0 else self.n - 1 - self.current_id[j],
            self.current_id[i] if dir > 0 else self.n - 1 - self.current_id[i] 
        )
        
    def transformMat(self):
        scaled_rot = [[s * self.scale for s in row] for row in self.rot]
        half_n = (self.n - 1) / 2
        translation = (np.array(self.current_id) - half_n) * 2 * self.scale

        transformation_matrix = [
            [*scaled_rot[0], 0],
            [*scaled_rot[1], 0],
            [*scaled_rot[2], 0],
            [*translation, 1]
        ]
        return transformation_matrix

    def isAffected(self, axis, slice, dir):
        return self.current_id[axis] == slice
    
    def draw(self, animate: bool, angle: float, axis: int, slice: int, dir: int):
        if self.current_id == [1, 1, 1]:
            return

        glPushMatrix()

        if animate and self.isAffected(axis, slice, dir):
            glRotatef(angle * dir, *[1 if i == axis else 0 for i in range(3)])
        
        glMultMatrixf(self.transformMat())
        self.draw_stickers()
        
        glPopMatrix()
    
    def draw_stickers(self):
        face_color_map = {
            0: self.colors[2],  # BACK face (z- direction)
            1: self.colors[0],  # LEFT face (x- direction)
            2: self.colors[2],  # FRONT face (z+ direction)
            3: self.colors[0],  # RIGHT face (x+ direction)
            4: self.colors[1],  # UP face (y+ direction)
            5: self.colors[1]   # DOWN face (y- direction)
        }

        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POLYGON_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
        
        glBegin(GL_QUADS)
        for face, surface in enumerate(SURFACES):
            color_key = face_color_map.get(face)
            if color_key:
                color = color_map.get(color_key, (0, 0, 0))
                glColor3fv(color)
            for vertex in surface:
                glVertex3fv(VERTICES[vertex])
        glEnd()
        
        glColor3f(0, 0, 0)
        glBegin(GL_LINES)
        for edge in EDGES:
            for vertex in edge:
                glVertex3fv(VERTICES[vertex])
        glEnd()

class Cube():
    def __init__(self, n, scale, state=None):
        self.n = n
        self.scale = scale
        self.state = state

        state = "".join(x for x in state if x not in string.whitespace)
        assert len(state) == 54

        # Initialize face blocks
        self.faces = (
            Block(RIGHT, self.n, scale, (state[28], None, None)),
            Block(LEFT, self.n, scale, (state[22], None, None)),
            Block(UP, self.n, scale, (None, state[4], None)),
            Block(DOWN, self.n, scale, (None, state[49], None)),
            Block(FRONT, self.n, scale, (None, None, state[25])),
            Block(BACK, self.n, scale, (None, None, state[31]))
        )

        # Initialize edge blocks
        self.edges = (
            Block(convert_directions_to_position(FRONT, LEFT), self.n, scale, (state[23], None, state[24])),     
            Block(convert_directions_to_position(FRONT, RIGHT), self.n, scale, (state[27], None, state[26])),  
            Block(convert_directions_to_position(FRONT, UP), self.n, scale, (None, state[7], state[13])),     
            Block(convert_directions_to_position(FRONT, DOWN), self.n, scale, (None, state[46], state[37])),    
            Block(convert_directions_to_position(BACK, LEFT), self.n, scale, (state[21], None, state[32])),     
            Block(convert_directions_to_position(BACK, RIGHT), self.n, scale, (state[29], None, state[30])),    
            Block(convert_directions_to_position(BACK, UP), self.n, scale, (None, state[1], state[19])),       
            Block(convert_directions_to_position(BACK, DOWN), self.n, scale, (None, state[52], state[43])),     
            Block(convert_directions_to_position(LEFT, UP), self.n, scale, (state[10], state[3], None)),       
            Block(convert_directions_to_position(LEFT, DOWN), self.n, scale, (state[34], state[48], None)),     
            Block(convert_directions_to_position(RIGHT, UP), self.n, scale, (state[16], state[5], None)),     
            Block(convert_directions_to_position(RIGHT, DOWN), self.n, scale, (state[40], state[50], None)),    
        )

        # Initialize corner blocks
        self.corners = (
            Block(convert_directions_to_position(FRONT, LEFT, DOWN), self.n, scale, (state[35], state[45], state[36])), 
            Block(convert_directions_to_position(FRONT, LEFT, UP), self.n, scale, (state[11], state[6], state[12])),  
            Block(convert_directions_to_position(FRONT, RIGHT, DOWN), self.n, scale, (state[39], state[47], state[38])), 
            Block(convert_directions_to_position(FRONT, RIGHT, UP), self.n, scale, (state[15], state[8], state[14])), 
            Block(convert_directions_to_position(BACK, LEFT, DOWN), self.n, scale, (state[33], state[51], state[44])),  
            Block(convert_directions_to_position(BACK, LEFT, UP), self.n, scale, (state[9], state[0], state[20])),  
            Block(convert_directions_to_position(BACK, RIGHT, DOWN), self.n, scale, (state[41], state[53], state[42])), 
            Block(convert_directions_to_position(BACK, RIGHT, UP), self.n, scale, (state[17], state[2], state[18])), 
        )
        
        # Combine all blocks
        self.blocks = self.faces + self.edges + self.corners

    def get_blocks(self):
        return self.blocks

    def get_color_list(self):
        self.front = [p.colors[2] for p in sorted(self._face(FRONT), key=lambda p: (-p.current_id[1], p.current_id[0])) if p.colors[2] is not None]
        self.back = [p.colors[2] for p in sorted(self._face(BACK), key=lambda p: (-p.current_id[1], -p.current_id[0])) if p.colors[2] is not None] 
        self.up = [p.colors[1] for p in sorted(self._face(UP), key=lambda p: (p.current_id[2], p.current_id[0])) if p.colors[1] is not None] 
        self.down = [p.colors[1] for p in sorted(self._face(DOWN), key=lambda p: (-p.current_id[2], p.current_id[0])) if p.colors[1] is not None] 
        self.right = [p.colors[0] for p in sorted(self._face(RIGHT), key=lambda p: (-p.current_id[1], -p.current_id[2])) if p.colors[0] is not None]
        self.left = [p.colors[0] for p in sorted(self._face(LEFT), key=lambda p: (-p.current_id[1], p.current_id[2])) if p.colors[0] is not None] 
  
        return "".join(self.up + self.left[0:3] + self.front[0:3] + self.right[0:3] + self.back[0:3]
                + self.left[3:6] + self.front[3:6] + self.right[3:6] + self.back[3:6]
                + self.left[6:9] + self.front[6:9] + self.right[6:9] + self.back[6:9] + self.down)
    
    def _face(self, axis):
        if axis == LEFT:
            return [b for b in self.blocks if b.current_id[0] == 0]
        elif axis == RIGHT:
            return [b for b in self.blocks if b.current_id[0] == 2]
        elif axis == UP:
            return [b for b in self.blocks if b.current_id[1] == 2]
        elif axis == DOWN:
            return [b for b in self.blocks if b.current_id[1] == 0]
        elif axis == FRONT:
            return [b for b in self.blocks if b.current_id[2] == 2]
        elif axis == BACK:
            return [b for b in self.blocks if b.current_id[2] == 0]
        else:
            raise ValueError("Invalid axis value")
       
    def apply_move(self, axis, slice, dir):
        for block in self.blocks:
            block.update(axis, slice, dir)
            
    def solved(self):
        return self.state == self.solved_state()
    
    def solved_state(self):
        return "OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR"  # Placeholder
    
class RubiksCubeSolver:
    def __init__(self, heuristic=None, threshold=20):
        self.heuristic = heuristic or {}
        self.max_depth = threshold
        self.threshold = threshold
        self.min_threshold = None
        self.moves = []

    def search(self, state, g_score):
        cube = Cube(3, 1, state=state)
        if cube.solved():
            return True
        elif len(self.moves) >= self.threshold:
            return False
        
        min_bound = float('inf')
        best_action = None
        for move in rot_slice_map.values():
            new_cube = Cube(3, 1, state=state)
            new_cube.apply_move(*move)
            if new_cube.solved():
                self.moves.append(move)
                return True
            
            next_state = new_cube.get_color_list()
            h_score = self.heuristic.get(next_state, self.max_depth)
            f_score = g_score + h_score

            if f_score < min_bound:
                min_bound = f_score
                best_action = [(next_state, move)]
            elif f_score == min_bound:
                if best_action is None:
                    best_action = [(next_state, move)]
                else:
                    best_action.append((next_state, move))
        
        if best_action is not None:
            if self.min_threshold is None or min_bound < self.min_threshold:
                self.min_threshold = min_bound
            next_action = random.choice(best_action)
            self.moves.append(next_action[1])
            status = self.search(next_action[0], g_score + 1)
            if status: return status
        return False
    
    def solve(self, state):
        while True:
            if self.search(state, 1):
                return self.moves
            self.moves = []
            self.threshold = self.min_threshold
        return []

def heuristic(state, actions=rot_slice_map.values(), max_moves=4, heuristic=None):
    if heuristic is None:
        heuristic = {state: 0}
    que = [(state, 0)]
    node_count = sum([len(actions) ** (x + 1) for x in range(max_moves + 1)])
    with tqdm(total=node_count, desc='Heuristic DB') as pbar:
        while True:
            if not que:
                break
            s, d = que.pop()
            if d > max_moves:
                continue
            for move in actions: 
                new_cube = Cube(3, 1, state=s) 
                new_cube.apply_move(*move) 
                new_state = new_cube.get_color_list()
                if new_state not in heuristic or heuristic[new_state] > d + 1:
                    heuristic[new_state] = d + 1
                que.append((new_state, d + 1))
                pbar.update(1)
    return heuristic

# Main loop
def main():
    # Initialize pygame
    pygame.init()
    display = (800,600)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    pygame.display.set_caption("Cubussi")

    # Set perspective
    glEnable(GL_DEPTH_TEST) 
    glutInit()
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (display[0] / display[1]), 1.0, 100.0)
    
    # Initialize Rubiks Cube
    cube = Cube(3, 1, "OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR")

    # Variables for rotating and moving with mouse
    rot_x = 0
    rot_y = 0
    dragging = False
    last_pos = None
    animate = False
    animate_ang = 0
    action = (0, 0, 1)
    actions = []

    # Game loop
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    dragging = True
                    last_pos = event.pos
            if event.type == KEYDOWN:
                if not animate and event.key in rot_slice_map:
                    animate, action = True, rot_slice_map[event.key]  
                if event.key == K_SPACE:
                    actions = [random.choice(list(rot_slice_map.values())) for _ in range(5)] # Scrambles blocks   
                if event.key == K_s and not animate:
                    start_time = time.time()
                    print("Initializing solving algorithm...")
                    if os.path.exists('heuristic.json'):
                        print("Heuristics found locally...")
                        with open('heuristic.json') as f:
                            h_db = json.load(f)
                    else:
                        print("Gathering heuristics...")
                        h_db = heuristic(cube.get_color_list())
                        print("Generating JSON file...")
                        with open('heuristic.json', 'w', encoding='utf-8') as f:
                            json.dump(
                                h_db,
                                f,
                                ensure_ascii=False,
                                indent=4
                            )
                        print("JSON file generated!")   
                    solver = RubiksCubeSolver(h_db)
                    print("Searching for moves...")
                    actions = solver.solve(cube.get_color_list())
                    if actions:
                        print("Moves to solve:", actions)
                    else:
                        print("Solving cube filed: cube already solved.")
                    elapsed_time = round(time.time() - start_time, 2)
                    print("Time taken to solve:", elapsed_time, "seconds\n")
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            if event.type == pygame.MOUSEMOTION:
                if dragging:
                    dx, dy = event.pos[0] - last_pos[0], event.pos[1] - last_pos[1]
                    rot_x += dy * 0.1
                    rot_y += dx * 0.1
                    last_pos = event.pos
            
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -20)
        glRotatef(rot_x, 1, 0, 0)
        glRotatef(rot_y, 0, 1, 0)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        if not animate and actions:
            animate, animate_ang = True, 0
            action = actions.pop(0)
        
        if animate:
            if animate_ang >= 90:
                for block in cube.get_blocks():
                    block.update(*action)
                animate, animate_ang = False, 0
                
        for block in cube.get_blocks():
            block.draw(animate, animate_ang, *action)
        if animate:
            animate_ang += 5
        pygame.display.flip()

if __name__ == '__main__':
    main()
    pygame.quit()
    quit()
