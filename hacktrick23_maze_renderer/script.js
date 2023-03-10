let heroImg;
let renderedMaze;
let intervalID;
let rescuedCounter = 0;
let rescueItems = [];

// Loading maze.json file
fetch("./attempt/maze.json")
  .then((response) => response.json())
  .then((json) => {
    renderMaze(json.maze, json.rescue_items);
    rescueItems = json.rescue_items;
  });

// Adding event listeners to play & stop btns
document.getElementById("play-btn").addEventListener("click", onPlayBtnClicked);
document.getElementById("stop-btn").addEventListener("click", onStopBtnClicked);

// Loading states.json file
function onPlayBtnClicked() {
  fetch("./attempt/states.json")
    .then((response) => response.json())
    .then((json) => play(json));
}

function onStopBtnClicked() {
  clearInterval(intervalID);
}

function play(actions) {
  let keys = Object.values(actions);
  rescuedCounter = 0;
  document.getElementById("rescued").innerText = 0;
  let i = 0;
  intervalID = setInterval(() => {
    renderHero(keys[i][0], keys[i][1]);
    updateRescueItems(keys[i][2]);
    i++;
    document.getElementById("actions").innerText = i;
    if (intervalID && i === keys.length) {
      // Checking if the last action added was to move the agent to the exit cell
      if (
        (keys[keys.length - 1][0][0] == 8 &&
          keys[keys.length - 1][0][1] == 9 &&
          keys[keys.length - 1][1] == "2") ||
        (keys[keys.length - 1][0][0] == 9 &&
          keys[keys.length - 1][0][1] == 8 &&
          keys[keys.length - 1][1] == "1")
      ) {
        renderHero([9, 9], 1);
        updateRescueItems(keys[i - 1][i - 1][2]);
      }
      clearInterval(intervalID);
    }
    // Change this value to change the speed of the hero in the maze
  }, 60);
}

function renderMaze(maze, rescueItems) {
  const mazeContainer = document.getElementById("maze-container");
  if (renderedMaze) {
    renderedMaze.remove();
  }

  renderedMaze = document.createElement("div");
  renderedMaze.setAttribute("id", "maze");
  mazeContainer.append(renderedMaze);

  for (let i = 0; i < maze.length; i++) {
    for (let j = 0; j < maze[i].length; j++) {
      let div = document.createElement("div");
      let img = document.createElement("img");
      img.src = generateCell(j, i, maze);
      img.classList.add("maze-img");
      div.classList.add("maze-box");
      div.append(img);
      div.setAttribute("id", `maze-box-${j}-${i}`);
      renderedMaze.append(div);
    }
  }

  heroImg = document.createElement("img");
  heroImg.setAttribute("id", "hero");
  heroImg.src = "./assets/hero.png";
  heroImg.classList.add("hero-img");
  let origin = document.getElementById("maze-box-0-0");
  origin.append(heroImg);
  renderRescueItems(rescueItems);
}

function renderHero(newState, action) {
  heroImg.remove();

  heroImg = document.createElement("img");
  heroImg.setAttribute("id", "hero");

  // Changing the hero img based on the current action and rescued counter
  let src = "";
  if (rescuedCounter === 0) {
    switch (action) {
      case 0:
      case "0":
        src = "./assets/heroN.png";
        break;
      case 1:
      case "1":
        src = "./assets/hero.png";
        break;
      case 2:
      case "2":
        src = "./assets/heroE.png";
        break;
      case 3:
      case "3":
        src = "./assets/heroW.png";
        break;
    }
  } else {
    src =
      action == 0
        ? "./assets/heroN.png"
        : `./assets/hero-${
            action == 3 ? rescuedCounter + "W" : rescuedCounter
          }.png`;
  }
  heroImg.src = src;
  heroImg.classList.add("hero-img");
  let position = document.getElementById(
    `maze-box-${newState[0]}-${newState[1]}`
  );
  position?.append(heroImg);
}

function renderRescueItems(items) {
  items.forEach((e, i) => {
    let y = e[0];
    let x = e[1];
    const tile = document.getElementById(`maze-box-${y}-${x}`);
    const itemImg = document.createElement("img");
    itemImg.src = `./assets/kid-${i}.png`;
    itemImg.classList.add("hero-img");
    itemImg.setAttribute("id", `item-${i}`);
    tile.append(itemImg);
  });
}

function updateRescueItems(items) {
  let rescuedCounterTmp = 0;
  let itemsObj = JSON.parse(items.replaceAll("'", '"'));
  rescueItems.forEach((e, i) => {
    const key = `(${e[0]}, ${e[1]})`;
    if (itemsObj[key] === 1) {
      rescuedCounterTmp++;
    }
    if (itemsObj[key] === 1 || itemsObj[key] === 2) {
      let tmpItem = document.getElementById(`item-${i}`);
      if (tmpItem) tmpItem.remove();
    }
  });
  rescuedCounter = rescuedCounterTmp;
  document.getElementById("rescued").innerText = rescuedCounterTmp;
}

// Generate the cell img file path based on the maze representation
function generateCell(i, j, maze) {
  let walls = [1, 1, 1, 1];
  let val = maze[i][j];
  switch (val) {
    case 1:
      walls[1] = 0;
      break;
    case 2:
      walls[2] = 0;
      break;
    case 4:
      walls[3] = 0;
      break;
    case 8:
      walls[0] = 0;
      break;
  }

  if (i - 1 >= 0 && maze[i - 1][j] === 2) {
    walls[0] = 0;
  }

  if (i + 1 < maze.length && maze[i + 1][j] === 8) {
    walls[2] = 0;
  }

  if (j - 1 >= 0 && maze[i][j - 1] === 4) {
    walls[1] = 0;
  }

  if (j + 1 < maze[i].length && maze[i][j + 1] === 1) {
    walls[3] = 0;
  }

  if (i === maze.length - 1 && j === maze[i].length - 1) {
    walls[3] = 0;
  }

  let filePath = "./assets/" + walls.join("") + ".png";

  return filePath;
}
