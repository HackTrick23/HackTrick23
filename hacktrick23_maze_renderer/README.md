## How to run the renderer

1. Update the [maze.json](./attempt/maze.json) file with the following:

   - maze: a 2d representation of the maze.
   - rescue_items: a 2d array of the rescue items positions.
     Each element is an array of 2 representing the coordinates of the rescue item.

   > use the file as an example.

2. Generate your `states.json` from maze env which should follow this format.

   ```json
   {
     "0": [[0, 0], 3, "{'(3, 1)': 0, '(8, 1)': 0, '(0, 8)': 0, '(8, 9)': 0}"],
     "1": [[0, 0], 0, "{'(3, 1)': 0, '(8, 1)': 0, '(0, 8)': 0, '(8, 9)': 0}"],
     "2": [[1, 0], 2, "{'(3, 1)': 0, '(8, 1)': 0, '(0, 8)': 0, '(8, 9)': 0}"],
     "3": [[1, 0], 0, "{'(3, 1)': 0, '(8, 1)': 0, '(0, 8)': 0, '(8, 9)': 0}"]
   }
   ```

3. Update the [states.json](./attempt/states.json) file with your agent generated states.
4. Open the [index.html](./index.html) in your browser.
5. Click on the play button to start the simulation.
