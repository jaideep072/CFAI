const Pacman3D = (function() {
    let scene, camera, renderer, container, controls;
    let mazeGroup = new THREE.Group();
    let agentMesh;
    let ghostMeshes = [];
    let currentGrid = [];
    let currentShape = 'flat';
    let pelletMeshes = {};
    let animationId;
    let clickCallback = null;
    let mouseDownPos = {x: 0, y: 0};

    const CELL_SIZE = 10;
    const WALL_HEIGHT = 10;

    function init(containerId) {
        container = document.getElementById(containerId);
        if (!container) return;
        
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0xFAF6F0); // Match UI theme background

        camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);

        if (typeof THREE !== 'undefined' && typeof THREE.OrbitControls !== 'undefined') {
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.maxPolarAngle = Math.PI / 2 - 0.05; // Don't go below the floor
        }

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(50, 100, 50);
        dirLight.castShadow = true;
        scene.add(dirLight);
        
        const pointLight = new THREE.PointLight(0xF2CC8F, 0.8, 150); // Soft amber light
        pointLight.position.set(0, 50, 0);
        scene.add(pointLight);

        scene.add(pointLight);

        window.addEventListener('resize', onWindowResize, false);
        
        // Raycasting for clicks
        renderer.domElement.addEventListener('pointerdown', (e) => {
            mouseDownPos.x = e.clientX;
            mouseDownPos.y = e.clientY;
        });

        renderer.domElement.addEventListener('pointerup', (e) => {
            const dist = Math.abs(e.clientX - mouseDownPos.x) + Math.abs(e.clientY - mouseDownPos.y);
            if (dist > 5) return; // Was a drag, not a click

            const rect = renderer.domElement.getBoundingClientRect();
            const mouse = new THREE.Vector2();
            mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

            const raycaster = new THREE.Raycaster();
            raycaster.setFromCamera(mouse, camera);

            const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
            const target = new THREE.Vector3();
            raycaster.ray.intersectPlane(plane, target);

            if (target && currentGrid.length > 0) {
                const rows = currentGrid.length;
                const cols = currentGrid[0].length;
                const offsetX = (cols * CELL_SIZE) / 2;
                const offsetZ = (rows * CELL_SIZE) / 2;

                const c = Math.floor((target.x + offsetX) / CELL_SIZE);
                const r = Math.floor((target.z + offsetZ) / CELL_SIZE);

                if (r >= 0 && r < rows && c >= 0 && c < cols) {
                    if (clickCallback) clickCallback(r, c);
                }
            }
        });

        scene.add(mazeGroup);
        
        animate();
    }
    
    function setOnClick(cb) {
        clickCallback = cb;
    }

    function onWindowResize() {
        if (!container || container.classList.contains('hidden') || !camera || !renderer) return;
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    }

    function getGridTransform(r, c, shape, rows, cols, heightOffset = 0) {
        const offsetX = (cols * CELL_SIZE) / 2;
        const offsetZ = (rows * CELL_SIZE) / 2;
        
        let pos = new THREE.Vector3();
        let up = new THREE.Vector3(0, 1, 0);
        
        if (shape === 'flat') {
            pos.set(c * CELL_SIZE - offsetX + CELL_SIZE/2, heightOffset, r * CELL_SIZE - offsetZ + CELL_SIZE/2);
            return { pos, up };
        }
        
        if (shape === 'cylinder') {
            const R = (cols * CELL_SIZE) / (2 * Math.PI);
            const theta = (c / cols) * 2 * Math.PI;
            const h = (r - rows/2) * CELL_SIZE;
            
            up.set(Math.cos(theta), 0, Math.sin(theta)).normalize();
            pos.copy(up).multiplyScalar(R + heightOffset);
            pos.y = -h;
            return { pos, up };
        }
        
        if (shape === 'sphere' || shape === 'cube') {
            const R = (Math.max(rows, cols) * CELL_SIZE) / Math.PI;
            const phi = (r / Math.max(1, rows - 1)) * Math.PI;
            const theta = (c / cols) * 2 * Math.PI;
            
            const nx = Math.sin(phi) * Math.cos(theta);
            const ny = Math.cos(phi);
            const nz = Math.sin(phi) * Math.sin(theta);
            
            up.set(nx, ny, nz).normalize();
            
            if (shape === 'cube') {
                const absX = Math.abs(nx);
                const absY = Math.abs(ny);
                const absZ = Math.abs(nz);
                const maxAbs = Math.max(absX, absY, absZ);
                
                const scale = R / maxAbs;
                pos.set(nx * scale, ny * scale, nz * scale);
                
                up.set(0,0,0);
                if (maxAbs === absX) up.x = Math.sign(nx);
                else if (maxAbs === absY) up.y = Math.sign(ny);
                else up.z = Math.sign(nz);
                
                pos.addScaledVector(up, heightOffset);
            } else {
                pos.copy(up).multiplyScalar(R + heightOffset);
            }
            
            return { pos, up };
        }
        
        pos.set(c * CELL_SIZE - offsetX + CELL_SIZE/2, heightOffset, r * CELL_SIZE - offsetZ + CELL_SIZE/2);
        return { pos, up };
    }

    function generateMaze(grid, startPos, ghostPos, mazeShape = 'flat') {
        if (!scene) return;
        currentGrid = grid;
        currentShape = mazeShape;
        pelletMeshes = {};
        
        // Clear previous maze
        while(mazeGroup.children.length > 0){ 
            const obj = mazeGroup.children[0];
            mazeGroup.remove(obj);
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) obj.material.dispose();
        }

        const rows = grid.length;
        const cols = grid[0].length;

        // Base Core (Floor)
        let coreGeo;
        if (mazeShape === 'flat') {
            coreGeo = new THREE.PlaneGeometry(cols * CELL_SIZE, rows * CELL_SIZE);
        } else if (mazeShape === 'cylinder') {
            const R = (cols * CELL_SIZE) / (2 * Math.PI);
            coreGeo = new THREE.CylinderGeometry(R, R, rows * CELL_SIZE, 32, 1, false);
        } else if (mazeShape === 'sphere') {
            const R = (Math.max(rows, cols) * CELL_SIZE) / Math.PI;
            coreGeo = new THREE.SphereGeometry(R, 32, 32);
        } else if (mazeShape === 'cube') {
            const R = (Math.max(rows, cols) * CELL_SIZE) / Math.PI;
            coreGeo = new THREE.BoxGeometry(R*2, R*2, R*2);
        }
        
        const coreMat = new THREE.MeshStandardMaterial({ color: 0xF5EFEB, roughness: 0.9, metalness: 0.1 });
        const coreMesh = new THREE.Mesh(coreGeo, coreMat);
        if (mazeShape === 'flat') {
            coreMesh.rotation.x = -Math.PI / 2;
        }
        coreMesh.receiveShadow = true;
        mazeGroup.add(coreMesh);

        // Walls
        const wallGeo = new THREE.BoxGeometry(CELL_SIZE * 0.95, WALL_HEIGHT, CELL_SIZE * 0.95);
        const wallMat = new THREE.MeshStandardMaterial({ 
            color: 0x663335,
            roughness: 0.7,
            emissive: 0x221112
        });
        
        // Pellets
        const pelletGeo = new THREE.SphereGeometry(CELL_SIZE * 0.15, 8, 8);
        const pelletMat = new THREE.MeshStandardMaterial({ color: 0xF2CC8F, emissive: 0x332211 });

        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                if (grid[r][c] === 1) { // Wall
                    const wall = new THREE.Mesh(wallGeo, wallMat);
                    const tf = getGridTransform(r, c, mazeShape, rows, cols, WALL_HEIGHT/2);
                    wall.position.copy(tf.pos);
                    wall.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tf.up);
                    
                    const edges = new THREE.EdgesGeometry(wallGeo);
                    const lineMat = new THREE.LineBasicMaterial({ color: 0xE56B6F, linewidth: 1, transparent: true, opacity: 0.5 });
                    const edgeLines = new THREE.LineSegments(edges, lineMat);
                    wall.add(edgeLines);
                    
                    wall.castShadow = true;
                    wall.receiveShadow = true;
                    mazeGroup.add(wall);
                } else if (grid[r][c] === 0) { // Open path
                    const pellet = new THREE.Mesh(pelletGeo, pelletMat.clone());
                    const tf = getGridTransform(r, c, mazeShape, rows, cols, 2);
                    pellet.position.copy(tf.pos);
                    mazeGroup.add(pellet);
                    
                    if (!pelletMeshes[r]) pelletMeshes[r] = {};
                    pelletMeshes[r][c] = pellet;
                }
            }
        }

        // Agent (Pac-Man)
        const agentGeo = new THREE.SphereGeometry(CELL_SIZE * 0.4, 32, 32, Math.PI / 4, Math.PI * 1.5);
        const agentMat = new THREE.MeshStandardMaterial({ color: 0x81B29A, emissive: 0x1A241F, side: THREE.DoubleSide, roughness: 0.3, metalness: 0.5 });
        agentMesh = new THREE.Mesh(agentGeo, agentMat);
        agentMesh.castShadow = true;
        mazeGroup.add(agentMesh);
        if (startPos) setMeshPosition(agentMesh, startPos);
        
        // Ghosts will be spawned dynamically via setGhosts

        // Adjust camera
        if (mazeShape === 'flat') {
            camera.position.set(0, Math.max(cols, rows) * CELL_SIZE * 0.9, Math.max(cols, rows) * CELL_SIZE * 0.6);
        } else {
            camera.position.set(0, Math.max(cols, rows) * CELL_SIZE * 0.5, Math.max(cols, rows) * CELL_SIZE * 1.5);
        }
        camera.lookAt(0, 0, 0);
    }

    function setMeshPosition(mesh, pos) {
        if (!currentGrid || currentGrid.length === 0) return;
        const rows = currentGrid.length;
        const cols = currentGrid[0].length;
        const tf = getGridTransform(pos[0], pos[1], currentShape, rows, cols, CELL_SIZE * 0.4);
        mesh.position.copy(tf.pos);
        mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tf.up);
        
        // Rotate agent sideways to lay flat
        if (mesh === agentMesh) {
            mesh.rotateX(Math.PI / 2);
        }
    }

    function getWorldPos(r, c) {
        if (!currentGrid || currentGrid.length === 0) return new THREE.Vector3();
        const rows = currentGrid.length;
        const cols = currentGrid[0].length;
        const tf = getGridTransform(r, c, currentShape, rows, cols, CELL_SIZE * 0.4);
        return tf.pos;
    }

    function setGhosts(ghostsData) {
        ghostMeshes.forEach(mesh => mazeGroup.remove(mesh));
        ghostMeshes = [];

        if (!scene || !ghostsData) return;

        const ghostGeo = new THREE.CylinderGeometry(CELL_SIZE * 0.4, CELL_SIZE * 0.4, CELL_SIZE * 0.8, 16);
        const ghostHeadGeo = new THREE.SphereGeometry(CELL_SIZE * 0.4, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2);

        const colors = {
            'blinky': 0xFF0000,
            'pinky': 0xFFB8FF,
            'inky': 0x00FFFF,
            'clyde': 0xFFB852,
            'chaser': 0xE56B6F
        };

        ghostsData.forEach(g => {
            const color = colors[g.type] || 0xE56B6F;
            const ghostMat = new THREE.MeshStandardMaterial({ color: color, emissive: color, emissiveIntensity: 0.2, roughness: 0.4 });
            const mesh = new THREE.Mesh(ghostGeo, ghostMat);
            
            const ghostHead = new THREE.Mesh(ghostHeadGeo, ghostMat);
            ghostHead.position.y = CELL_SIZE * 0.4;
            mesh.add(ghostHead);

            mesh.castShadow = true;
            mazeGroup.add(mesh);
            setMeshPosition(mesh, g.pos);
            ghostMeshes.push(mesh);
        });
    }

    function eatPellet(r, c) {
        if (pelletMeshes[r] && pelletMeshes[r][c]) {
            mazeGroup.remove(pelletMeshes[r][c]);
            pelletMeshes[r][c] = null;
        }
    }

    function animateMove(agentPos, ghostsData, duration = 300) {
        return new Promise(resolve => {
            if (!agentMesh) return resolve();

            const startAgent = agentMesh.position.clone();
            const endAgent = getWorldPos(agentPos[0], agentPos[1]);
            
            const ghostStarts = [];
            const ghostEnds = [];
            if (ghostsData && ghostMeshes.length === ghostsData.length) {
                ghostsData.forEach((g, i) => {
                    ghostStarts.push(ghostMeshes[i].position.clone());
                    ghostEnds.push(getWorldPos(g.pos[0], g.pos[1]));
                });
            }

            const startTime = performance.now();

            function tween() {
                const now = performance.now();
                const progress = Math.min((now - startTime) / duration, 1.0);
                const ease = 1 - Math.pow(1 - progress, 3);

                agentMesh.position.lerpVectors(startAgent, endAgent, ease);
                
                ghostStarts.forEach((start, i) => {
                    ghostMeshes[i].position.lerpVectors(start, ghostEnds[i], ease);
                });

                if (progress < 1.0) {
                    requestAnimationFrame(tween);
                } else {
                    resolve();
                }
            }
            tween();
        });
    }

    function setGhostPos(pos) {
        // Legacy fallback
    }

    function setAgentPos(pos) {
        if (!agentMesh) return;
        setMeshPosition(agentMesh, pos);
    }
    
    function updateSearchState(visited, frontier, current) {
        if (!pelletMeshes) return;
        
        // Reset all pellets to amber
        for (let r in pelletMeshes) {
            for (let c in pelletMeshes[r]) {
                pelletMeshes[r][c].material.color.setHex(0xF2CC8F);
                pelletMeshes[r][c].material.emissive.setHex(0x332211);
            }
        }
        
        // Highlight frontier
        frontier.forEach(([r, c]) => {
            if (pelletMeshes[r] && pelletMeshes[r][c]) {
                pelletMeshes[r][c].material.color.setHex(0xFFB703);
                pelletMeshes[r][c].material.emissive.setHex(0xAA6600);
            }
        });
        
        // Highlight visited
        visited.forEach(([r, c]) => {
            if (pelletMeshes[r] && pelletMeshes[r][c]) {
                pelletMeshes[r][c].material.color.setHex(0x0EAD69); // Cyan-green
                pelletMeshes[r][c].material.emissive.setHex(0x004422);
            }
        });
        
        // Snap agent to current search node
        if (current) {
            setAgentPos(current);
        }
    }
    
    function setFinalPath(path) {
        if (!pelletMeshes) return;
        path.forEach(([r, c]) => {
            if (pelletMeshes[r] && pelletMeshes[r][c]) {
                pelletMeshes[r][c].material.color.setHex(0xFFD166); // Golden
                pelletMeshes[r][c].material.emissive.setHex(0xAA8800);
            }
        });
    }

    function animate() {
        animationId = requestAnimationFrame(animate);
        if (controls) controls.update();
        if (renderer && scene && camera) {
            renderer.render(scene, camera);
        }
    }

    return {
        init,
        onWindowResize,
        setAgentPos,
        setGhostPos,
        setGhosts,
        eatPellet,
        animateMove,
        updateSearchState,
        setFinalPath,
        setOnClick,
        generateMaze
    };
})();
