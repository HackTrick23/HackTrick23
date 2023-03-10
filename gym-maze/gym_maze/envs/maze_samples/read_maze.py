import numpy as np
import json

maze = np.array([[2, 1, 2, 1, 1, 1, 1, 4, 4, 2], [2, 4, 2, 1, 1, 1, 1, 4, 4, 2]])

np.save('maze.npy', maze)

print(maze)

# with open("maze_sample.json", "w") as file:
#     json.dump(maze, file)