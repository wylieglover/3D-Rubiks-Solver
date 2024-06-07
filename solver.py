from tqdm import tqdm
import random
from pygame.locals import *

from rubik import Cube

rot_slice_map = {
    K_1: (0, 0, 1), K_2: (0, 1, 1), K_3: (0, 2, 1), K_4: (1, 0, 1), K_5: (1, 1, 1),
    K_6: (1, 2, 1), K_7: (2, 0, 1), K_8: (2, 1, 1), K_9: (2, 2, 1),
    K_F1: (0, 0, -1), K_F2: (0, 1, -1), K_F3: (0, 2, -1), K_F4: (1, 0, -1), K_F5: (1, 1, -1),
    K_F6: (1, 2, -1), K_F7: (2, 0, -1), K_F8: (2, 1, -1), K_F9: (2, 2, -1),
}  

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
