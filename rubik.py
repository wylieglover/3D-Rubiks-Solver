import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np

# Key bindings for rotations
rot_slice_map = {
    K_1: (0, 0, 1), K_2: (0, 1, 1), K_3: (0, 2, 1), K_4: (1, 0, 1), K_5: (1, 1, 1),
    K_6: (1, 2, 1), K_7: (2, 0, 1), K_8: (2, 1, 1), K_9: (2, 2, 1),
    K_F1: (0, 0, -1), K_F2: (0, 1, -1), K_F3: (0, 2, -1), K_F4: (1, 0, -1), K_F5: (1, 1, -1),
    K_F6: (1, 2, -1), K_F7: (2, 0, -1), K_F8: (2, 1, -1), K_F9: (2, 2, -1),
}  

# Cube colors
colors = (
    (1, 0, 0), # Red
    (0, 1, 0), # Green  
    (1, 0.5, 0), # Orange
    (1, 1, 0), # Yellow
    (1, 1, 1), # White
    (0, 0, 1) # Blue
)

# Cube vertices
vertices = (
    (1, -1, -1), (1,  1, -1), (-1,  1, -1), (-1, -1, -1),
    (1, -1,  1), (1,  1,  1), (-1, -1,  1), (-1,  1,  1)
)

# Cube edges for lines (3x3x3)
edges = (
    (0, 1),(0, 3),(0, 4),(2, 1),
    (2, 3),(2, 7),(6, 3),(6, 4),
    (6, 7),(5, 1),(5, 4),(5, 7)
)

# Cube surfaces for faces (3x3x3)
surfaces = (
    (0, 1, 2, 3), # Front
    (3, 2, 7, 6), # Right
    (6, 7, 5, 4), # Back
    (4, 5, 1, 0), # Left
    (1, 5, 7, 2), # Top
    (4, 0, 3, 6)  # Bottom
)

class Block():
    def __init__(self, id, n, scale):
        self.n = n
        self.scale = scale
        self.current_id = list(id)
        self.rot = np.identity(3)

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
        
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        if animate and self.isAffected(axis, slice, dir):
            glRotatef( angle*dir, *[1 if i==axis else 0 for i in range(3)] )
            
        glMultMatrixf(self.transformMat())
        
        for i, surface in enumerate(surfaces):
            glBegin(GL_QUADS)
            glColor3fv(colors[i])
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
    def __init__(self, n, scale):
        self.n = n
        cr = range(self.n)
        self.cubes = [Block((x, y, z), self.n, scale) for x in cr for y in cr for z in cr]
    
    def get_blocks(self):
        return self.cubes

def main():
    # Initialize pygame
    pygame.init()
    display = (800,600)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    clock = pygame.time.Clock()
   
    # Set perspective
    glEnable(GL_DEPTH_TEST) 
    glutInit()
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)

    # Initialize the cube
    cubes = Cube(3, 1.5)
    
    rot_x = 0
    rot_y = 0
    dragging = False
    last_pos = None
    
    animate = False
    action = (0, 0, 1)
    animate_ang = 0
    
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
        glTranslatef(0, 0, -40)
        glRotatef(rot_x, 1, 0, 0)
        glRotatef(rot_y, 0, 1, 0)
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

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

        clock.tick(60)  # Cap FPS at 60

if __name__ == '__main__':
    main()
    pygame.quit()
    quit()
