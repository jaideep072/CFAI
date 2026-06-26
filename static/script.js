/**
 * PATHFINDING VISUALIZER - FRONTEND CONTROLLER
 * Handles interactive drawing, drag-and-drop start/goal pins,
 * animation playback loops, API calls, CSP visualizations, and benchmarks.
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // === STATE VARIABLES ===
    let grid = [];
    let rows = 21;
    let cols = 21;
    let start = [0, 0];
    let goal = [20, 20];
    
    // Interactive Editing States
    let isMouseDown = false;
    let isDrawing = false;
    let activeTool = 'wall'; // 'wall', 'mud', 'water', 'erase'
    let isDraggingStart = false;
    let isDraggingGoal = false;

    // Adversarial & Probabilistic States (CO4, CO5, CO6)
    let ghostPos = null;
    let ghosts = [];
    let initialGhostPos = null;
    let initialAgentPos = null;
    let pacmanScore = 0;
    let arcadeInterval = null;
    let queuedDirection = null;
    let currentDirection = null;
    let isApiBusy = false;
    let isGhostPlacementMode = false;
    let isAdversarialPlaying = false;
    let adversarialTimeout = null;
    let ghostBelief = null;
    
    // Animation Playback States
    let steps = [];
    let solvedPath = [];
    let currentFrameIndex = -1;
    let isPlaying = false;
    let animationTimeout = null;
    let animationSpeed = 50; // ms per frame
    
    // === DOM ELEMENTS ===
    const gridContainer = document.getElementById('grid-container');
    const presetSelect = document.getElementById('maze-preset');
    const customParams = document.getElementById('custom-maze-params');
    const rowsInput = document.getElementById('maze-rows');
    const colsInput = document.getElementById('maze-cols');
    const seedInput = document.getElementById('maze-seed');
    
    const btnGenerate = document.getElementById('btn-generate');
    const btnClear = document.getElementById('btn-clear');
    
    const chkPartiallyObservable = document.getElementById('env-partially-observable');
    const chkHeatmap = document.getElementById('env-heatmap');
    const visionRadiusGroup = document.getElementById('vision-radius-group');
    const visionRadiusSlider = document.getElementById('vision-radius');
    const lblVisionRadius = document.getElementById('val-vision-radius');
    
    const algoSelect = document.getElementById('algo-select');
    const heuristicParams = document.getElementById('heuristic-params');
    const heuristicSelect = document.getElementById('heuristic-select');
    const weightParams = document.getElementById('weight-params');
    const weightSlider = document.getElementById('algo-weight');
    const lblAlgoWeight = document.getElementById('val-algo-weight');
    const btnSolve = document.getElementById('btn-solve');
    
    // Playback buttons
    const btnPlayPause = document.getElementById('btn-play-pause');
    const btnStepPrev = document.getElementById('btn-step-prev');
    const btnStepNext = document.getElementById('btn-step-next');
    const btnResetAnim = document.getElementById('btn-reset-anim');
    const animSpeedSlider = document.getElementById('anim-speed');
    const lblAnimSpeed = document.getElementById('val-anim-speed');
    const animProgressBar = document.getElementById('anim-progress');
    const lblStepCount = document.getElementById('progress-step-count');
    const lblAnimStatus = document.getElementById('anim-status-label');
    
    // Stats labels
    const statAlgo = document.getElementById('stat-algo');
    const statExpanded = document.getElementById('stat-expanded');
    const statPathLen = document.getElementById('stat-path-len');
    const statFrontier = document.getElementById('stat-frontier');
    const statTime = document.getElementById('stat-time');
    const statSolved = document.getElementById('stat-solved');
    const infoCardText = document.getElementById('solve-details-text');
    const infoCardPanel = document.getElementById('solve-details-panel');
    
    // CSP Elements
    const btnCspColor = document.getElementById('btn-csp-color');
    const btnCspSchedule = document.getElementById('btn-csp-schedule');
    const cspResultsContainer = document.getElementById('csp-results-container');
    const cspResultsTitle = document.getElementById('csp-results-title');
    const cspResultsContent = document.getElementById('csp-results-content');
    const cspColorsNum = document.getElementById('csp-colors-num');
    
    // Benchmark Elements
    const btnRunBenchmark = document.getElementById('btn-run-benchmark');
    const benchmarkTable = document.getElementById('benchmark-table');
    const benchmarkTableBody = document.getElementById('benchmark-table-body');
    const benchmarkAnalysisPanel = document.getElementById('benchmark-analysis');
    const benchmarkAnalysisText = document.getElementById('benchmark-analysis-text');
    const apiStatus = document.getElementById('api-status');
    const instructionText = document.getElementById('instruction-text');

    // Adversarial Elements
    const btnPlaceGhost = document.getElementById('btn-place-ghost');
    const btnAdvStep = document.getElementById('btn-adv-step');
    const btnAdvPlay = document.getElementById('btn-adv-play');
    const btnAdvReset = document.getElementById('btn-adv-reset');
    const advControlSelect = document.getElementById('adv-control-mode');
    const advAlgoContainer = document.getElementById('adv-algo-container');
    const advAlgoSelect = document.getElementById('adv-algo');
    const advDepthSlider = document.getElementById('adv-depth');
    const lblAdvDepth = document.getElementById('val-adv-depth');
    const advStatusText = document.getElementById('adv-status-text');
    const advStatusPanel = document.getElementById('adv-status-panel');

    // Probabilistic Elements
    const btnHmmStep = document.getElementById('btn-hmm-step');
    const btnHmmReset = document.getElementById('btn-hmm-reset');
    const btnRunVe = document.getElementById('btn-run-ve');
    const veResultsContainer = document.getElementById('ve-results-container');
    const veResultsContent = document.getElementById('ve-results-content');
    const lblSensorVal = document.getElementById('lbl-sensor-val');
    const lblTrueDistVal = document.getElementById('lbl-true-dist-val');

    // Hybrid Elements
    const btnHybridRun = document.getElementById('btn-hybrid-run');
    const hybridRiskSlider = document.getElementById('hybrid-risk');
    const lblHybridRisk = document.getElementById('val-hybrid-risk');
    const hybridTraceContent = document.getElementById('hybrid-trace-content');

    // === INITIALIZATION ===
    function init() {
        const style = document.createElement('style');
        style.innerHTML = `.pellet { width: 6px; height: 6px; background-color: #F2CC8F; border-radius: 50%; margin: auto; position: relative; top: 50%; transform: translateY(-50%); box-shadow: 0 0 4px #F2CC8F; }`;
        document.head.appendChild(style);

        if (typeof Pacman3D !== 'undefined') {
            Pacman3D.init('pacman-3d-canvas');
            Pacman3D.setOnClick((r, c) => {
                if (grid && grid[r] && grid[r][c] === 1) return; // Don't place on walls
                
                if (isGhostPlacementMode) {
                    if (ghostPos) {
                        const oldGhostCell = document.getElementById(`cell-${ghostPos[0]}-${ghostPos[1]}`);
                        if (oldGhostCell) {
                            oldGhostCell.classList.remove('ghost');
                            oldGhostCell.textContent = '';
                        }
                    }
                    ghostPos = [r, c];
                    initialGhostPos = [r, c];
                    initialAgentPos = [start[0], start[1]];
                    Pacman3D.setGhostPos(ghostPos);
                    
                    const cellEl = document.getElementById(`cell-${r}-${c}`);
                    if (cellEl) {
                        cellEl.classList.add('ghost');
                        cellEl.textContent = 'G';
                    }
                    
                    isGhostPlacementMode = false;
                    document.body.style.cursor = 'default';
                    
                    const btnAdvStep = document.getElementById('btn-adv-step');
                    const btnAdvPlay = document.getElementById('btn-adv-play');
                    const btnHmmStep = document.getElementById('btn-hmm-step');
                    const btnHybridRun = document.getElementById('btn-hybrid-run');
                    if (btnAdvStep) btnAdvStep.disabled = false;
                    if (btnAdvPlay) btnAdvPlay.disabled = false;
                    if (btnHmmStep) btnHmmStep.disabled = false;
                    if (btnHybridRun) btnHybridRun.disabled = false;

                    resetHMMBelief();
                    
                    const instructionText = document.getElementById('instruction-text');
                    if (instructionText) instructionText.innerHTML = `<strong>Ghost Placed!</strong> Ready to run Adversarial search (Game tab), HMM tracking (Bayes tab), or Expected Utility decision loops (Hybrid tab).`;
                }
            });
        }
        setupGlobalEvents();
        setupNavigationEvents();
        setupControlEvents();
        setupTabEvents();
        setupAccordionEvents();
        setupToolEvents();
        callGenerateApi(); // Load initial large maze preset
    }

    // === EVENT LISTENERS ===
    
    function setupGlobalEvents() {
        // Handle keyboard events for Manual Adversarial Mode
        window.addEventListener('keydown', (e) => {
            const workspace = document.getElementById('app-workspace');
            const isAdversarial = workspace && workspace.className === 'page-adversarial';
            const advControlSelect = document.getElementById('adv-control-mode');
            if (isAdversarial && advControlSelect && advControlSelect.value === 'manual' && ghostPos) {
                if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                    e.preventDefault(); // Prevent page scrolling
                    let nr = start[0];
                    let nc = start[1];
                    if (e.key === 'ArrowUp') nr--;
                    else if (e.key === 'ArrowDown') nr++;
                    else if (e.key === 'ArrowLeft') nc--;
                    else if (e.key === 'ArrowRight') nc++;
                    
                    if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] !== 1) {
                        start = [nr, nc];
                        stepAdversarial(true);
                    }
                }
            }
        });

        // Track mouse clicks globally to prevent sticky draw states
        window.addEventListener('mousedown', () => {
            isMouseDown = true;
        });
        window.addEventListener('mouseup', () => {
            isMouseDown = false;
            isDrawing = false;
            isDraggingStart = false;
            isDraggingGoal = false;
            
            // Clean cursor styling
            document.body.style.cursor = 'default';
        });

        // Dynamically resize grid on window size changes
        window.addEventListener('resize', () => {
            const workspace = document.getElementById('app-workspace');
            if (workspace && workspace.className !== 'page-dashboard') {
                resizeGrid();
            }
        });
    }

    function setupNavigationEvents() {
        const navBtns = document.querySelectorAll('.nav-btn');
        const workspace = document.getElementById('app-workspace');

        const themeColors = {
            dashboard: { color: 'var(--accent)', rgb: '168, 85, 247', wall: '#5E3E34' },
            pathfinding: { color: 'var(--emerald)', rgb: '16, 185, 129', wall: '#365445' },
            adversarial: { color: 'var(--rose)', rgb: '239, 68, 68', wall: '#663335' },
            probabilistic: { color: 'var(--cyan)', rgb: '14, 165, 233', wall: '#184D63' },
            hybrid: { color: 'var(--violet)', rgb: '157, 78, 221', wall: '#432160' }
        };

        navBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const page = btn.getAttribute('data-page');
                
                // Update nav buttons active state
                navBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Update workspace class for page rendering
                workspace.className = `page-${page}`;
                
                // Update CSS theme variables
                const theme = themeColors[page];
                document.body.style.setProperty('--theme-color', theme.color);
                document.body.style.setProperty('--theme-color-rgb', theme.rgb);
                document.body.style.setProperty('--color-wall', theme.wall);
                
                // Update page explanation
                const pageExp = document.getElementById('page-explanation');
                if (pageExp) {
                    if (page === 'pathfinding') {
                        pageExp.innerHTML = '<strong>Pathfinding &amp; CSP:</strong> Visualize uninformed, heuristic-guided search, and constraint satisfaction solvers on dynamic terrain grids.';
                    } else if (page === 'adversarial') {
                        pageExp.innerHTML = '<strong>Adversarial Arena:</strong> Simulate zero-sum multi-agent games modeling an Evader (Agent) and a Chaser (Ghost) on the grid.';
                    } else if (page === 'probabilistic') {
                        pageExp.innerHTML = '<strong>Probabilistic Tracker:</strong> Track a hidden ghost moving stochastically using noisy distance readings and probabilistic inference.';
                    } else if (page === 'hybrid') {
                        pageExp.innerHTML = '<strong>Hybrid Reasoner:</strong> Evaluate paths under uncertainty by combining threat belief maps, risk tolerance, and CSP scheduling constraints.';
                    } else if (page === 'dashboard') {
                        pageExp.innerHTML = '';
                    }
                }
                
                // Update grid layout sizes / visibility on navigation
                if (page === 'adversarial') {
                    const gridCard = document.getElementById('grid-card');
                    if (gridCard) gridCard.classList.add('hidden');
                    const canvas = document.getElementById('pacman-3d-canvas');
                    if (canvas) canvas.classList.remove('hidden');
                    if (typeof Pacman3D !== 'undefined') Pacman3D.onWindowResize();
                } else {
                    const canvas = document.getElementById('pacman-3d-canvas');
                    if (canvas) canvas.classList.add('hidden');
                    const gridCard = document.getElementById('grid-card');
                    if (gridCard) gridCard.classList.remove('hidden');
                    
                    if (page !== 'dashboard') {
                        resizeGrid();
                        updateGridVisibility();
                    }
                }
            });
        });
    }

    function setupControlEvents() {
        // Preset select toggles custom options
        presetSelect.addEventListener('change', () => {
            const val = presetSelect.value;
            if (val === 'custom' || val === 'custom_prims' || val === 'empty') {
                customParams.classList.remove('hidden');
            } else {
                customParams.classList.add('hidden');
            }
        });

        // 3D Mode Toggle
        const btnToggle3D = document.getElementById('btn-toggle-3d');
        const shapeSelect = document.getElementById('shape-select');
        const gridCard = document.getElementById('grid-card');
        const canvas3D = document.getElementById('pacman-3d-canvas');
        
        let is3DMode = false;

        btnToggle3D.addEventListener('click', () => {
            is3DMode = !is3DMode;
            if (is3DMode) {
                gridCard.classList.add('hidden');
                canvas3D.classList.remove('hidden');
                btnToggle3D.innerHTML = '<i class="fa-solid fa-table-cells"></i> 2D Mode';
                btnToggle3D.classList.remove('btn-secondary');
                btnToggle3D.classList.add('btn-primary');
                sync3DMaze();
                // Initialize Pacman3D if it hasn't been initialized
                if (typeof Pacman3D !== 'undefined' && canvas3D.children.length === 0) {
                    Pacman3D.init('pacman-3d-canvas');
                    sync3DMaze();
                }
            } else {
                gridCard.classList.remove('hidden');
                canvas3D.classList.add('hidden');
                btnToggle3D.innerHTML = '<i class="fa-solid fa-cube"></i> 3D Mode';
                btnToggle3D.classList.remove('btn-primary');
                btnToggle3D.classList.add('btn-secondary');
            }
        });

        shapeSelect.addEventListener('change', () => {
            if (is3DMode) {
                sync3DMaze();
            }
        });

        // Extend generate maze callback and API updates to automatically sync 3D if active
        const originalRenderGrid = window.renderGrid || function(){};
        
        // Generate button
        btnGenerate.addEventListener('click', () => {
            stopAnimation();
            callGenerateApi();
        });

        // Clear button
        btnClear.addEventListener('click', () => {
            stopAnimation();
            clearPathVisuals();
            solvedPath = [];
            steps = [];
            resetPlaybackUI();
            resetStatsUI();
        });

        // Import Button
        const fileImport = document.getElementById('file-import');
        if (fileImport) {
            fileImport.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (ev) => {
                    try {
                        const data = JSON.parse(ev.target.result);
                        if (data.grid && data.start && data.goal) {
                            generateGrid(data.grid, data.start, data.goal);
                            instructionText.innerHTML = `<strong>Maze Imported Successfully!</strong>`;
                        }
                    } catch(err) {
                        alert('Invalid JSON file.');
                    }
                };
                reader.readAsText(file);
                e.target.value = ''; // reset
            });
        }

        // Export Button
        const btnExport = document.getElementById('btn-export');
        if (btnExport) {
            btnExport.addEventListener('click', () => {
                const data = { grid, start, goal };
                const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'maze_export.json';
                a.click();
                URL.revokeObjectURL(url);
                instructionText.innerHTML = `<strong>Maze Exported!</strong> Saved as maze_export.json`;
            });
        }

        // Partially observable toggles vision slider
        chkPartiallyObservable.addEventListener('change', () => {
            if (chkPartiallyObservable.checked) {
                visionRadiusGroup.classList.remove('hidden');
            } else {
                visionRadiusGroup.classList.add('hidden');
            }
            // Re-render the grid visibility based on state
            updateGridVisibility();
        });

        if (chkHeatmap) {
            chkHeatmap.addEventListener('change', () => {
                if (chkHeatmap.checked) {
                    renderHeuristicHeatmap();
                } else {
                    removeHeuristicHeatmap();
                }
            });
        }

        visionRadiusSlider.addEventListener('input', () => {
            lblVisionRadius.textContent = visionRadiusSlider.value;
            updateGridVisibility();
        });

        // Algo select toggles weights and heuristics parameters
        algoSelect.addEventListener('change', () => {
            const val = algoSelect.value;
            
            // Heuristics are only relevant for Greedy, A*, Weighted A*
            if (val === 'greedy' || val === 'astar' || val === 'weighted_astar') {
                heuristicParams.classList.remove('hidden');
            } else {
                heuristicParams.classList.add('hidden');
            }

            // Weight is only relevant for Weighted A*
            if (val === 'weighted_astar') {
                weightParams.classList.remove('hidden');
            } else {
                weightParams.classList.add('hidden');
            }
        });

        weightSlider.addEventListener('input', () => {
            lblAlgoWeight.textContent = weightSlider.value;
        });

        // Playback speed slider
        animSpeedSlider.addEventListener('input', () => {
            animationSpeed = parseInt(animSpeedSlider.value);
            lblAnimSpeed.textContent = animationSpeed;
        });

        // Solve button
        btnSolve.addEventListener('click', () => {
            stopAnimation();
            callSolveApi();
        });

        // Animation playback listeners
        btnPlayPause.addEventListener('click', togglePlayPause);
        btnStepNext.addEventListener('click', stepForward);
        btnStepPrev.addEventListener('click', stepBackward);
        btnResetAnim.addEventListener('click', resetAnimation);

        // CSP Solvers
        btnCspColor.addEventListener('click', runCspColoring);
        btnCspSchedule.addEventListener('click', runCspScheduling);

        // Benchmark Run
        btnRunBenchmark.addEventListener('click', runBenchmarks);

        // Adversarial Control Panel
        btnPlaceGhost.addEventListener('click', () => {
            const ghostTypes = ['blinky', 'pinky', 'inky', 'clyde'];
            const corners = [[1, 1], [1, cols-2], [rows-2, 1], [rows-2, cols-2]];
            
            ghosts.forEach(g => {
                const c = document.getElementById(`cell-${g.pos[0]}-${g.pos[1]}`);
                if (c) { c.classList.remove('ghost'); c.textContent = ''; }
            });
            ghosts = [];

            ghostTypes.forEach((type, idx) => {
                let r = corners[idx][0];
                let c = corners[idx][1];
                if (grid[r] && grid[r][c] !== undefined && grid[r][c] !== 1) {
                    ghosts.push({pos: [r, c], type: type});
                } else {
                    for(let rr=0; rr<rows; rr++){
                        let found = false;
                        for(let cc=0; cc<cols; cc++){
                            if(grid[rr][cc] !== 1 && !(rr===start[0] && cc===start[1])) {
                                ghosts.push({pos: [rr, cc], type: type});
                                found = true; break;
                            }
                        }
                        if(found) break;
                    }
                }
            });

            ghosts.forEach(g => {
                const cellEl = document.getElementById(`cell-${g.pos[0]}-${g.pos[1]}`);
                if (cellEl) {
                    cellEl.classList.add('ghost');
                }
            });
            
            ghostPos = ghosts[0].pos; // Legacy
            initialGhostPos = ghosts[0].pos;
            initialAgentPos = [start[0], start[1]];
            
            if (typeof Pacman3D !== 'undefined') Pacman3D.setGhosts(ghosts);

            btnAdvStep.disabled = false;
            btnAdvPlay.disabled = false;
            instructionText.innerHTML = `<strong>Ghosts Spawned!</strong> 4 ghosts deployed. Select Arcade Mode to begin real-time play.`;
        });

        advDepthSlider.addEventListener('input', () => {
            lblAdvDepth.textContent = advDepthSlider.value;
        });

        if (advControlSelect) {
            advControlSelect.addEventListener('change', () => {
                if (advControlSelect.value === 'manual') {
                    btnAdvStep.classList.add('hidden');
                    btnAdvPlay.classList.add('hidden');
                    if (advAlgoContainer) advAlgoContainer.classList.add('hidden');
                    document.getElementById('pacman-score-container').classList.remove('hidden');
                    instructionText.innerHTML = `<strong>Arcade Mode Active:</strong> Use Arrow Keys to navigate and eat pellets!`;
                    if (!arcadeInterval) arcadeInterval = setInterval(arcadeTick, 300);
                } else {
                    btnAdvStep.classList.remove('hidden');
                    btnAdvPlay.classList.remove('hidden');
                    if (advAlgoContainer) advAlgoContainer.classList.remove('hidden');
                    document.getElementById('pacman-score-container').classList.add('hidden');
                    instructionText.innerHTML = `<strong>AI Mode Active:</strong> Use Step or Auto-Play.`;
                    if (arcadeInterval) { clearInterval(arcadeInterval); arcadeInterval = null; }
                }
            });
        }

        btnAdvStep.addEventListener('click', () => {
            stopAdversarial();
            stepAdversarial(false);
        });

        btnAdvPlay.addEventListener('click', () => {
            if (isAdversarialPlaying) {
                stopAdversarial();
            } else {
                playAdversarial();
            }
        });

        btnAdvReset.addEventListener('click', resetAdversarial);

        // Probabilistic Controls
        btnHmmStep.addEventListener('click', () => {
            updateHMMBelief();
        });

        btnHmmReset.addEventListener('click', () => {
            resetHMMBelief();
            clearHeatmapVisuals();
            instructionText.innerHTML = `<strong>HMM Reset:</strong> Ghost tracking distribution cleared.`;
        });

        btnRunVe.addEventListener('click', runVariableElimination);

        // Hybrid Controls
        hybridRiskSlider.addEventListener('input', () => {
            lblHybridRisk.textContent = hybridRiskSlider.value;
        });

        btnHybridRun.addEventListener('click', runHybridDecision);
    }

    function setupTabEvents() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.getAttribute('data-tab');
                
                tabBtns.forEach(b => b.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                
                btn.classList.add('active');
                document.getElementById(targetTab).classList.add('active');
            });
        });
    }

    function setupAccordionEvents() {
        const accordionHeaders = document.querySelectorAll('.accordion-header');
        accordionHeaders.forEach(header => {
            // Expand first item initially, keep others collapsed
            const body = header.nextElementSibling;
            if (header.textContent.includes('Performance')) {
                body.classList.remove('hidden');
            } else {
                body.classList.add('hidden');
            }
            
            header.addEventListener('click', () => {
                body.classList.toggle('hidden');
            });
        });
    }

    // === GRID INTERACTIVE DRAWING & RENDERING ===
    
    function resizeGrid() {
        const parent = gridContainer.parentElement;
        if (!parent) return;
        
        // Use timeout to let the browser resolve new layout dimensions if tabs just switched
        setTimeout(() => {
            const maxW = parent.clientWidth - 32;
            const maxH = parent.clientHeight - 32;
            
            const ratio = cols / rows;
            let finalW = maxW;
            let finalH = maxW / ratio;
            
            if (finalH > maxH) {
                finalH = maxH;
                finalW = maxH * ratio;
            }
            
            if (finalW > 50 && finalH > 50) {
                gridContainer.style.width = `${finalW}px`;
                gridContainer.style.height = `${finalH}px`;
            }
        }, 0);
    }

    function sync3DMaze() {
        if (typeof Pacman3D !== 'undefined' && document.getElementById('pacman-3d-canvas').children.length > 0) {
            const shapeSelect = document.getElementById('shape-select');
            const shape = shapeSelect ? shapeSelect.value : 'cube';
            Pacman3D.generateMaze(grid, start, typeof ghostPos !== 'undefined' ? ghostPos : null, shape);
        }
    }

    function generateGrid(gridData, startData, goalData) {
        grid = gridData;
        rows = gridData.length;
        cols = gridData[0].length;
        start = startData;
        goal = goalData;
        
        // Configure dynamic CSS grid template columns/rows
        gridContainer.style.gridTemplateRows = `repeat(${rows}, 1fr)`;
        gridContainer.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
        gridContainer.style.aspectRatio = `${cols} / ${rows}`;
        gridContainer.innerHTML = '';
        
        pacmanScore = 0;
        const scoreEl = document.getElementById('val-pacman-score');
        if (scoreEl) scoreEl.textContent = pacmanScore;
        
        if (typeof Pacman3D !== 'undefined') {
            const shapeSelect = document.getElementById('shape-select');
            const shape = shapeSelect ? shapeSelect.value : 'cube';
            Pacman3D.generateMaze(grid, start, typeof ghostPos !== 'undefined' ? ghostPos : null, shape);
        }

        // Dynamically size grid to fit viewport
        resizeGrid();

        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const cellEl = document.createElement('div');
                cellEl.classList.add('cell');
                cellEl.dataset.row = r;
                cellEl.dataset.col = c;
                cellEl.id = `cell-${r}-${c}`;
                
                // Set initial status class
                if (r === start[0] && c === start[1]) {
                    cellEl.classList.add('start');
                    cellEl.textContent = 'S';
                } else if (r === goal[0] && c === goal[1]) {
                    cellEl.classList.add('goal');
                    cellEl.textContent = 'G';
                } else if (grid[r][c] === 1) {
                    cellEl.classList.add('wall');
                } else if (grid[r][c] === 2) {
                    cellEl.classList.add('mud');
                } else if (grid[r][c] === 3) {
                    cellEl.classList.add('water');
                } else if (grid[r][c] === 0) {
                    const pellet = document.createElement('div');
                    pellet.classList.add('pellet');
                    cellEl.appendChild(pellet);
                }
                
                setupCellInteractions(cellEl, r, c);
                gridContainer.appendChild(cellEl);
            }
        }
        
        updateGridVisibility();
    }

    function applyTool(r, c, cellEl) {
        if ((r === start[0] && c === start[1]) || (r === goal[0] && c === goal[1])) return;
        
        cellEl.classList.remove('wall', 'mud', 'water');
        
        if (activeTool === 'wall') {
            grid[r][c] = 1;
            cellEl.classList.add('wall');
        } else if (activeTool === 'mud') {
            grid[r][c] = 2;
            cellEl.classList.add('mud');
        } else if (activeTool === 'water') {
            grid[r][c] = 3;
            cellEl.classList.add('water');
        } else if (activeTool === 'erase') {
            grid[r][c] = 0;
        }
    }

    function setupCellInteractions(cellEl, r, c) {
        // Mousedown handler initiates drawing or drag-and-drop
        cellEl.addEventListener('mousedown', (e) => {
            e.preventDefault();
            stopAnimation();
            clearPathVisuals();
            solvedPath = [];
            steps = [];
            resetPlaybackUI();
            
            if (isGhostPlacementMode) {
                // Remove previous ghost cell visual
                if (ghostPos) {
                    const oldGhostCell = document.getElementById(`cell-${ghostPos[0]}-${ghostPos[1]}`);
                    if (oldGhostCell) {
                        oldGhostCell.classList.remove('ghost');
                        oldGhostCell.textContent = '';
                    }
                }
                ghostPos = [r, c];
                initialGhostPos = [r, c];
                initialAgentPos = [start[0], start[1]];
                if (typeof Pacman3D !== 'undefined') Pacman3D.setGhostPos(ghostPos);
                cellEl.classList.add('ghost');
                cellEl.textContent = 'G';
                isGhostPlacementMode = false;
                document.body.style.cursor = 'default';
                
                // Enable game control buttons
                btnAdvStep.disabled = false;
                btnAdvPlay.disabled = false;
                btnHmmStep.disabled = false;
                btnHybridRun.disabled = false;

                // Reset tracking belief distribution
                resetHMMBelief();

                instructionText.innerHTML = `<strong>Ghost Placed!</strong> Ready to run Adversarial search (Game tab), HMM tracking (Bayes tab), or Expected Utility decision loops (Hybrid tab).`;
                return;
            }

            if (r === start[0] && c === start[1]) {
                isDraggingStart = true;
                document.body.style.cursor = 'grabbing';
            } else if (r === goal[0] && c === goal[1]) {
                isDraggingGoal = true;
                document.body.style.cursor = 'grabbing';
            } else {
                isDrawing = true;
                applyTool(r, c, cellEl);
            }
        });

        // Mouseenter handler handles continuing drag drawing/dragging icons
        cellEl.addEventListener('mouseenter', () => {
            if (isDraggingStart) {
                // Ensure we don't drag start marker onto walls/weights or the goal marker
                if (grid[r][c] === 0 && !(r === goal[0] && c === goal[1])) {
                    // Update start cell in UI
                    const prevStartCell = document.getElementById(`cell-${start[0]}-${start[1]}`);
                    if (prevStartCell) {
                        prevStartCell.classList.remove('start');
                        prevStartCell.textContent = '';
                    }
                    start = [r, c];
                    cellEl.classList.add('start');
                    cellEl.textContent = 'S';
                    updateGridVisibility();
                    if (typeof Pacman3D !== 'undefined') Pacman3D.setAgentPos(start);
                }
            } else if (isDraggingGoal) {
                // Ensure we don't drag goal marker onto walls/weights or the start marker
                if (grid[r][c] === 0 && !(r === start[0] && c === start[1])) {
                    // Update goal cell in UI
                    const prevGoalCell = document.getElementById(`cell-${goal[0]}-${goal[1]}`);
                    if (prevGoalCell) {
                        prevGoalCell.classList.remove('goal');
                        prevGoalCell.textContent = '';
                    }
                    goal = [r, c];
                    cellEl.classList.add('goal');
                    cellEl.textContent = 'G';
                }
            } else if (isDrawing) {
                applyTool(r, c, cellEl);
            }
        });
    }

    function updateGridVisibility() {
        const isPartiallyObservable = chkPartiallyObservable.checked;
        const visionRadius = parseInt(visionRadiusSlider.value);
        
        // Reference node to hide things around (current active search frame or start)
        let observer = start;
        if (currentFrameIndex >= 0 && currentFrameIndex < steps.length) {
            observer = steps[currentFrameIndex].current;
        }

        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const cellEl = document.getElementById(`cell-${r}-${c}`);
                if (!cellEl) continue;

                if (isPartiallyObservable) {
                    // Manhattan distance check: abs(dr) + abs(dc) <= radius
                    const distance = Math.abs(r - observer[0]) + Math.abs(c - observer[1]);
                    if (distance <= visionRadius) {
                        cellEl.classList.remove('fog');
                    } else {
                        cellEl.classList.add('fog');
                    }
                } else {
                    cellEl.classList.remove('fog');
                }
            }
        }
    }

    function renderHeuristicHeatmap() {
        let maxDist = 0;
        // Calculate max dist for normalization
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                if (grid[r][c] !== 1) { // not a wall
                    const dist = Math.abs(r - goal[0]) + Math.abs(c - goal[1]);
                    if (dist > maxDist) maxDist = dist;
                }
            }
        }
        
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const cellEl = document.getElementById(`cell-${r}-${c}`);
                if (!cellEl || grid[r][c] === 1) continue;
                
                const dist = Math.abs(r - goal[0]) + Math.abs(c - goal[1]);
                const intensity = Math.max(0, 1 - (dist / maxDist));
                // Professional warm heat color: RGBA(255, 81, 47, alpha)
                cellEl.style.backgroundColor = `rgba(255, 81, 47, ${intensity * 0.5})`;
            }
        }
    }

    function removeHeuristicHeatmap() {
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const cellEl = document.getElementById(`cell-${r}-${c}`);
                if (cellEl) cellEl.style.backgroundColor = '';
            }
        }
    }

    function clearPathVisuals() {
        const cells = document.querySelectorAll('.cell');
        cells.forEach(c => {
            c.classList.remove('visited', 'frontier', 'path', 'current-node', 
                               'csp-red', 'csp-green', 'csp-blue', 'csp-waypoint', 'adv-path');
            c.removeAttribute('data-slot');
            if (!c.classList.contains('start') && !c.classList.contains('goal') && !c.classList.contains('ghost')) {
                c.textContent = '';
            }
        });
        cspResultsContainer.classList.add('hidden');
        
        if (typeof Pacman3D !== 'undefined') {
            Pacman3D.updateSearchState([], [], start);
            Pacman3D.setAgentPos(start);
        }
    }

    // === API HANDLERS ===

    function callGenerateApi() {
        const preset = presetSelect.value;
        const payload = {
            type: preset,
            rows: parseInt(rowsInput.value),
            cols: parseInt(colsInput.value),
            seed: parseInt(seedInput.value)
        };

        setLoading(true);
        fetch('/api/maze/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => {
            if (!res.ok) throw new Error('API request failed');
            return res.json();
        })
        .then(data => {
            setLoading(false);
            apiStatus.className = 'status-indicator online';
            apiStatus.textContent = 'Connected';
            
            generateGrid(data.grid, data.start, data.goal);
            clearPathVisuals();
            resetPlaybackUI();
            resetStatsUI();
        })
        .catch(err => {
            setLoading(false);
            apiStatus.className = 'status-indicator offline';
            apiStatus.textContent = 'Connection Error';
            alert('Failed to generate maze. Ensure backend is running.');
            console.error(err);
        });
    }

    function callSolveApi() {
        const payload = {
            grid: grid,
            start: start,
            goal: goal,
            algorithm: algoSelect.value,
            heuristic: heuristicSelect.value,
            weight: parseFloat(weightSlider.value)
        };

        instructionText.innerHTML = `<strong>Solving...</strong> Calling the backend API for algorithm ${algoSelect.value.toUpperCase()}.`;
        setLoading(true);

        fetch('/api/maze/solve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => {
            if (!res.ok) throw new Error('Solver API request failed');
            return res.json();
        })
        .then(data => {
            setLoading(false);
            
            if (data.error) {
                alert('Solver failed: ' + data.error);
                return;
            }

            // Save results to state
            steps = data.steps;
            solvedPath = data.path;
            
            // Update stats layout
            renderStats(data.stats, algoSelect.value);
            
            // Set up playback visual elements
            clearPathVisuals();
            currentFrameIndex = 0;
            enablePlaybackControls(true);
            
            // Update animation status
            lblAnimStatus.textContent = 'Solved. Ready to Play.';
            lblStepCount.textContent = `0 / ${steps.length}`;
            animProgressBar.style.width = '0%';
            
            // Start play immediately
            startPlayback();
            
            instructionText.innerHTML = `<strong>Solved!</strong> Visited nodes are cyan, frontier cells are amber, and the final solved route will be golden.`;
        })
        .catch(err => {
            setLoading(false);
            alert('Failed to solve maze. Verify backend app.py is running.');
            console.error(err);
        });
    }

    function runCspColoring() {
        if (!solvedPath || solvedPath.length < 2) {
            alert('Please solve the maze first to obtain a path for coloring!');
            return;
        }

        const payload = {
            path: solvedPath,
            n_colors: parseInt(cspColorsNum.value)
        };

        fetch('/api/csp/color', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            cspResultsContainer.classList.remove('hidden');
            cspResultsTitle.innerHTML = '<i class="fa-solid fa-palette"></i> 3-Coloring Results';
            
            if (data.success) {
                // Clear any previous coloring
                document.querySelectorAll('.cell').forEach(c => {
                    c.classList.remove('csp-red', 'csp-green', 'csp-blue');
                });
                
                // Color mapping: 0 -> Red, 1 -> Green, 2 -> Blue
                const classMap = { 0: 'csp-red', 1: 'csp-green', 2: 'csp-blue' };
                const textMap = { 0: 'Red', 1: 'Green', 2: 'Blue' };
                let outputStr = "Color Assignment:\n";
                
                for (const [cellKey, colorIdx] of Object.entries(data.colors)) {
                    // Extract row and col from key: cell_r_c
                    const parts = cellKey.split('_');
                    const r = parts[1];
                    const c = parts[2];
                    
                    const cellEl = document.getElementById(`cell-${r}-${c}`);
                    if (cellEl && !(r == start[0] && c == start[1]) && !(r == goal[0] && c == goal[1])) {
                        cellEl.classList.add(classMap[colorIdx]);
                    }
                    outputStr += `  Cell (${r}, ${c}) → ${textMap[colorIdx]}\n`;
                }
                cspResultsContent.textContent = outputStr;
                instructionText.innerHTML = `<strong>Constraint Satisfied!</strong> Path cells colored Red, Green, or Blue. No adjacent cells share a color.`;
            } else {
                cspResultsContent.textContent = `FAILED: ${data.error}`;
            }
        })
        .catch(err => {
            alert('Error running CSP coloring.');
            console.error(err);
        });
    }

    function runCspScheduling() {
        if (!solvedPath || solvedPath.length < 2) {
            alert('Please solve the maze first to schedule waypoints!');
            return;
        }

        const payload = { path: solvedPath };

        fetch('/api/csp/schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            cspResultsContainer.classList.remove('hidden');
            cspResultsTitle.innerHTML = '<i class="fa-solid fa-clock"></i> Waypoint Scheduling Results';
            
            if (data.success) {
                // Clear previous waypoints
                document.querySelectorAll('.cell').forEach(c => {
                    c.classList.remove('csp-waypoint');
                    c.removeAttribute('data-slot');
                });

                let outputStr = "Schedule Timeline:\n";
                
                for (const [cellKey, timeSlot] of Object.entries(data.schedule)) {
                    const parts = cellKey.split('_');
                    const r = parts[1];
                    const c = parts[2];
                    
                    const cellEl = document.getElementById(`cell-${r}-${c}`);
                    if (cellEl) {
                        cellEl.classList.add('csp-waypoint');
                        cellEl.setAttribute('data-slot', `T${timeSlot}`);
                    }
                    outputStr += `  Checkpoint (${r}, ${c}) scheduled for Time Slot T_${timeSlot}\n`;
                }
                
                cspResultsContent.textContent = outputStr;
                instructionText.innerHTML = `<strong>Scheduling Feasible!</strong> Checkpoints marked on grid with dashed borders and time slot order.`;
            } else {
                cspResultsContent.textContent = `FAILED: ${data.error}`;
            }
        })
        .catch(err => {
            alert('Error running waypoint scheduler.');
            console.error(err);
        });
    }

    function runBenchmarks() {
        const payload = {
            grid: grid,
            start: start,
            goal: goal
        };

        instructionText.innerHTML = '<strong>Running Benchmarks...</strong> Running all search algorithms on current layout.';
        setLoading(true);

        fetch('/api/maze/benchmark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            setLoading(false);
            
            benchmarkTableBody.innerHTML = '';
            benchmarkTable.classList.remove('hidden');
            benchmarkAnalysisPanel.classList.remove('hidden');
            
            // Find best algorithms: shortest path length, fewest nodes expanded
            let bestLength = Infinity;
            let bestExpanded = Infinity;
            let shortestAlgos = [];
            let fastestAlgos = [];

            // Render table rows
            data.results.forEach(res => {
                const tr = document.createElement('tr');
                
                if (res.solved) {
                    if (res.path_length < bestLength) {
                        bestLength = res.path_length;
                        shortestAlgos = [res.algorithm];
                    } else if (res.path_length === bestLength) {
                        shortestAlgos.push(res.algorithm);
                    }
                    
                    if (res.nodes_expanded < bestExpanded) {
                        bestExpanded = res.nodes_expanded;
                        fastestAlgos = [res.algorithm];
                    } else if (res.nodes_expanded === bestExpanded) {
                        fastestAlgos.push(res.algorithm);
                    }
                }

                tr.innerHTML = `
                    <td><strong>${res.algorithm}</strong></td>
                    <td>${res.solved ? res.path_length : '<span class="text-rose">✗</span>'}</td>
                    <td>${res.solved ? res.nodes_expanded : '-'}</td>
                    <td>${res.solved ? res.peak_frontier : '-'}</td>
                    <td>${res.solved ? res.elapsed_ms.toFixed(2) + ' ms' : '-'}</td>
                `;
                
                benchmarkTableBody.appendChild(tr);
            });

            // Highlight rows that are shortest (optimal)
            const rows = benchmarkTableBody.querySelectorAll('tr');
            rows.forEach((row, idx) => {
                const res = data.results[idx];
                if (res.solved && res.path_length === bestLength) {
                    row.classList.add('best-algo-row');
                }
            });

            // Generate analytical text
            let analysis = `<strong>Optimal Path Length:</strong> ${bestLength} cells (found by: ${shortestAlgos.join(', ')}).<br><br>`;
            analysis += `<strong>Maximum Search Efficiency:</strong> ${fastestAlgos.join(', ')} expanded the fewest nodes (${bestExpanded} cells) to find its path.<br><br>`;
            analysis += `<em>Notice:</em> BFS, UCS, and A* are guaranteed to find the optimal path. A* is significantly more efficient than BFS/UCS because its heuristic directs the search, reducing expanded nodes.`;
            
            benchmarkAnalysisText.innerHTML = analysis;
            instructionText.innerHTML = '<strong>Benchmarks Complete.</strong> Check the Benchmark tab on the right to compare results!';
        })
        .catch(err => {
            setLoading(false);
            alert('Benchmark failed.');
            console.error(err);
        });
    }

    // === ANIMATION ENGINE ===

    function togglePlayPause() {
        if (isPlaying) {
            stopAnimation();
        } else {
            startPlayback();
        }
    }

    function startPlayback() {
        if (steps.length === 0) return;
        isPlaying = true;
        btnPlayPause.innerHTML = '<i class="fa-solid fa-pause"></i>';
        lblAnimStatus.textContent = 'Running Search...';
        
        // If animation completed previously, restart from 0
        if (currentFrameIndex >= steps.length) {
            currentFrameIndex = 0;
            clearPathVisuals();
        }
        
        animationLoop();
    }

    function stopAnimation() {
        isPlaying = false;
        btnPlayPause.innerHTML = '<i class="fa-solid fa-play"></i>';
        lblAnimStatus.textContent = 'Paused';
        if (animationTimeout) {
            clearTimeout(animationTimeout);
            animationTimeout = null;
        }
    }

    function animationLoop() {
        if (!isPlaying) return;
        
        renderAnimationFrame(currentFrameIndex);
        
        currentFrameIndex++;
        
        if (currentFrameIndex < steps.length) {
            animationTimeout = setTimeout(animationLoop, animationSpeed);
        } else {
            // Reached end of exploration, animate final path
            isPlaying = false;
            btnPlayPause.innerHTML = '<i class="fa-solid fa-play"></i>';
            lblAnimStatus.textContent = 'Drawing Final Path...';
            
            animateFinalPath(0);
        }
    }

    function renderAnimationFrame(index) {
        if (index < 0 || index >= steps.length) return;
        
        const frame = steps[index];
        const current = frame.current;
        const visited = frame.visited;
        const frontier = frame.frontier;
        
        // Remove previous active markers
        const prevActive = document.querySelector('.cell.current-node');
        if (prevActive) prevActive.classList.remove('current-node');
        
        // Apply visited status
        visited.forEach(([r, c]) => {
            const el = document.getElementById(`cell-${r}-${c}`);
            if (el && !(r === start[0] && c === start[1])) {
                el.classList.remove('frontier');
                el.classList.add('visited');
            }
        });
        
        // Apply frontier status
        frontier.forEach(([r, c]) => {
            const el = document.getElementById(`cell-${r}-${c}`);
            if (el && !el.classList.contains('visited') && !(r === start[0] && c === start[1])) {
                el.classList.add('frontier');
            }
        });
        
        // Apply active cell highlighting
        const activeEl = document.getElementById(`cell-${current[0]}-${current[1]}`);
        if (activeEl && !(current[0] === start[0] && current[1] === start[1])) {
            activeEl.classList.add('current-node');
        }
        
        // Sync 3D Search State
        if (typeof Pacman3D !== 'undefined') {
            Pacman3D.updateSearchState(visited, frontier, current);
        }
        
        // Update vision fog of war
        updateGridVisibility();
        
        // Progress elements
        lblStepCount.textContent = `${index + 1} / ${steps.length}`;
        const percentage = ((index + 1) / steps.length) * 100;
        animProgressBar.style.width = `${percentage}%`;
    }

    function animateFinalPath(pathIndex) {
        if (!solvedPath || solvedPath.length === 0) {
            lblAnimStatus.textContent = 'Finished (No path exists)';
            return;
        }

        if (pathIndex < solvedPath.length) {
            const [r, c] = solvedPath[pathIndex];
            const el = document.getElementById(`cell-${r}-${c}`);
            if (el && !(r === start[0] && c === start[1]) && !(r === goal[0] && c === goal[1])) {
                el.classList.add('path');
            }
            
            if (typeof Pacman3D !== 'undefined') {
                Pacman3D.setAgentPos([r, c]);
                // We update the path cumulatively in 3D
                Pacman3D.setFinalPath(solvedPath.slice(0, pathIndex + 1));
            }
            
            // Chain animations
            setTimeout(() => animateFinalPath(pathIndex + 1), 25);
        } else {
            lblAnimStatus.textContent = 'Goal Reached!';
            instructionText.innerHTML = `<strong>Solved!</strong> Found path of length ${solvedPath.length} cells. Try running <strong>CSP Coloring</strong> on the details panel.`;
        }
    }

    function stepForward() {
        stopAnimation();
        if (currentFrameIndex < steps.length - 1) {
            currentFrameIndex++;
            renderAnimationFrame(currentFrameIndex);
        } else if (currentFrameIndex === steps.length - 1) {
            // Trigger path draw
            currentFrameIndex++;
            animateFinalPath(0);
        }
    }

    function stepBackward() {
        stopAnimation();
        if (currentFrameIndex > 0) {
            // Clearing path overlays if stepping back from completed path
            if (currentFrameIndex >= steps.length) {
                document.querySelectorAll('.cell').forEach(c => c.classList.remove('path'));
            }
            
            currentFrameIndex--;
            
            // To re-render at frame index, we must clear grid and re-render frame
            clearPathVisuals();
            renderAnimationFrame(currentFrameIndex);
        }
    }

    function resetAnimation() {
        stopAnimation();
        clearPathVisuals();
        currentFrameIndex = 0;
        lblStepCount.textContent = `0 / ${steps.length}`;
        animProgressBar.style.width = '0%';
        lblAnimStatus.textContent = 'Reset';
        updateGridVisibility();
    }

    // === UI CONTROLLER HELPERS ===

    function setLoading(isLoading) {
        if (isLoading) {
            btnSolve.disabled = true;
            btnGenerate.disabled = true;
            btnRunBenchmark.disabled = true;
        } else {
            btnSolve.disabled = false;
            btnGenerate.disabled = false;
            btnRunBenchmark.disabled = false;
        }
    }

    function enablePlaybackControls(enable) {
        btnPlayPause.disabled = !enable;
        btnStepPrev.disabled = !enable;
        btnStepNext.disabled = !enable;
        btnResetAnim.disabled = !enable;
    }

    function resetPlaybackUI() {
        enablePlaybackControls(false);
        btnPlayPause.innerHTML = '<i class="fa-solid fa-play"></i>';
        lblAnimStatus.textContent = 'Idle';
        lblStepCount.textContent = '0 / 0';
        animProgressBar.style.width = '0%';
        currentFrameIndex = -1;
    }

    function resetStatsUI() {
        statAlgo.textContent = '-';
        statExpanded.textContent = '-';
        statPathLen.textContent = '-';
        statFrontier.textContent = '-';
        statTime.textContent = '-';
        statSolved.textContent = '-';
        infoCardPanel.classList.add('hidden');
    }

    function renderStats(stats, origAlgo) {
        statAlgo.textContent = stats.algorithm;
        statExpanded.textContent = stats.nodes_expanded;
        statPathLen.textContent = stats.solved ? stats.path_length : 'Unsolvable';
        statFrontier.textContent = stats.peak_frontier;
        statTime.textContent = `${stats.elapsed_ms.toFixed(2)} ms`;
        statSolved.textContent = stats.solved ? 'Success' : 'No Path';
        statSolved.className = `stat-value ${stats.solved ? 'text-emerald' : 'text-rose'}`;
        
        infoCardPanel.classList.remove('hidden');
        infoCardText.innerHTML = getAlgorithmBehaviorText(origAlgo, stats.solved);
    }

    function getAlgorithmBehaviorText(algo, solved) {
        if (!solved) {
            return `The search failed to find a valid route between the start and goal. No path exists under the current grid configuration.`;
        }

        switch (algo) {
            case 'bfs':
                return `<strong>BFS (Breadth-First Search)</strong> operates layer-by-layer using a FIFO queue. It is guaranteed to find the <strong>optimal (shortest) path</strong>. Notice that it expands nodes in circular rings, exploring in all directions uniformly.`;
            case 'bidirectional_bfs':
                return `<strong>Bidirectional BFS</strong> runs two simultaneous Breadth-First Searches: one forward from the start state, and one backward from the goal state. They meet in the middle, which dramatically reduces the search space (nodes expanded) while still guaranteeing an <strong>optimal (shortest) path</strong>.`;
            case 'dfs':
                return `<strong>DFS (Depth-First Search)</strong> uses a LIFO stack, diving deep along a single branch before backtracking. It is <strong>suboptimal</strong>, often finding winding, inefficient paths. However, it can expand far fewer nodes if it happens to head in the right direction.`;
            case 'ucs':
                return `<strong>UCS (Uniform Cost Search)</strong> expands nodes based on path cost using a priority queue. Notice that in this weighted layout, UCS will steer around high-cost terrain (Mud cost=3.0, Water cost=6.0) to find the path of <strong>minimum total cost</strong>, unlike standard BFS which ignores cell costs.`;
            case 'greedy':
                return `<strong>Greedy Best-First Search</strong> prioritizes nodes solely using the heuristic function $h(n)$ (estimated distance to goal). It expands nodes rapidly in a straight beam towards the goal, reducing expanded nodes, but is <strong>suboptimal</strong> and can get stuck in walls.`;
            case 'astar':
                return `<strong>A* Search</strong> is the industry standard. It evaluates nodes using $f(n) = g(n) + h(n)$, combining cost-so-far and estimated cost to goal. It is <strong>admissible and optimal</strong>, finding the shortest/cheapest path while expanding far fewer nodes than BFS/UCS.`;
            case 'weighted_astar':
                return `<strong>Weighted A*</strong> increases the influence of the heuristic: $f(n) = g(n) + w \cdot h(n)$. This biases the agent to rush towards the goal, expanding fewer nodes (behaving more like Greedy), but potentially sacrificing path optimality.`;
            default:
                return `Solved using search pathfinding. Explore stats above or run benchmarks to see performance differences.`;
        }
    }

    function setupToolEvents() {
        const toolWall = document.getElementById('tool-wall');
        const toolMud = document.getElementById('tool-mud');
        const toolWater = document.getElementById('tool-water');
        const toolErase = document.getElementById('tool-erase');

        const tools = [
            { el: toolWall, val: 'wall' },
            { el: toolMud, val: 'mud' },
            { el: toolWater, val: 'water' },
            { el: toolErase, val: 'erase' }
        ];

        tools.forEach(t => {
            if (t.el) {
                t.el.addEventListener('click', () => {
                    tools.forEach(x => { if (x.el) x.el.classList.remove('active'); });
                    t.el.classList.add('active');
                    activeTool = t.val;
                });
            }
        });
    }

    // ==============================================================================
    // ADVERSARIAL MULTI-AGENT SIMULATOR (CO4)
    // ==============================================================================

    function arcadeTick() {
        if (!ghosts || ghosts.length === 0) return;
        
        let nr = start[0], nc = start[1];
        let moved = false;
        
        if (queuedDirection) {
            let qr = nr + queuedDirection[0];
            let qc = nc + queuedDirection[1];
            if (qr >= 0 && qr < rows && qc >= 0 && qc < cols && grid[qr][qc] !== 1) {
                currentDirection = queuedDirection;
                queuedDirection = null;
            }
        }
        
        if (currentDirection) {
            let cr = nr + currentDirection[0];
            let cc = nc + currentDirection[1];
            if (cr >= 0 && cr < rows && cc >= 0 && cc < cols && grid[cr][cc] !== 1) {
                start = [cr, cc];
                moved = true;
            }
        }
        
        if (moved) {
            const cellEl = document.getElementById(`cell-${start[0]}-${start[1]}`);
            if (cellEl) {
                const pellet = cellEl.querySelector('.pellet');
                if (pellet) {
                    pellet.remove();
                    pacmanScore += 10;
                    document.getElementById('val-pacman-score').textContent = pacmanScore;
                    if (typeof Pacman3D !== 'undefined') Pacman3D.eatPellet(start[0], start[1]);
                }
            }
            
            if (!isApiBusy) {
                stepAdversarial(true);
            }
        }
    }

    function stepAdversarial(isManual = false) {
        if (!ghosts || ghosts.length === 0) {
            if (!isManual) alert('Please scatter the Ghosts first.');
            return;
        }

        const payload = {
            grid: grid,
            agent_pos: start,
            agent_dir: currentDirection || [0, 0],
            ghosts: ghosts,
            mode: isManual ? 'manual' : advAlgoSelect.value,
            depth: parseInt(advDepthSlider.value)
        };
        
        isApiBusy = true;

        fetch('/api/adversarial/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            isApiBusy = false;
            if (data.error) {
                alert('Adversarial logic failed: ' + data.error);
                stopAdversarial();
                return;
            }

            // Remove old visual markers
            const oldAgentCell = document.getElementById(`cell-${start[0]}-${start[1]}`);
            if (oldAgentCell) {
                oldAgentCell.classList.remove('start');
                if (!oldAgentCell.querySelector('.pellet')) oldAgentCell.textContent = '';
            }
            ghosts.forEach(g => {
                const oldGhostCell = document.getElementById(`cell-${g.pos[0]}-${g.pos[1]}`);
                if (oldGhostCell) {
                    oldGhostCell.classList.remove('ghost');
                    if (!oldGhostCell.querySelector('.pellet')) oldGhostCell.textContent = '';
                }
            });

            // Clear previous predicted paths
            document.querySelectorAll('.cell.adv-path').forEach(c => {
                c.classList.remove('adv-path');
                if (!c.querySelector('.pellet') && !c.classList.contains('ghost') && !c.classList.contains('start')) {
                    c.textContent = '';
                }
            });

            // Update State Variables
            start = data.next_agent_move;
            ghosts = data.next_ghosts;
            ghostPos = ghosts[0].pos; // Legacy support

            if (typeof Pacman3D !== 'undefined') {
                Pacman3D.animateMove(start, ghosts, 300);
            }

            // Render new positions
            const newAgentCell = document.getElementById(`cell-${start[0]}-${start[1]}`);
            if (newAgentCell) {
                newAgentCell.classList.add('start');
            }
            ghosts.forEach(g => {
                const newGhostCell = document.getElementById(`cell-${g.pos[0]}-${g.pos[1]}`);
                if (newGhostCell) {
                    newGhostCell.classList.add('ghost');
                }
            });

            // Render new predicted paths sequentially (animated explanation)
            if (data.predicted_agent_path && data.predicted_agent_path.length > 0) {
                data.predicted_agent_path.forEach(([r, c], idx) => {
                    setTimeout(() => {
                        const cellEl = document.getElementById(`cell-${r}-${c}`);
                        const isGhost = ghosts.some(g => g.pos[0] === r && g.pos[1] === c);
                        if (cellEl && !(r === data.next_agent_move[0] && c === data.next_agent_move[1]) && !isGhost) {
                            cellEl.classList.add('adv-path');
                            if (!cellEl.querySelector('.pellet')) cellEl.textContent = idx + 1; // Show step sequence
                        }
                    }, idx * 50);
                });
            }

            advStatusPanel.classList.remove('hidden');
            advStatusText.innerHTML = `
                <strong>Opponent Evaluation:</strong> ${data.evaluation.toFixed(2)}<br>
                <strong>Agent Move:</strong> (${start[0]}, ${start[1]})<br>
                <strong>Score:</strong> ${pacmanScore}
            `;

            // Check game termination conditions
            let caught = ghosts.some(g => g.pos[0] === start[0] && g.pos[1] === start[1]);
            
            if (start[0] === goal[0] && start[1] === goal[1]) {
                stopAdversarial();
                instructionText.innerHTML = `<strong>VICTORY!</strong> The Agent successfully navigated to the goal while evading the Ghosts!`;
                alert('Victory! Agent reached the goal!');
            } else if (caught) {
                stopAdversarial();
                if (arcadeInterval) {
                    clearInterval(arcadeInterval);
                    arcadeInterval = null;
                }
                instructionText.innerHTML = `<strong>DEFEAT!</strong> A Ghost caught the Agent! Try a different strategy or play again.`;
                alert('Defeat! The Ghost caught the Agent! Score: ' + pacmanScore);
            }
        })
        .catch(err => {
            console.error(err);
            isApiBusy = false;
            stopAdversarial();
        });
    }

    function playAdversarial() {
        isAdversarialPlaying = true;
        btnAdvPlay.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
        btnAdvPlay.className = 'btn btn-secondary';
        instructionText.innerHTML = `<strong>Running Adversarial Loop...</strong> Watching minimax tree vs stochastic chase logic.`;
        
        function loop() {
            if (!isAdversarialPlaying) return;
            stepAdversarial();
            // Loop step time delay based on speed slider, wait longer to let path animations finish
            adversarialTimeout = setTimeout(loop, Math.max(500, animationSpeed * 8));
        }
        loop();
    }

    function stopAdversarial() {
        isAdversarialPlaying = false;
        btnAdvPlay.innerHTML = '<i class="fa-solid fa-play"></i> Auto-Play';
        btnAdvPlay.className = 'btn btn-primary';
        if (adversarialTimeout) {
            clearTimeout(adversarialTimeout);
            adversarialTimeout = null;
        }
    }

    function resetAdversarial() {
        stopAdversarial();
        if (initialAgentPos && initialGhostPos) {
            // Remove current positions from grid
            const currentAgentCell = document.getElementById(`cell-${start[0]}-${start[1]}`);
            if (currentAgentCell) {
                currentAgentCell.classList.remove('start');
                currentAgentCell.textContent = '';
            }
            const currentGhostCell = document.getElementById(`cell-${ghostPos[0]}-${ghostPos[1]}`);
            if (currentGhostCell) {
                currentGhostCell.classList.remove('ghost');
                currentGhostCell.textContent = '';
            }

            // Restore initial values
            start = [initialAgentPos[0], initialAgentPos[1]];
            ghostPos = [initialGhostPos[0], initialGhostPos[1]];
            
            if (typeof Pacman3D !== 'undefined') {
                Pacman3D.setAgentPos(start);
                Pacman3D.setGhostPos(ghostPos);
            }

            // Clear previous predicted paths
            document.querySelectorAll('.cell.adv-path').forEach(c => {
                c.classList.remove('adv-path');
                c.textContent = '';
            });

            // Re-render
            const initialAgentCell = document.getElementById(`cell-${start[0]}-${start[1]}`);
            if (initialAgentCell) {
                initialAgentCell.classList.add('start');
                initialAgentCell.textContent = 'S';
            }
            const initialGhostCell = document.getElementById(`cell-${ghostPos[0]}-${ghostPos[1]}`);
            if (initialGhostCell) {
                initialGhostCell.classList.add('ghost');
                initialGhostCell.textContent = 'G';
            }

            advStatusText.textContent = 'Game reset to initial positions.';
            instructionText.innerHTML = `<strong>Game Reset:</strong> Agent and ghost restored.`;
        }
    }

    // ==============================================================================
    // PROBABILISTIC TRACKING (HMM) & VARIABLE ELIMINATION (CO5)
    // ==============================================================================

    function resetHMMBelief() {
        if (!grid || grid.length === 0) return;
        const rCount = grid.length;
        const cCount = grid[0].length;
        
        let openCellsCount = 0;
        for (let r = 0; r < rCount; r++) {
            for (let c = 0; c < cCount; c++) {
                if (grid[r][c] !== 1) openCellsCount++;
            }
        }

        const prob = 1.0 / openCellsCount;
        ghostBelief = Array(rCount).fill().map((_, r) => 
            Array(cCount).fill().map((_, c) => (grid[r][c] !== 1) ? prob : 0.0)
        );
        clearHeatmapVisuals();
    }

    function updateHMMBelief() {
        if (!ghostPos) {
            alert('Place the Ghost on the grid first.');
            return;
        }

        // 1. Compute noisy distance measurement
        const trueDist = Math.abs(start[0] - ghostPos[0]) + Math.abs(start[1] - ghostPos[1]);
        
        // Noisy reading: 70% true distance, 20% diff +/- 1, 10% diff +/- 2
        const rand = Math.random();
        let noise = 0;
        if (rand > 0.7 && rand <= 0.8) noise = -1;
        else if (rand > 0.8 && rand <= 0.9) noise = 1;
        else if (rand > 0.9 && rand <= 0.95) noise = -2;
        else if (rand > 0.95) noise = 2;

        const sensorReading = Math.max(0, trueDist + noise);

        lblSensorVal.textContent = sensorReading;
        lblTrueDistVal.textContent = trueDist;

        // 2. Call backend route
        const payload = {
            grid: grid,
            belief: ghostBelief,
            sensor_reading: sensorReading,
            agent_pos: start
        };

        fetch('/api/probabilistic/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert('HMM failed: ' + data.error);
                return;
            }

            ghostBelief = data.belief;
            renderHeatmap();
            instructionText.innerHTML = `<strong>HMM Filtering Update:</strong> Probability distribution updated. Darker amber indicates high probability of Ghost occupation.`;
        })
        .catch(err => console.error(err));
    }

    function renderHeatmap() {
        clearHeatmapVisuals();
        if (!ghostBelief) return;

        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const prob = ghostBelief[r][c];
                if (prob > 0.005) {
                    const cellEl = document.getElementById(`cell-${r}-${c}`);
                    if (cellEl && !cellEl.classList.contains('start') && !cellEl.classList.contains('goal')) {
                        cellEl.classList.add('prob-heatmap');
                        // Set linear transparency based on probability intensity (cap at 0.9 opacity)
                        const opacity = Math.min(0.9, prob * 5.0); // scaled for better visibility on small grids
                        cellEl.style.backgroundColor = `rgba(245, 158, 11, ${opacity})`;
                    }
                }
            }
        }
    }

    function clearHeatmapVisuals() {
        document.querySelectorAll('.cell.prob-heatmap').forEach(c => {
            c.classList.remove('prob-heatmap');
            c.style.backgroundColor = '';
        });
    }

    function runVariableElimination() {
        veResultsContainer.classList.remove('hidden');
        veResultsContent.textContent = 'Running Variable Elimination math...';

        fetch('/api/probabilistic/bayes_ve', {
            method: 'POST'
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                veResultsContent.textContent = 'Error: ' + data.error;
                return;
            }
            
            // Format worked trace log cleanly
            veResultsContent.innerHTML = data.trace.join('\n');
            instructionText.innerHTML = `<strong>VE Trace Outputted!</strong> View step-by-step marginal calculation tables on the right.`;
        })
        .catch(err => {
            veResultsContent.textContent = 'Error executing VE query: ' + err;
        });
    }

    // ==============================================================================
    // HYBRID INTELLIGENT REASONING ENGINE (CO6)
    // ==============================================================================

    function runHybridDecision() {
        if (!ghostBelief) {
            alert('Make sure a Ghost is placed on the grid and HMM beliefs are initialized.');
            return;
        }

        const payload = {
            grid: grid,
            agent_pos: start,
            goal: goal,
            ghost_belief: ghostBelief,
            risk_tolerance: parseFloat(hybridRiskSlider.value)
        };

        hybridTraceContent.textContent = 'Executing decision logic loops...';

        fetch('/api/hybrid/decide', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                hybridTraceContent.textContent = 'Error: ' + data.error;
                return;
            }

            // 1. Render Path
            clearPathVisuals();
            const selectedPath = data.selected_path;
            
            selectedPath.forEach(([r, c], idx) => {
                const cellEl = document.getElementById(`cell-${r}-${c}`);
                if (cellEl && !(r === start[0] && c === start[1]) && !(r === goal[0] && c === goal[1])) {
                    // Delay coloring slightly to create a ripple path draw effect
                    setTimeout(() => {
                        cellEl.classList.add('path');
                    }, idx * 15);
                }
            });

            // 2. Render CSP Scheduling Waypoints
            if (data.csp_success) {
                for (const [cellKey, timeSlot] of Object.entries(data.schedule)) {
                    const parts = cellKey.split('_');
                    const r = parts[1];
                    const c = parts[2];
                    
                    const cellEl = document.getElementById(`cell-${r}-${c}`);
                    if (cellEl) {
                        cellEl.classList.add('csp-waypoint');
                        cellEl.setAttribute('data-slot', `T${timeSlot}`);
                    }
                }
            }

            // 3. Print Trace Log
            hybridTraceContent.innerHTML = data.trace.join('<br>');
            instructionText.innerHTML = `<strong>Hybrid Reasoning Complete!</strong> Explainable trace explains detour vs risk trade-offs. Checkpoints scheduled via CSP variables.`;
        })
        .catch(err => {
            hybridTraceContent.textContent = 'Error executing hybrid solver: ' + err;
        });
    }

    // Run app init
    init();
});
