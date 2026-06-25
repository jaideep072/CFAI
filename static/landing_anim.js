const canvas = document.getElementById('splashCanvas');
const ctx = canvas.getContext('2d');

let width, height, cols, rows;
const CELL_SIZE = 30;

function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
    cols = Math.floor(width / CELL_SIZE);
    rows = Math.floor(height / CELL_SIZE);
}
window.addEventListener('resize', resize);
resize();

// Colors
const COLOR_BG = '#1e1e24';
const COLOR_PELLET = 'rgba(255, 255, 255, 0.15)';
const COLOR_AGENT = '#81B29A'; // Emerald
const COLOR_GOAL = '#E56B6F';  // Rose

let grid = [];
let pellets = [];
let start = {r: 0, c: 0};
let goal = {r: 0, c: 0};
let path = [];
let agentPos = {x: 0, y: 0};
let pathIndex = 0;
let phase = 'wait'; // 'move', 'wait'
let waitTimer = 0;

function initMaze() {
    grid = [];
    pellets = [];
    for (let r=0; r<rows; r++) {
        let row = [];
        for (let c=0; c<cols; c++) {
            // 35% invisible walls
            let isWall = Math.random() < 0.35 ? 1 : 0;
            row.push(isWall);
            if (!isWall) {
                pellets.push({r: r, c: c, eaten: false});
            }
        }
        grid.push(row);
    }
    
    start = {r: Math.floor(rows/2), c: Math.floor(cols * 0.1)};
    goal = {r: Math.floor(rows/2), c: Math.floor(cols * 0.9)};
    
    // Clear start/goal areas
    for(let i=-1; i<=1; i++) {
        for(let j=-1; j<=1; j++) {
            let nr = start.r+i, nc = start.c+j;
            if(nr >= 0 && nr < rows && nc >= 0 && nc < cols) {
                grid[nr][nc] = 0;
                let p = pellets.find(p => p.r === nr && p.c === nc);
                if (!p) pellets.push({r: nr, c: nc, eaten: false});
            }
            nr = goal.r+i; nc = goal.c+j;
            if(nr >= 0 && nr < rows && nc >= 0 && nc < cols) {
                grid[nr][nc] = 0;
                let p = pellets.find(p => p.r === nr && p.c === nc);
                if (!p) pellets.push({r: nr, c: nc, eaten: false});
            }
        }
    }
    
    // Make sure agent doesn't eat the dot it starts on immediately
    let sp = pellets.find(p => p.r === start.r && p.c === start.c);
    if(sp) sp.eaten = true;
    
    agentPos = {x: start.c * CELL_SIZE + CELL_SIZE/2, y: start.r * CELL_SIZE + CELL_SIZE/2};
    
    findPath();
    if (path.length === 0) {
        initMaze(); // trapped, retry
    } else {
        pathIndex = 0;
        phase = 'move';
    }
}

function findPath() {
    let frontier = [start];
    let cameFrom = {};
    cameFrom[start.r+','+start.c] = null;
    let found = false;
    
    while(frontier.length > 0) {
        let current = frontier.shift();
        if (current.r === goal.r && current.c === goal.c) {
            found = true;
            break;
        }
        
        const dirs = [[-1,0],[1,0],[0,-1],[0,1]];
        for (let d of dirs) {
            let nr = current.r + d[0];
            let nc = current.c + d[1];
            if (nr>=0 && nr<rows && nc>=0 && nc<cols && grid[nr][nc] === 0) {
                let key = nr + ',' + nc;
                if (cameFrom[key] === undefined) {
                    cameFrom[key] = current;
                    frontier.push({r: nr, c: nc});
                }
            }
        }
    }
    
    path = [];
    if (found) {
        let curr = goal;
        while (curr) {
            path.push(curr);
            curr = cameFrom[curr.r+','+curr.c];
        }
        path.reverse();
    }
}

let targetAngle = 0;
let currentAngle = 0;

function update() {
    if (phase === 'move') {
        if (pathIndex < path.length) {
            let targetNode = path[pathIndex];
            let tx = targetNode.c * CELL_SIZE + CELL_SIZE/2;
            let ty = targetNode.r * CELL_SIZE + CELL_SIZE/2;
            
            let dx = tx - agentPos.x;
            let dy = ty - agentPos.y;
            let dist = Math.sqrt(dx*dx + dy*dy);
            
            // Turn agent towards movement
            if (dist > 0.1) {
                targetAngle = Math.atan2(dy, dx);
            }
            
            // smooth angle transition
            let diff = targetAngle - currentAngle;
            while(diff < -Math.PI) diff += Math.PI*2;
            while(diff > Math.PI) diff -= Math.PI*2;
            currentAngle += diff * 0.2;
            
            if (dist < 4) { // speed is 4, so within 1 frame
                agentPos.x = tx;
                agentPos.y = ty;
                pathIndex++;
            } else {
                agentPos.x += (dx / dist) * 4; // speed
                agentPos.y += (dy / dist) * 4;
            }
            
            // Eat pellets
            for (let p of pellets) {
                if (!p.eaten) {
                    let px = p.c * CELL_SIZE + CELL_SIZE/2;
                    let py = p.r * CELL_SIZE + CELL_SIZE/2;
                    let pdx = px - agentPos.x;
                    let pdy = py - agentPos.y;
                    if (pdx*pdx + pdy*pdy < 100) { // within 10px
                        p.eaten = true;
                    }
                }
            }
        } else {
            phase = 'wait';
            waitTimer = 80; // wait ~1.2s
        }
    } else if (phase === 'wait') {
        waitTimer--;
        if (waitTimer <= 0) {
            initMaze();
        }
    }
}

function draw() {
    ctx.fillStyle = COLOR_BG;
    ctx.fillRect(0, 0, width, height);
    
    // Draw pellets (implies the maze layout!)
    ctx.fillStyle = COLOR_PELLET;
    for (let p of pellets) {
        if (!p.eaten && !(p.r === goal.r && p.c === goal.c)) {
            ctx.beginPath();
            ctx.arc(p.c * CELL_SIZE + CELL_SIZE/2, p.r * CELL_SIZE + CELL_SIZE/2, 3, 0, Math.PI*2);
            ctx.fill();
        }
    }
    
    // Draw path trail behind pacman
    if ((phase === 'move' || phase === 'wait') && path.length > 0) {
        ctx.strokeStyle = COLOR_AGENT;
        ctx.lineWidth = 4;
        ctx.shadowBlur = 12;
        ctx.shadowColor = COLOR_AGENT;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.beginPath();
        
        ctx.moveTo(path[0].c * CELL_SIZE + CELL_SIZE/2, path[0].r * CELL_SIZE + CELL_SIZE/2);
        
        let maxIdx = Math.min(pathIndex - 1, path.length - 1);
        for (let i = 1; i <= maxIdx; i++) {
            ctx.lineTo(path[i].c * CELL_SIZE + CELL_SIZE/2, path[i].r * CELL_SIZE + CELL_SIZE/2);
        }
        
        // Draw line exactly to the agent's current position to make it seamless
        if (phase === 'move') {
            ctx.lineTo(agentPos.x, agentPos.y);
        } else if (phase === 'wait') {
            ctx.lineTo(path[path.length-1].c * CELL_SIZE + CELL_SIZE/2, path[path.length-1].r * CELL_SIZE + CELL_SIZE/2);
        }
        
        ctx.stroke();
        ctx.shadowBlur = 0; // reset
    }
    
    // Draw Goal
    if (phase === 'move' || phase === 'wait') {
        ctx.fillStyle = COLOR_GOAL;
        ctx.shadowBlur = 15;
        ctx.shadowColor = COLOR_GOAL;
        ctx.beginPath();
        ctx.arc(goal.c * CELL_SIZE + CELL_SIZE/2, goal.r * CELL_SIZE + CELL_SIZE/2, 8, 0, Math.PI*2);
        ctx.fill();
        ctx.shadowBlur = 0;
    }
    
    // Draw Agent (Pacman-like wedge)
    ctx.save();
    ctx.translate(agentPos.x, agentPos.y);
    ctx.rotate(currentAngle);
    
    // Mouth chomping animation
    let mouthAngle = 0;
    if (phase === 'move') {
        mouthAngle = Math.sin(Date.now() / 80) * 0.4 + 0.4; // oscillates between 0 and 0.8 rads
    }
    
    ctx.fillStyle = COLOR_AGENT;
    ctx.shadowBlur = 10;
    ctx.shadowColor = COLOR_AGENT;
    ctx.beginPath();
    ctx.arc(0, 0, 10, mouthAngle, Math.PI*2 - mouthAngle);
    ctx.lineTo(0, 0);
    ctx.fill();
    ctx.restore();
}

function loop() {
    update();
    draw();
    requestAnimationFrame(loop);
}

initMaze();
loop();
