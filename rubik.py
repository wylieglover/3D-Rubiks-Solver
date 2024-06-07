from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np
import string

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

class Cube:
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
        def check(colors):
            assert len(colors) == 9
            return all(c == colors[0] for c in colors)
        return (check([block.colors[2] for block in self._face(FRONT)]) and
                check([block.colors[2] for block in self._face(BACK)]) and
                check([block.colors[1] for block in self._face(UP)]) and
                check([block.colors[1] for block in self._face(DOWN)]) and
                check([block.colors[0] for block in self._face(LEFT)]) and
                check([block.colors[0] for block in self._face(RIGHT)]))
    