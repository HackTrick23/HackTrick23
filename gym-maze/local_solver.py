import sys
import numpy as np
import math
import random
import json
import requests

import gym
import gym_maze
from gym_maze.envs.maze_manager import MazeManager
from riddle_solvers import *

def select_action(state):
    # This is a random agent 
    # This function should get actions from your trained agent when inferencing.
    actions = ['N', 'S', 'E', 'W']
    random_action = random.choice(actions)
    action_index = actions.index(random_action)
    return random_action, action_index


def local_inference(riddle_solvers):

    obv = manager.reset(agent_id)

    for t in range(MAX_T):
        # Select an action
        state_0 = obv
        action, action_index = select_action(state_0) # Random action
        obv, reward, terminated, truncated, info = manager.step(agent_id, action)

        if not info['riddle_type'] == None:
            solution = riddle_solvers[info['riddle_type']](info['riddle_question'])
            obv, reward, terminated, truncated, info = manager.solve_riddle(info['riddle_type'], agent_id, solution)

        # THIS IS A SAMPLE TERMINATING CONDITION WHEN THE AGENT REACHES THE EXIT
        # IMPLEMENT YOUR OWN TERMINATING CONDITION
        if np.array_equal(obv[0], (9,9)):
            manager.set_done(agent_id)
            break # Stop Agent

        if RENDER_MAZE:
            manager.render(agent_id)

        states[t] = [obv[0].tolist(), action_index, str(manager.get_rescue_items_status(agent_id))]       
        


if __name__ == "__main__":

    sample_maze = np.load("hackathon_sample.npy")
    agent_id = "9" # add your agent id here
    
    manager = MazeManager()
    manager.init_maze(agent_id, maze_cells=sample_maze)
    env = manager.maze_map[agent_id]

    riddle_solvers = {'cipher': cipher_solver, 'captcha': captcha_solver, 'pcap': pcap_solver, 'server': server_solver}
    maze = {}
    states = {}

    
    maze['maze'] = env.maze_view.maze.maze_cells.tolist()
    maze['rescue_items'] = list(manager.rescue_items_dict.keys())

    MAX_T = 5000
    RENDER_MAZE = True
    

    local_inference(riddle_solvers)

    with open("./states.json", "w") as file:
        json.dump(states, file)

    
    with open("./maze.json", "w") as file:
        json.dump(maze, file)
    