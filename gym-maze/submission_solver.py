import sys
import numpy as np
import math
import random
import json
import requests

from riddle_solvers import *

### the api calls must be modified by you according to the server IP communicated with you
#### students track --> 16.170.85.45
#### working professionals track --> 13.49.133.141
server_ip = '13.49.133.141'

def select_action(state):
    # This is a random agent 
    # This function should get actions from your trained agent when inferencing.
    actions = ['N', 'S', 'E', 'W']
    random_action = random.choice(actions)
    action_index = actions.index(random_action)
    return random_action, action_index


def move(agent_id, action):
    response = requests.post(f'http://{server_ip}:5000/move', json={"agentId": agent_id, "action": action})
    return response

def solve(agent_id,  riddle_type, solution):
    response = requests.post(f'http://{server_ip}:5000/solve', json={"agentId": agent_id, "riddleType": riddle_type, "solution": solution}) 
    print(response.json()) 
    return response

def get_obv_from_response(response):
    directions = response.json()['directions']
    distances = response.json()['distances']
    position = response.json()['position']
    obv = [position, distances, directions] 
    return obv

        
def submission_inference(riddle_solvers):

    response = requests.post(f'http://{server_ip}:5000/init', json={"agentId": agent_id})
    obv = get_obv_from_response(response)

    while(True):
        # Select an action
        state_0 = obv
        action = select_action(state_0) # Random action
        response = move(agent_id, action)
        if not response.status_code == 200:
            print(response)
            break

        obv = get_obv_from_response(response)
        print(response.json())

        if not response.json()['riddleType'] == None:
            solution = riddle_solvers[response.json()['riddleType']](response.json()['riddleQuestion'])
            response = solve(agent_id, response.json()['riddleType'], solution)


        # THIS IS A SAMPLE TERMINATING CONDITION WHEN THE AGENT REACHES THE EXIT
        # IMPLEMENT YOUR OWN TERMINATING CONDITION
        if np.array_equal(response.json()['position'], (9,9)):
            response = requests.post(f'http://{server_ip}:5000/leave', json={"agentId": agent_id})
            break


if __name__ == "__main__":
    
    agent_id = "9"
    riddle_solvers = {'cipher': cipher_solver, 'captcha': captcha_solver, 'pcap': pcap_solver, 'server': server_solver}
    submission_inference(riddle_solvers)
    