import gym
import time
import random
import numpy as np
import copy
from gym_maze.envs import MazeEnv
import os, random
import requests
import json


class MazeManager():
    def __init__(self, maze_size=10):
        self.maze_size = maze_size
        self.maze_map= dict() #### mapping agent id to Maze Env Object
        self.riddles_dict= dict() ##### dictionary to map agent id to RiddleContainer object
        self.rescue_items_dict = dict() ### map rescue item position to riddle_type
        self.randomize_rescue_items()
        self.riddle_scores = {"cipher": 20, "server": 30, "pcap": 40, "captcha": 10}
    ## end init

    def init_maze(self, agent_id, maze_cells=None):
        if(hasattr(maze_cells, 'shape')):
            env = gym.make('maze-sample-10x10-v0', rescue_item_locations= list(self.rescue_items_dict.keys()), maze_cells=maze_cells, enable_render=True)
            self.maze_map[agent_id] = env
            state = self.maze_map[agent_id].reset()
            env = None
            self.init_riddles(agent_id)
            return state
        else:
            raise Exception('Enter a Numpy array!')
            
    ### end init maze

    def init_riddles(self, agent_id):
        self.riddles_dict[agent_id] = RiddleContainer()
        return
    ## end init riddles

    def pull_riddle(self, riddle_type, agent_id):
        riddle = self.riddles_dict[agent_id].get_riddle(riddle_type)
        question = riddle.get_question()
        return question
    
    def solve_riddle(self, riddle_type, agent_id, solution):
        robot = self.maze_map[agent_id].maze_view.robot
        actual_riddle_type = self.rescue_items_dict.get(tuple(robot), None)
        if actual_riddle_type==None:
            print("no riddle here")
            print()
            return self.maze_map[agent_id].get_current_state()
        
        
        riddle = self.riddles_dict[agent_id].get_riddle(actual_riddle_type)
        
        if(riddle_type==actual_riddle_type):
            
            if not riddle.solved():
                riddle.solve_riddle(solution)
                
                if riddle.solved():
                    print(riddle_type)
                    print("riddle solved")
                    if not self.maze_map[agent_id].maze_view.maze.get_rescue_item(tuple(robot)).rescued:
                        self.maze_map[agent_id].maze_view.maze.get_rescue_item(tuple(robot)).rescued = True
                        print("rescued")
                        print()
                        self.maze_map[agent_id].maze_view.increment_rescue_items()
                else:
                    print("riddle failed")
                    print(riddle_type)
                    self.maze_map[agent_id].maze_view.maze.get_rescue_item(tuple(robot)).rescued = True
                    print("rescue item nulled")
                    print()
        
        elif riddle.attempts==0:
            print("wrong riddle type")
            print(riddle.attempts)
            self.maze_map[agent_id].maze_view.maze.get_rescue_item(tuple(robot)).rescued = True
            riddle.attempts+=1
            print("rescue item nulled")
            print()
            
        


        return self.maze_map[agent_id].get_current_state()
        
        

    def randomize_rescue_items(self):
        riddle_types = ['server', 'cipher', 'pcap', 'captcha']
        random.shuffle(riddle_types)

        for riddle_type in riddle_types:
            position = (random.randrange(0, self.maze_size-1), random.randrange(0, self.maze_size-1))
            while(position==(0,0) or position==(9,9)):
                position = (random.randrange(0, self.maze_size-1), random.randrange(0, self.maze_size-1))
                
            self.rescue_items_dict[position] = riddle_type
    ## end randomize rescue items

    def step(self, agent_id, action):
        obv, reward, terminated, truncated, info = self.maze_map[agent_id].step(action)
        if tuple(obv[0]) in self.rescue_items_dict:
            riddle_type = self.rescue_items_dict[tuple(obv[0])]
            riddle = self.riddles_dict[agent_id].get_riddle(riddle_type)
            if not riddle.solved() and riddle.attempts==0:
                question = self.pull_riddle(riddle_type, agent_id)
                info['riddle_type'] = riddle_type
                info['riddle_question'] = question


        return obv, reward, terminated, truncated, info

        
    ## end step
    
    def reset(self, agent_id):
        if agent_id in self.maze_map:
            self.riddles_dict[agent_id].reset_riddles()
            return self.maze_map[agent_id].reset()
        else:
            raise('Agent Not Found')

    def get_action_space(self, agent_id):
        if agent_id in self.maze_map:
            return self.maze_map[agent_id].action_space
        else:
            raise('Agent Not Found')
        
    def get_observation_space(self, agent_id):
        if agent_id in self.maze_map:
            return self.maze_map[agent_id].observation_space
        else:
            raise('Agent Not Found')

    def is_game_over(self, agent_id):
        if agent_id in self.maze_map:
            return self.maze_map[agent_id].maze_view.game_over
        else:
            raise('Agent Not Found')

    
    def render(self, agent_id, mode="human", close=False):
        if agent_id in self.maze_map:
            if close:
                self.maze_map[agent_id].maze_view.quit_game()

            return self.maze_map[agent_id].maze_view.update(mode)
        else:
            raise('Agent Not Found')

    def set_done(self, agent_id):
        if agent_id in self.maze_map:
            self.maze_map[agent_id].terminated = True
        else:
            raise('Agent Not Found')
        
    def calculate_final_score(self, agent_id,riddlesTimeDictionary):
        rescue_score = (1000*self.maze_map[agent_id].maze_view.rescued_items)/(self.maze_map[agent_id].steps)
        riddles_score = 0
        riddles_score_dict = dict()
        for riddle in self.riddles_dict[agent_id].riddles.values():
            riddle_score = self.riddle_scores[riddle.riddle_type]*riddle.solved()
            if riddle_score > 0:
                riddle_score = riddle_score / (riddlesTimeDictionary.get(riddle.riddle_type,1)*100)
            riddles_score += riddle_score
            riddles_score_dict[riddle.riddle_type] = riddle_score
            
        total_score = (rescue_score + riddles_score)
        if(not tuple(self.maze_map[agent_id].maze_view.robot)==(9,9) or not self.maze_map[agent_id].terminated):
            total_score = 0.8 * total_score
        
        return total_score, riddles_score_dict
    
    def calculate_current_score(self, agent_id):
        rescue_score = (1000*self.maze_map[agent_id].maze_view.rescued_items)/(self.maze_map[agent_id].steps)
        riddles_score = 0
        riddles_score_dict = dict()
        for riddle in self.riddles_dict[agent_id].riddles.values():
            riddle_score = self.riddle_scores[riddle.riddle_type]*riddle.solved()
            riddles_score += riddle_score
            riddles_score_dict[riddle.riddle_type] = riddle_score
            
        total_score = (rescue_score + riddles_score)
        
        return total_score, riddles_score_dict
    
    def get_rescue_items_status(self, agent_id):
        riddles = self.riddles_dict[agent_id].riddles
        rescue_items_status = dict()
        
        for position,riddle_type in self.rescue_items_dict.items():
            if(riddles[riddle_type].attempts==0):
                rescue_items_status[str(position)] = 0
                
            else:
                if(riddles[riddle_type].solved()):
                    rescue_items_status[str(position)] = 1
                else:
                    rescue_items_status[str(position)] = 2
            
        return rescue_items_status
            
        
        
        
        
        

class RiddleContainer():
    def __init__(self):
        ## initialize the 4 riddles
        self.cipher_riddle = CipherRiddle(riddle_type='cipher', riddle_dir_path='../riddles/cipher-riddles/riddles.json')
        self.cipher_riddle.load_riddle()

        self.server_riddle = ServerRiddle(riddle_type='server', riddle_dir_path='../riddles/server-riddles/riddles.json')
        self.server_riddle.load_riddle()

        self.pcap_riddle = PcapRiddle(riddle_type='pcap', riddle_dir_path='../riddles/pcap-riddles/riddles.json')
        self.pcap_riddle.load_riddle()

        self.captcha_riddle = CaptchaRiddle(riddle_type='captcha', riddle_dir_path='../riddles/captchav2-riddles/riddles.json')
        self.captcha_riddle.load_riddle()
        
        self.riddles = {
            'cipher':self.cipher_riddle,
            'server':self.server_riddle,
            'pcap':self.pcap_riddle,
            'captcha':self.captcha_riddle,
        }
    
    def get_riddle(self, riddle_type):
        riddles = {
            'cipher':self.cipher_riddle,
            'server':self.server_riddle,
            'pcap':self.pcap_riddle,
            'captcha':self.captcha_riddle,
        }

        return riddles.get(riddle_type, None)
    
    def reset_riddles(self):
        self.cipher_riddle.set_solved(False)
        self.server_riddle.set_solved(False)
        self.pcap_riddle.set_solved(False)
        self.captcha_riddle.set_solved(False)
        
        self.cipher_riddle.attempts = 0
        self.server_riddle.attempts = 0
        self.pcap_riddle.attempts = 0
        self.captcha_riddle.attempts = 0

    
class Riddle:
    """
    This class will represent any of the 4 riddles
    """
    def __init__(self, riddle_type, riddle_dir_path):
        self.riddle_type = riddle_type
        self.riddle_dir_path = riddle_dir_path
        ## pull random file from the riddle type
        self.riddle_question = None 
        self.riddle_solution = None
        self._solved = False ##solved flag
        self.attempts = 0 # number of attempts to solve the riddle

    def load_riddle(self):
        pass
    
    def get_question(self):
        return self.riddle_question
    
    def set_solved(self, solved_flag):
        self._solved= solved_flag
    
    def solved(self):
        return self._solved

    def solve_riddle(self, solution):
        self.attempts += 1 
        self._solved = solution == self.riddle_solution

class CipherRiddle(Riddle):
    
    def __init__(self, riddle_type, riddle_dir_path):
        super().__init__(riddle_type, riddle_dir_path)
        
    def load_riddle(self):

        # Open the txt file as Unicode strings and read all of it
        with open(self.riddle_dir_path, "r") as r:
            riddle_collection = json.load(r)
        
        riddle_id = 0
        
        riddle = riddle_collection[riddle_id]
        self.riddle_question = riddle['question']
        self.riddle_solution = riddle['solution']
        ## end load riddle
    
class CaptchaRiddle(Riddle):
    def __init__(self, riddle_type, riddle_dir_path):
        super().__init__(riddle_type, riddle_dir_path)
        
    def load_riddle(self):

        # Open the txt file as Unicode strings and read all of it
        with open(self.riddle_dir_path, "r") as r:
            riddle_collection = json.load(r)
        
        riddle_id = 0
        
        riddle = riddle_collection[riddle_id]
        self.riddle_question = riddle['question']
        self.riddle_solution = riddle['solution']
        ## end load riddle
        
class ServerRiddle(Riddle):
    def __init__(self, riddle_type, riddle_dir_path):
        super().__init__(riddle_type, riddle_dir_path)
        
    def load_riddle(self):

        # Open the txt file as Unicode strings and read all of it
        with open(self.riddle_dir_path, "r") as r:
            riddle_collection = json.load(r)
        
        riddle_id = 0
        
        riddle = riddle_collection[riddle_id]
        self.riddle_question = riddle['question']
        self.riddle_solution = riddle['solution']
        ## end load riddle
        
    def solve_riddle(self, solution):
        ### the logic to verify the server riddle locally is to be implemented by your team ###
        pass
        
class PcapRiddle(Riddle):
    def __init__(self, riddle_type, riddle_dir_path):
        super().__init__(riddle_type, riddle_dir_path)
        
    def load_riddle(self):

        # Open the txt file as Unicode strings and read all of it
        with open(self.riddle_dir_path, "r") as r:
            riddle_collection = json.load(r)
        
        riddle_id = 0
        
        riddle = riddle_collection[riddle_id]
        self.riddle_question = riddle['question']
        self.riddle_solution = riddle['solution']
        ## end load riddle
    
        
        


if __name__ == "__main__":
    #########
    pass
