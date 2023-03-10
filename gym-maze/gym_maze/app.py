from flask import Flask, jsonify, request
from pymongo import MongoClient
import numpy as np
import json
from flask_cors import CORS, cross_origin
from collections import deque

from datetime import datetime
import sys
from bson import json_util

sys.path.insert(1, '/path/to/application/app/folder')
from envs import maze_manager

import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

# -------------START CLASSES-------------

allowedActions = [
    "N", "S", "E", "W"
]

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
db = MongoClient()
db = db["Maze"]
mazeManager = maze_manager.MazeManager()

agentId = "ABC123"
name = "Team"

#db.Users.insert_one({"_id": 0, "name": "Test"})
# # db.Users.insert_one({"_id":"Users", "Users": allowedAgentsList})
# db.Users.insert_one({"_id":"ABC123"})
# db.Server.insert_one({"_id": "MAX_STEPS", "steps": 1000})
# db.Server.insert_one({"_id": "MAX_NO_OF_SECS_BETWEEN_ACTIONS", "secs": 30})
# db.Server.insert_one({"_id": "MAX_NO_OF_SECS_OF_GAME", "secs": 600})
# db.Server.insert_one({"_id": "SAVING_THRESHOLD", "secs": 50})
# db.Server.insert_one({"_id": "RESCUE_LOCATIONS_FIRST", "locations": [[8, 1], [5, 4], [6, 9],[4, 3]]})
# db.Server.insert_one({"_id": "RESCUE_LOCATIONS_FINAL", "locations": [[8, 1], [5, 4], [6, 9],[4, 3]]})


# 10mins
# maxNoSecs = db.Server.find({"_id": "MAX_NO_OF_SECS_BETWEEN_ACTIONS"})
# maxSteps = db.Server.find({"_id": "MAX_STEPS"})
# MAX_NO_OF_SECS_BETWEEN_ACTIONS = list(maxNoSecs)[0]['secs']
# MAX_NO_OF_SECS_OF_GAME = list(maxNoSecsGame)[0]['secs']
# MAX_STEPS = list(maxSteps)[0]['steps']
# SAVING_THRESHOLD = list(savingThreshold)[0]['steps']


MAX_NO_OF_SECS_BETWEEN_ACTIONS = 30
MAX_NO_OF_SECS_OF_GAME = 900
MAX_STEPS = 5000
SAVING_THRESHOLD = 50
rescueItems = list(mazeManager.rescue_items_dict.keys())
RESCUE_LOCATIONS_FIRST = [list(rescueItems[0]), list(rescueItems[1]), list(rescueItems[2]), list(rescueItems[3])]
RESCUE_LOCATIONS_FINAL = [list(rescueItems[0]), list(rescueItems[1]), list(rescueItems[2]), list(rescueItems[3])]
# 0 for initial and 1 for final
HACKATHON_PHASE = 0



class Agent:
    def __init__(self, id, connected, currentPosition, currentRiddle, solvedRiddles, mazeId,
                 score, teamName, connectionTime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 stepsRemaining=MAX_STEPS):
        self.id = id
        self.connected = connected
        self.currentPosition = currentPosition
        self.currentRiddle = currentRiddle
        self.solvedRiddles = []
        self.riddlesTime = dict()
        self.mazeId = mazeId
        self.score = score
        self.teamName = teamName
        self.connectionTime = connectionTime
        self.lastStepTimeStamp = connectionTime
        self.stepsRemaining = stepsRemaining

    def getAgentJson(self):
        return {
            "id": 0,
            "connected": self.connected,
            "currentPosition": self.currentPosition,
            "currentRiddle": self.currentRiddle,
            "solvedRiddles": self.solvedRiddles,
            "mazeId": self.mazeId,
            "score": self.score,
            "teamName": self.teamName,
            "connectionTime": self.connectionTime
        }


agents = dict()
agentsSteps = dict()
agentRiddles = dict()
agentRiddleStartTimes = dict()
agentRiddleSolveTimes = dict()


def getAgent(id):
    return agents[id] if id in agents else None


allowedAgents = {
    'ABC123',
    'ABC1234',
    0
}

allowedAgentsList = ["ABC123"]

adminPasswords = {
    "ADMIN123"
}


def get_move(cell, r, c, rows_length, cols_length):
    next_state = None
    if cell == 1 and r - 1 >= 0:
        next_state = r - 1, c
    elif cell == 2 and c + 1 < cols_length:
        next_state = r, c + 1
    elif cell == 4 and r + 1 < rows_length:
        next_state = r + 1, c
    elif cell == 8 and c - 1 >= 0:
        next_state = r, c - 1
    return next_state


def get_possible_children(r, c, rows_length, cols_length):
    children = []
    if r - 1 >= 0:
        children.append((r - 1, c))
    if c - 1 >= 0:
        children.append((r, c - 1))
    if c + 1 < cols_length:
        children.append((r, c + 1))
    if r + 1 < rows_length:
        children.append((r + 1, c))
    return children


def get_possible_moves(maze, r, c):
    rows_length, cols_length = maze.shape
    next_states = set()
    cell = maze[r][c]
    next_state = get_move(cell, r, c, rows_length, cols_length)
    if next_state is not None:
        next_states.add(next_state)
    possible_children = get_possible_children(r, c, rows_length, cols_length)
    for child in possible_children:
        child_r, child_c = child
        cell = maze[child_r][child_c]
        next_state = get_move(cell, child_r, child_c, rows_length, cols_length)
        if next_state is None:
            continue
        r_new, c_new = next_state
        if r_new == r and c_new == c:
            next_states.add(child)
    return next_states


def maze_has_blockers(maze):
    maze = maze.T
    queue = deque()
    queue.append((0, 0))
    optimizedQueue = set()  # for faster search
    explored = set()
    while len(queue) > 0:
        currentState = queue.popleft()
        explored.add(currentState)
        r, c = currentState
        children = get_possible_moves(maze, r, c)
        for child in children:
            if child not in optimizedQueue and child not in explored:
                queue.append(child)
                optimizedQueue.add(child)
    return len(explored) != np.prod(maze.shape)


def validate_maze(maze):
    # Check if the maze is a 2D numpy array
    if not isinstance(maze, np.ndarray) or maze.ndim != 2:
        return False, "Please submit a valid 10x10 numpy array"

    # Check if the maze is 10x10
    if maze.shape[0] != 10 or maze.shape[1] != 10:
        return False, "Please submit a valid 10x10 numpy array"

    # Check if each entry in the array is 1, 2, 4 or 8
    if not np.all(np.isin(maze, [1, 2, 4, 8])):
        return False, "Please submit a valid 10x10 numpy array which only contains the values 1,2,4 or 8"
    if maze_has_blockers(maze):
        return False, "Please submit a valid maze which has a solution and has no blockers"
    # If all checks pass, the maze is valid
    return True, "Maze submitted successfully"

def checkTimeout(agentId):
    # check timestamps
    agent = agents[agentId]
    currentTime = datetime.now()
    agentTime = datetime.strptime(agent.lastStepTimeStamp, "%Y-%m-%d %H:%M:%S")
    totalTime = datetime.strptime(agent.connectionTime, "%Y-%m-%d %H:%M:%S")
    actionTimeDifference = currentTime - agentTime
    gameTimeDifference = currentTime - totalTime
    save = False
    if MAX_STEPS - agent.stepsRemaining > SAVING_THRESHOLD:
        save = True
    if actionTimeDifference.total_seconds() > MAX_NO_OF_SECS_BETWEEN_ACTIONS or gameTimeDifference.total_seconds() > MAX_NO_OF_SECS_OF_GAME:
        if save:
            saveSimulationHistory(agentId)
        else:
            del agents[agentId]
            del agentsSteps[agentId]

        return False
    # check remaining steps
    if agent.stepsRemaining <= 0:
        if save:
            saveSimulationHistory(agentId)
        else:
            del agents[agentId]
            del agentsSteps[agentId]

        return False
    agent.lastStepTimeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    agent.stepsRemaining -= 1
    return True


# -------------END CLASSES--------------------

@app.route('/status')
def status():
    return jsonify({'status': 'up'})


@app.route('/submitMaze', methods=['POST'])
def submitMaze():
    agentId = request.get_json()['agentId']
    if db.Users.find_one({"_id": agentId}) == None:
        return "agentId is either wrong, or not initialized!", 400
    else:
        submittedMaze = request.get_json()['submittedMaze']
        submittedMazeNp = np.array(json.loads(submittedMaze))
        validateMaze = validate_maze(submittedMazeNp)
        isValid, validationText = validateMaze
        if not isValid:
            return validationText, 400
        try:
            db.Mazes.insert_one({"_id": agentId, "maze": submittedMaze})
        except:
            return "Maze is either already submitted or invalid", 400
        # np.save(f'submitted_mazes/{agentId}.npy', submittedMazeNp)
        return validationText, 200
    


@app.route('/init', methods=['POST'])
def init():
    try:
        agentId = request.get_json()['agentId']
    except:
        return "Wrong request", 400
    allowedAgent = db.Users.find_one({"_id": agentId})
    if allowedAgent != None:
        if agentId in agents:
            if MAX_STEPS - agents[agentId].stepsRemaining > SAVING_THRESHOLD:
                saveSimulationHistory(agentId)
        # check attempts
        mazeNumber = HACKATHON_PHASE
        attempts = db.Attempts.find({"agentId": agentId, "maze": str(mazeNumber)})
        attemptsList = list(attempts)
        if (len(attemptsList) >= 5) and (mazeNumber == 0):
            return "Max attempts reached", 400
        elif len(attemptsList) > 0 and (mazeNumber != 0):
            return "Maze already attempted", 400
        
        if mazeNumber != 0 and mazeNumber != 1:
            return "Maze Number not valid", 400
        ## check if user attempted their maze
        if mazeNumber == 1:
            attempts = db.Attempts.find({"agentId": agentId})
            attemptsList = list(attempts)
            attemptedMazes = []
            for attempt in attemptsList:
                attemptedMazes.append(attempt['maze'])
            if agentId not in attemptedMazes:
                mazeNumber = agentId
            else:
                for submittedMaze in allowedAgents:
                    if submittedMaze not in attemptedMazes:
                        mazeNumber = submittedMaze
                        break
                if mazeNumber == 1:
                    return "all mazes attempted", 400

        
        Maze = db.Mazes.find_one({"_id": str(mazeNumber)})
        if Maze == None:
            return "Maze Not Found", 400
        numpyMaze = np.array(Maze["maze"])
        mazeState = mazeManager.init_maze(agentId, maze_cells=numpyMaze)
        

        state = {
            "position": mazeState[0].tolist(),
            "distances": mazeState[1],
            "directions": mazeState[2]
        }
        newAgent = Agent(
            id=agentId, connected=True, currentPosition=state["position"],
            currentRiddle=0, solvedRiddles=[], mazeId=mazeNumber,
            score=0, teamName="", connectionTime=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        agentsSteps[agentId] = []
        agents[agentId] = newAgent
        # Send state
        return {'position': state["position"],
                "distances": state["distances"],
                "directions": state["directions"]}, 200
    else:
        return "Connection refused because agentId is wrong, please double check and try again!", 401

allowedAgent = db.Users.find()
@app.route('/move', methods=['POST'])
def move():
    agentId = request.get_json()['agentId']
    #allowedAgent = db.Users.find_one({"_id": agentId})
    if agentId in allowedAgent :
        return "agentId is either wrong, or not initialized!", 400
    else:
        if agentId in agents:
            if checkTimeout(agentId):
                action = request.get_json()['action']

                if action in allowedActions:
                    obv, reward, terminated, truncated, info = mazeManager.step(agentId, action)
                    state = {
                        "position": obv[0].tolist(),
                        "distances": obv[1],
                        "directions": obv[2],
                        "rescuedItems": info["rescued_items"],
                        "riddleType": info["riddle_type"],
                        "riddleQuestion": info["riddle_question"],
                    }
                    if info['riddle_type'] and info['riddle_question']:
                        agents[agentId].riddlesTime[info['riddle_type']] = time.time()
                    dbAction = {
                        str(len(agentsSteps[agentId])): [obv[0].tolist(), allowedActions.index(action), str(mazeManager.get_rescue_items_status(agentId))]
                    }
                    agentsSteps[agentId].append(dbAction)
                    if state == None:
                        return "Action not allowed", 403
                    else:
                        agents[agentId].currentPosition = obv[0].tolist()
                        return state, 200
                else:
                    return "Action is invalid", 400
            else:
                return "Time limit exceeded, or reached max number of steps", 400
        else:
            return "agent not initialized", 400


@app.route('/solve', methods=['POST'])
def solve():
    try:
        agentId = request.get_json()['agentId']
    except:
        return "Agent id not found in request", 400
    allowedAgent = db.Users.find_one({"_id": agentId})

    if allowedAgent == None or agentId not in agents:
        return "agentId is either wrong, or not initialized!", 400
    else:
        if checkTimeout(agentId):
            try:
                solution, riddleType =  request.get_json()['solution'], \
                request.get_json()["riddleType"]
            except:
                return "Wrong input ", 400
            agents[agentId].riddlesTime[riddleType] = time.time() - agents[agentId].riddlesTime[riddleType]
            mazeState = mazeManager.solve_riddle(riddleType, agentId, solution)
            state = {
                "position": mazeState[0][0].tolist(),
                "distances": mazeState[0][1],
                "directions": mazeState[0][2],
                "rescuedItems": mazeState[4]["rescued_items"],
                "riddleType":  mazeState[4]["riddle_type"],
                "riddleQuestion":  mazeState[4]["riddle_question"],
            }
            if state == None:
                return "Invalid riddle Id or solution", 400
            else:
                return state, 200
        else:
            return "Time limit exceeded, or reached max number of steps", 400


@app.route('/getAgentStatus', methods=['POST'])
def getAgentStatus():
    agentId = request.get_json()['agentId']
    adminPassword = request.get_json()['adminPassword']
    if adminPassword in adminPasswords:
        agent = getAgent(agentId)
        if agent == None:
            return "agentId is either wrong, or not initialized!", 400
        else:
            return jsonify({
                "id": agent.id,
                "connected": agent.connected,
                "currentPosition": agent.currentPosition,
                "mazeId": agent.mazeId,
                "score": agent.score,
                "teamInfo": agent.teamInfo,
                "connectionTime": agent.connectionTime,
                "lastAction": agent.lastStepTimeStamp,
                "remainingSteps": agent.stepsRemaining
            }), 200
    else:
        return 403


@app.route('/killSession', methods=['POST'])
def killSession():
    # check admin password
    agentId = request.get_json()['agentId']
    adminPassword = request.get_json()['adminPassword']
    if adminPassword in adminPasswords:
        agent = getAgent(agentId)
        if agent == None:
            return "agentId is either wrong, or not initialized!", 400
        else:
            saveSimulationHistory(agentId)
            return "Agent Killed!", 200
    else:
        return 403


@app.route('/leave', methods=['POST'])
def leave():
    try:
        agentId = request.get_json()['agentId']
    except:
        return "Can't find agent id", 400
    if agentId not in agents:
        return "agentId is either wrong, or not initialized!", 400
    else:
        position = agents[agentId].currentPosition
        if position == [9, 9]:
            saveSimulationHistory(agentId, True)
        else:
            saveSimulationHistory(agentId)
        return "You successfully exited the maze!", 200


@app.route('/runSavedGame', methods=['GET'])
def runGame():
    pass


def mazeEnded(agentId):
    pass

def saveSimulationHistory(agentId, didLeave=False):
    steps = agentsSteps[agentId]
    escaped = didLeave

    agent = agents[agentId]
    if agentId == agent.mazeId and didLeave == False:
        return


    totalScore, riddlesScores = mazeManager.calculate_final_score(agentId, agent.riddlesTime)
    riddlesTime = dict()
    riddleTypes=["cipher","server","pcap","captcha"]
    for riddleType in riddleTypes:
        try:
            riddlesTime[riddleType]=agents[agentId].riddlesTime[riddleType]
        except:
            riddlesTime[riddleType]="unsolved"
    rescueItemsStatus = [1, 2, 0, 1]
    info = {"escaped": escaped, "score": riddlesScores, "totalScore": totalScore, "riddlesTime": riddlesTime}
    saveLeaderboardInfo(agent, info)
    # score = mazeManger.calculateScore()
    db.Attempts.insert_one({"agentId": agentId, "maze": str(agent.mazeId), "actions": steps, "score": totalScore,
                            "rescueItems": str(rescueItemsStatus)})

    if db.Agents.find_one({"_id": agentId}) == None:
        db.Agents.insert_one({"_id": agentId, "agent": agent.getAgentJson()})
    else:
        db.Agents.replace_one({"_id": agentId}, {"_id": agentId, "agent": agent.getAgentJson()})
    del agents[agentId]
    del agentsSteps[agentId]


@app.route('/addAgent', methods=['POST'])
def addAgentId():
    agentId = request.get_json()['agentId']
    name = request.get_json()['name']
    users = db.Users.find_one({"_id": agentId})
    if users == None:
        db.Users.insert_one({"_id": agentId, "name":name})
        return jsonify({"Added": True}), 200
    else:
        return jsonify({"AlreadyAdded": True}), 200


@app.route('/deleteAgent', methods=['POST'])
def deleteAgentId():
    agentId = request.get_json()['agentId']
    users = db.Users.find_one({"_id": agentId})
    if users != None:
        db.Users.delete_one({"_id": agentId})
        return jsonify({"Added": True}), 200
    else:
        return jsonify({"Already Deleted": True}), 200

@app.route('/getActiveGames', methods=['POST'])
def deleteAgentId():
    adminPassword = request.get_json()['apiKey']
    if adminPassword in adminPasswords:
        return jsonify(agents), 200
    else:
        return 403



@app.route('/getTeamsAndMazes', methods=['POST'])
@cross_origin()
def getTeamsAndMazes():
    adminPassword = request.get_json()['apiKey']
    if adminPassword in adminPasswords:
        dbMazes = db.Mazes.find()
        dbTeams = db.Users.find()
        return json.loads(json_util.dumps({'mazes': list(dbMazes), 'teams': list(dbTeams), 'rescueItems':RESCUE_LOCATIONS_FIRST}))
    else:
        return 401

@app.route('/getLeaderboard', methods=['POST'])
@cross_origin()
def getLeaderboard():
    adminPassword = request.get_json()['apiKey']
    if adminPassword in adminPasswords:
        dbSubmissions = db.Submissions.find()
        return json.loads(json_util.dumps(list(dbSubmissions)))
    else:
        return 401


@app.route('/getAttempt', methods=['POST'])
@cross_origin()
def getAttempt():
    adminPassword = request.get_json()['apiKey']
    agentId = request.get_json()['agentId']
    mazeId = request.get_json()['mazeId']
    if adminPassword in adminPasswords:
        res = db.Attempts.find_one({"agentId": agentId, 'maze':mazeId})
        if len(list(res)) == 0:
            attemptResponse = {
                "actions": None,
                "score": None
            }   
            return json.loads(json_util.dumps(attemptResponse))

        attemptResponse = {
            "actions": res['actions'],
            "score": res['score']
        }

        return json.loads(json_util.dumps(attemptResponse))
    else:
        return 401


def saveLeaderboardInfo(agent, info):
    db.Submissions.insert_one({"agentId": agent.id,
                               "teamName": agent.teamName,
                               "actions": MAX_STEPS - agent.stepsRemaining,
                               "escaped": info['escaped'],
                               "score": info['score'],
                               "submissionTime": datetime.now(),
                               "totalScore": info['totalScore'],
                               "riddlesTime": info['riddlesTime']
                               })


def getScore(agentId):
    score = mazeManager.getScore(agentId)
    return score


def cleanAgents():
    print("CLEANING TIMED OUT AGENTS......")
    for agent in agents:
        checkTimeout(agent)


scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanAgents, trigger="interval", seconds=600)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


if __name__ == "__main__":
    from waitress import serve

    #serve(app, host="0.0.0.0", port=5000, connection_limit=1000, threads=100)
    app.run(host='0.0.0.0')
