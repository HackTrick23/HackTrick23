# Hacktrick23

## Setup
- Run `python setup.py install`. This file can be found in `gym-maze`.
- Install the requirements from `gym-maze/gym_maze/envs/requirements.txt`. Use `pip install -r requirements.txt` 

## Generating a Maze
- Run `maze_generator.py` which can be found in `gym_maze/env`. 
- `rescue_item_locations` is overriden internally and the rescue items will be randomly placed. 
- The default maze size for evaluation will be 10x10, but feel free to experiment with other sizes by adjusting `maze_size`.
- Below is a snippet of the main function.
- The resulting maze will be a .npy file named `sample_maze.npy`, saved in `gym-maze`.

```
if __name__ == "__main__":
    # DO NOT CHANGE
    # USE ONLY FOR GENERATING RANDOM/SAMPLE MAZES
    while(True):
        maze = Maze(maze_size=(10, 10), rescue_item_locations=[(10,10)])
        is_validated = validate_maze(maze.maze_cells)
        if is_validated:
            break

    print(maze.maze_cells)
    np.save("../../sample_maze.npy", maze.maze_cells)
```


## Running Locally
- Run `python local_solver.py`.
- Write any agent_id. This is used only when submitting.
- Make sure you add the path of the maze you want to try in the main function.
- Riddle solvers will be imported from `riddle_solvers.py`, so make sure to implement your riddle solutions there.

## Submission
- Make sure that you are using the correct IP and endpoints.
- Make sure that you are using the correct agent_id.
- Riddle solvers will be imported from `riddle_solvers.py`, so make sure to implement your riddle solutions there.
- Run `submission_solver.py`