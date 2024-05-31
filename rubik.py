import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np
import random

# Defining directions for faces
RIGHT = (2, 1, 1)
LEFT = (0, 1, 1)
UP = (1, 2, 1)
DOWN = (1, 0, 1)
FRONT = (1, 1, 2)
BACK = (1, 1, 0)

# Defining colors for faces
face_colors = {
    FRONT: (1, 0.5, 0),  # Orange
    LEFT: (0, 1, 0),    # Yellow
    BACK:  (1, 0, 0),    # White
    RIGHT:  (1, 1, 0),    # Blue
    UP:    (1, 1, 1),    # Green
    DOWN:  (0, 0, 1)     # Red
}

color_map = {
    (1, 0.5, 0): 'O',  # Orange
    (0, 1, 0): 'Y',    # Yellow
    (1, 0, 0): 'W',    # White
    (1, 1, 0): 'B',    # Blue
    (1, 1, 1): 'G',    # Green
    (0, 0, 1): 'R',    # Red
    (0, 0, 0): 'X'     # Black

}

# Convert directions to position
def convert_directions_to_position(face1, face2, face3=None):
    x = face1[0]
    y = face1[1]
    z = face1[2]

    if face2 == LEFT or face3 == LEFT:
        x -= 1
    elif face2 == RIGHT or face3 == RIGHT:
        x += 1
    if face2 == UP or face3 == UP:
        y += 1
    elif face2 == DOWN or face3 == DOWN:
        y -= 1
    if face2 == FRONT or face3 == FRONT:
        z += 1
    elif face2 == BACK or face3 == BACK:
        z -= 1

    position = (x, y, z)
    return position

# Key bindings for rotations
rot_slice_map = {
    K_1: (0, 0, 1), K_2: (0, 1, 1), K_3: (0, 2, 1), K_4: (1, 0, 1), K_5: (1, 1, 1),
    K_6: (1, 2, 1), K_7: (2, 0, 1), K_8: (2, 1, 1), K_9: (2, 2, 1),
    K_F1: (0, 0, -1), K_F2: (0, 1, -1), K_F3: (0, 2, -1), K_F4: (1, 0, -1), K_F5: (1, 1, -1),
    K_F6: (1, 2, -1), K_F7: (2, 0, -1), K_F8: (2, 1, -1), K_F9: (2, 2, -1),
}  

# Cube vertices
vertices = np.array([
    (1, -1, -1), (1,  1, -1), (-1,  1, -1), (-1, -1, -1),
    (1, -1,  1), (1,  1,  1), (-1, -1,  1), (-1,  1,  1)
], dtype=np.float32)

# Cube edges for lines (3x3x3)
edges = np.array([
    (0, 1), (0, 3), (0, 4), (2, 1),
    (2, 3), (2, 7), (6, 3), (6, 4),
    (6, 7), (5, 1), (5, 4), (5, 7)
], dtype=np.int32)

# Cube surfaces for faces (3x3x3)
surfaces = np.array([
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
        self.colors = colors
    
    def __repr__(self):
        return f"{self.colors}"
    
    def update(self, axis, slice, dir):
        if not self.isAffected(axis, slice, dir):
            return
        
        i, j = (axis+1) % 3, (axis+2) % 3
        for k in range(3):
            self.rot[k][i], self.rot[k][j] = -self.rot[k][j]*dir, self.rot[k][i]*dir

        self.current_id[i], self.current_id[j] = (
            self.current_id[j] if dir < 0 else self.n - 1 - self.current_id[j],
            self.current_id[i] if dir > 0 else self.n - 1 - self.current_id[i] 
        )

    def transformMat(self):
        # Calculate the translation vector
        scaleA = [[s * self.scale for s in a] for a in self.rot]
        half_n = (self.n - 1) / 2
        scaleT = [(p - half_n) * 2 * self.scale for p in self.current_id]
        return [*scaleA[0], 0, *scaleA[1], 0, *scaleA[2], 0, *scaleT, 1]

    def isAffected(self, axis, slice, dir):
        return self.current_id[axis] == slice
    
    def draw(self, animate, angle, axis, slice, dir):
        glPushMatrix()

        if animate and self.isAffected(axis, slice, dir):
            glRotatef( angle*dir, *[1 if i==axis else 0 for i in range(3)] )
            
        glMultMatrixf(self.transformMat())
        
        glBegin(GL_QUADS)
        for face, surface in enumerate(surfaces):
            color = self.colors.get(face, (0, 0, 0))
            glColor3fv(color)
            for vertex in surface:
                glVertex3fv(vertices[vertex])
        glEnd()
        
        glColor3f(0, 0, 0)
        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()
        
        glPopMatrix()    

class Cube():
    def __init__(self, n, scale, state=None):
        # Initialize cube dimensions
        self.n = n
        self.state = state or "OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR"
        # Initialize face pieces
        self.faces = [
            Block(RIGHT, self.n, scale, {3: face_colors[RIGHT]}),
            Block(LEFT, self.n, scale, {1: face_colors[LEFT]}),
            Block(UP, self.n, scale, {4: face_colors[UP]}),
            Block(DOWN, self.n, scale, {5: face_colors[DOWN]}),
            Block(FRONT, self.n, scale, {2: face_colors[FRONT]}),
            Block(BACK, self.n, scale, {0: face_colors[BACK]})
        ]

        # Initialize edge pieces
        self.edges = [
            Block(convert_directions_to_position(FRONT, LEFT), self.n, scale, {2: face_colors[FRONT], 1: face_colors[LEFT]}),     # FRONT_LEFT
            Block(convert_directions_to_position(FRONT, RIGHT), self.n, scale, {2: face_colors[FRONT], 3: face_colors[RIGHT]}),    # FRONT_RIGHT
            Block(convert_directions_to_position(FRONT, UP), self.n, scale, {2: face_colors[FRONT], 4: face_colors[UP]}),       # FRONT_UP
            Block(convert_directions_to_position(FRONT, DOWN), self.n, scale, {2: face_colors[FRONT], 5: face_colors[DOWN]}),     # FRONT_DOWN
            Block(convert_directions_to_position(BACK, LEFT), self.n, scale, {0: face_colors[BACK], 1: face_colors[LEFT]}),      # BACK_LEFT
            Block(convert_directions_to_position(BACK, RIGHT), self.n, scale, {0: face_colors[BACK], 3: face_colors[RIGHT]}),     # BACK_RIGHT
            Block(convert_directions_to_position(BACK, UP), self.n, scale, {0: face_colors[BACK], 4: face_colors[UP]}),        # BACK_UP
            Block(convert_directions_to_position(BACK, DOWN), self.n, scale, {0: face_colors[BACK], 5: face_colors[DOWN]}),      # BACK_DOWN
            Block(convert_directions_to_position(LEFT, UP), self.n, scale, {1: face_colors[LEFT], 4: face_colors[UP]}),        # LEFT_UP
            Block(convert_directions_to_position(LEFT, DOWN), self.n, scale, {1: face_colors[LEFT], 5: face_colors[DOWN]}),      # LEFT_DOWN
            Block(convert_directions_to_position(RIGHT, UP), self.n, scale, {3: face_colors[RIGHT], 4: face_colors[UP]}),       # RIGHT_UP
            Block(convert_directions_to_position(RIGHT, DOWN), self.n, scale, {3: face_colors[RIGHT], 5: face_colors[DOWN]}),     # RIGHT_DOWN
        ]

        # Initialize corner pieces
        self.corners = [
            Block(convert_directions_to_position(FRONT, LEFT, DOWN), self.n, scale, {2: face_colors[FRONT], 1: face_colors[LEFT], 5: face_colors[DOWN]}),  # FRONT_LEFT_DOWN
            Block(convert_directions_to_position(FRONT, LEFT, UP), self.n, scale, {2: face_colors[FRONT], 1: face_colors[LEFT], 4: face_colors[UP]}),  # FRONT_LEFT_UP
            Block(convert_directions_to_position(FRONT, RIGHT, DOWN), self.n, scale, {2: face_colors[FRONT], 3: face_colors[RIGHT], 5: face_colors[DOWN]}),  # FRONT_RIGHT_DOWN
            Block(convert_directions_to_position(FRONT, RIGHT, UP), self.n, scale, {2: face_colors[FRONT], 3: face_colors[RIGHT], 4: face_colors[UP]}),  # FRONT_RIGHT_UP
            Block(convert_directions_to_position(BACK, LEFT, DOWN), self.n, scale, {0: face_colors[BACK], 1: face_colors[LEFT], 5: face_colors[DOWN]}),  # BACK_LEFT_DOWN
            Block(convert_directions_to_position(BACK, LEFT, UP), self.n, scale, {0: face_colors[BACK], 1: face_colors[LEFT], 4: face_colors[UP]}),  # BACK_LEFT_UP
            Block(convert_directions_to_position(BACK, RIGHT, DOWN), self.n, scale, {0: face_colors[BACK], 3: face_colors[RIGHT], 5: face_colors[DOWN]}),  # BACK_RIGHT_DOWN
            Block(convert_directions_to_position(BACK, RIGHT, UP), self.n, scale, {0: face_colors[BACK], 3: face_colors[RIGHT], 4: face_colors[UP]}),  # BACK_RIGHT_UP
        ]
        
        # Combine all blocks
        self.blocks = self.faces + self.edges + self.corners
        # print(self.blocks)

    def get_blocks(self):
        return self.blocks
    
    def get_color(self, id):
        for block in self.blocks:
            if block.current_id == id:
                return block.colors

    def stringify(self):
        """
        Input: None
        Description: Create string representation of the current state of the cube
        Output: string representing the cube current state
        """
        # Turn colors from self.colors into a single letter representing the color
        cube_str = ""

        # Iterate over the blocks in the cube
        print()
        print(self.blocks)
            # print(block.current_id, block.colors)

    def solved(self):
        # Check if the cube is solved
        for block in self.blocks:
            if not np.array_equal(block.current_id, block.original_id):
                return False
        return True


def main():
    # Initialize pygame
    pygame.init()
    display = (800,600)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
   
    # Set perspective
    glEnable(GL_DEPTH_TEST) 
    glutInit()
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (display[0] / display[1]), 1.0, 100.0)  # Adjust near and far planes
    
    # Initialize the cube
    cubes = Cube(3, 1)

    rot_x = 0
    rot_y = 0
    dragging = False
    last_pos = None
    
    animate = False
    animate_ang = 0
    action = (0, 0, 1)
    actions = []
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    dragging = True
                    last_pos = event.pos
            if event.type == KEYDOWN:
                if not animate and event.key in rot_slice_map:
                    animate, action = True, rot_slice_map[event.key]  
                if event.key == K_SPACE:
                    # Scramble cube
                    actions = [random.choice(list(rot_slice_map.values())) for _ in range(20)]     
                if event.key == K_s:
                    # Solve cube
                    pass
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    dragging = False
            if event.type == pygame.MOUSEMOTION:
                if dragging:
                    dx, dy = event.pos[0] - last_pos[0], event.pos[1] - last_pos[1]
                    rot_x += dy * 0.1
                    rot_y += dx * 0.1
                    last_pos = event.pos
            
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -30)
        glRotatef(rot_x, 1, 0, 0)
        glRotatef(rot_y, 0, 1, 0)
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        # cubes.stringify()
        # print(cubes.get_color([2, 2, 2]))

        if not animate and actions:
            animate, animate_ang = True, 0
            action = actions.pop(0)
        
        if animate:
            if animate_ang >= 90:
                for cube in cubes.get_blocks():
                    cube.update(*action)
                animate, animate_ang = False, 0
                
        for cube in cubes.get_blocks():
            cube.draw(animate, animate_ang, *action)
        if animate:
            animate_ang += 5
        
        pygame.display.flip()

if __name__ == '__main__':
    main()
    pygame.quit()
    quit()
