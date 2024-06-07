import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import json
import time

from rubik import Cube
from solver import RubiksCubeSolver, heuristic, rot_slice_map


HEURISTIC_MAX_MOVES = 3
INITIAL_STATE = "OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR"

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
    cube = Cube(3, 1, state=INITIAL_STATE)

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
                    actions = [random.choice(list(rot_slice_map.values())) for _ in range(10)] # Scrambles blocks   
                if event.key == K_s and not animate:
                    start_time = time.time()
                    print("Initializing solving algorithm...")
                    if os.path.exists('heuristic.json'):
                        print("Heuristics found locally...")
                        with open('heuristic.json') as f:
                            h_db = json.load(f)
                    else:
                        print("Gathering heuristics...")
                        h_db = heuristic(cube.get_color_list(), max_moves=HEURISTIC_MAX_MOVES)
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
    