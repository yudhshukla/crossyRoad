from cmu_graphics import *
import random
import math

# ==========================================
# MODEL
# ==========================================

def onAppStart(app):
    app.highScore = 0
    restartGame(app)

def restartGame(app):
    app.setMaxShapeCount(5000)
    app.gameOver = False
    app.deathType = None 
    app.score = 0      
    app.coins = 0      
    
    # Grid settings
    app.cols = 15 
    app.tileW = 24 
    app.tileH = 12 
    
    app.playerRow = 0 
    app.playerCol = app.cols // 2
    app.playerColor = 'white'
    
    app.hopTimer = 0   
    app.waveTimer = 0  
    app.gameTimer = 0 
    
    app.particles = []
    
    # Camera follows player
    app.camRow = 0.0
    app.camCol = app.cols // 2
    
    app.lanes = {} 
    
    # Generate initial world 
    for i in range(-10, 10):
        createLane(app, i, 'grass')
        
    # Clear starting tree
    if 0 in app.lanes and app.playerCol in app.lanes[0].trees:
        app.lanes[0].trees.remove(app.playerCol)
        
    for i in range(10, 40):
        createLane(app, i, generateRandomLaneType())

class Lane:
    def __init__(self, laneType, direction, speed):
        self.type = laneType 
        self.direction = direction 
        self.speed = speed
        self.obstacles = [] 
        self.trees = set()  
        self.coins = set()
        
        self.trainState = 'IDLE' 
        self.trainTimer = random.randint(100, 300) 
        self.trainX = -1000 
        
def generateRandomLaneType():
    return random.choice(['grass', 'grass', 'road', 'road', 'road', 'road', 'river', 'river', 'train'])

def createLane(app, rowIndex, laneType):
    direction = random.choice([-1, 1])
    speed = random.randint(5, 15) / 100 
    if laneType == 'train': speed = 1.5 
    lane = Lane(laneType, direction, speed)
    
    if laneType == 'road':
        numCars = random.randint(1, 3)
        for _ in range(numCars):
            pos = random.uniform(0, app.cols)
            width = random.uniform(1.2, 1.8) 
            color = random.choice(['crimson', 'royalBlue', 'purple', 'orange', 'white'])
            lane.obstacles.append([pos, width, color])
            
    elif laneType == 'river':
        numLogs = random.randint(2, 4)
        lane.speed = random.randint(3, 8) / 100 
        for _ in range(numLogs):
            pos = random.uniform(0, app.cols)
            width = random.uniform(2, 3)
            color = 'saddleBrown'
            lane.obstacles.append([pos, width, color])

    if laneType == 'grass':
        numTrees = random.randint(0, 4) 
        for _ in range(numTrees):
            tCol = random.randint(0, app.cols - 1)
            lane.trees.add(tCol)
            
    if laneType in ['grass', 'road', 'train']:
        if random.random() < 0.2:
            cCol = random.randint(0, app.cols - 1)
            if cCol not in lane.trees:
                lane.coins.add(cCol)

    app.lanes[rowIndex] = lane

# ==========================================
# CONTROLLER
# ==========================================

def onKeyPress(app, key):
    if app.gameOver:
        if key == 'r': restartGame(app)
        return

    dRow, dCol = 0, 0
    if key == 'up':    dRow = 1
    elif key == 'down':  dRow = -1
    elif key == 'left':  dCol = -1
    elif key == 'right': dCol = 1
    else: return 

    newRow = app.playerRow + dRow
    newCol = app.playerCol + dCol

    if newCol < -5 or newCol > app.cols + 5: return 
    if newRow < -5: return 
    
    targetLane = app.lanes.get(newRow)
    
    # Use standard round() 
    if targetLane and pythonRound(newCol) in targetLane.trees:
        return 

    app.playerRow = newRow
    app.playerCol = newCol
    app.hopTimer = 5 
    
    if app.playerRow > app.score:
        app.score = app.playerRow
        if app.score > app.highScore:
            app.highScore = app.score
        
    if app.playerRow + 30 not in app.lanes:
        createLane(app, app.playerRow + 30, generateRandomLaneType())

def onStep(app):
    updateParticles(app)
    if app.gameOver: return
    
    if app.hopTimer > 0: app.hopTimer -= 1
    app.waveTimer += 0.2
    app.gameTimer += 1
    
    # Smooth Camera
    app.camRow += (app.playerRow - app.camRow) * 0.1
    app.camCol += (app.playerCol - app.camCol) * 0.1
    
    playerLane = app.lanes.get(app.playerRow)
    
    for rowIdx in app.lanes:
        lane = app.lanes[rowIdx]
        
        if lane.type == 'train':
            lane.trainTimer -= 1
            if lane.trainState == 'IDLE':
                if lane.trainTimer <= 0:
                    lane.trainState = 'WARNING'
                    lane.trainTimer = 90 
            elif lane.trainState == 'WARNING':
                if lane.trainTimer <= 0:
                    lane.trainState = 'PASSING'
                    if lane.direction == 1: lane.trainX = -20
                    else: lane.trainX = app.cols + 20
            elif lane.trainState == 'PASSING':
                lane.trainX += lane.speed * lane.direction
                if (lane.direction == 1 and lane.trainX > app.cols + 20) or \
                   (lane.direction == -1 and lane.trainX < -20):
                    lane.trainState = 'IDLE'
                    lane.trainTimer = random.randint(200, 500)
                    
        if lane.type != 'grass':
            for obs in lane.obstacles:
                obs[0] += lane.speed * lane.direction
                # Infinite wrap around
                if lane.direction == 1 and obs[0] > app.cols + 10:
                    obs[0] = -obs[1] - 10
                elif lane.direction == -1 and obs[0] < -obs[1] - 10:
                    obs[0] = app.cols + 10
                
    if playerLane:
        # Coin Collection
        if abs(app.playerCol - int(app.playerCol)) < 0.3:
            checkCol = int(pythonRound(app.playerCol))
            if checkCol in playerLane.coins:
                playerLane.coins.remove(checkCol)
                app.coins += 1

        # Train Hit
        if playerLane.type == 'train' and playerLane.trainState == 'PASSING':
            trainWidth = 15 
            tx = playerLane.trainX
            if abs(tx - app.playerCol) < trainWidth/2:
                triggerGameOver(app, 'squished')

        # Car Hit
        elif playerLane.type == 'road':
            for obs in playerLane.obstacles:
                carX, carW = obs[0], obs[1]
                if (app.playerCol < carX + carW - 0.2 and 
                    app.playerCol + 0.8 > carX + 0.2):
                    triggerGameOver(app, 'squished')
        
        # River Logic
        elif playerLane.type == 'river':
            onLog = False
            for obs in playerLane.obstacles:
                logX, logW = obs[0], obs[1]
                if (app.playerCol + 0.2 >= logX and 
                    app.playerCol + 0.6 <= logX + logW):
                    onLog = True
                    app.playerCol += playerLane.speed * playerLane.direction
                    break
            
            if not onLog:
                triggerGameOver(app, 'splashed')
            elif app.playerCol < -10 or app.playerCol > app.cols + 10:
                triggerGameOver(app, 'splashed')

def triggerGameOver(app, type):
    app.gameOver = True
    app.deathType = type
    createParticles(app, type)

def createParticles(app, type):
    sx, sy = getIsoScreenPos(app, app.playerRow, app.playerCol, 0)
    colors = ['red', 'orange', 'white'] if type == 'squished' else ['white', 'cyan', 'blue']
    for _ in range(30):
        angle = random.uniform(0, 2*math.pi)
        speed = random.uniform(2, 8)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        life = random.randint(20, 40)
        size = random.randint(3, 8)
        color = random.choice(colors)
        app.particles.append([sx, sy, dx, dy, color, life, size])

def updateParticles(app):
    for p in app.particles:
        p[0] += p[2] 
        p[1] += p[3] 
        p[5] -= 1    
        p[6] *= 0.9  
    app.particles = [p for p in app.particles if p[5] > 0]

# ==========================================
# VIEW: ISOMETRIC ENGINE (OPTIMIZED)
# ==========================================

def getIsoScreenPos(app, row, col, zHeight):
    cx, cy = app.width / 2, app.height / 2 + 100
    dRow = row - app.camRow
    dCol = col - app.camCol
    
    screenX = cx + (dCol - dRow) * app.tileW
    screenY = cy - (dCol + dRow) * app.tileH - zHeight
    return screenX, screenY

def drawIsoBlock(app, row, col, z, width, depth, height, color, topColor=None):
    if topColor is None: topColor = color
    
    # Vertices
    bx1, by1 = getIsoScreenPos(app, row, col, z)
    bx2, by2 = getIsoScreenPos(app, row, col + width, z)
    bx3, by3 = getIsoScreenPos(app, row + depth, col + width, z)
    bx4, by4 = getIsoScreenPos(app, row + depth, col, z)
    
    tx1, ty1 = bx1, by1 - height
    tx2, ty2 = bx2, by2 - height
    tx3, ty3 = bx3, by3 - height
    tx4, ty4 = bx4, by4 - height
    
    # Faces
    # Left
    drawPolygon(bx4, by4, bx3, by3, tx3, ty3, tx4, ty4, fill=color, opacity=90, border=None)
    # Right
    drawPolygon(bx3, by3, bx2, by2, tx2, ty2, tx3, ty3, fill=color, opacity=70, border=None)
    # Top
    drawPolygon(tx1, ty1, tx2, ty2, tx3, ty3, tx4, ty4, fill=topColor, border=None)

def redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill='lightSkyBlue')
    
    # Draw Far lanes first (High Row to Low Row)
    startRow = int(app.camRow) + 15
    endRow = int(app.camRow) - 10
    
    for r in range(startRow, endRow, -1):
        if r in app.lanes:
            drawIsoLane(app, r, app.lanes[r])
            
    # Draw Player (If not hidden by death)
    if not app.gameOver or app.deathType != 'splashed':
        pz = 0
        if app.hopTimer > 0: pz = 15 * math.sin(app.hopTimer * 0.6)
        h = 16
        if app.gameOver and app.deathType == 'squished': 
            h = 4
            pz = 0
        
        drawIsoBlock(app, app.playerRow, app.playerCol, 0, 0.6, 0.6, h, 'lightGray', app.playerColor)
        
        # Eyes
        sx, sy = getIsoScreenPos(app, app.playerRow + 0.6, app.playerCol + 0.2, pz + h - 5)
        drawCircle(sx, sy, 2, fill='black')
        sx, sy = getIsoScreenPos(app, app.playerRow + 0.6, app.playerCol + 0.4, pz + h - 6)
        drawCircle(sx, sy, 2, fill='black')

    for p in app.particles:
        drawCircle(p[0], p[1], p[6], fill=p[4])

    drawHUD(app)
    
    if app.gameOver:
        drawLabel("GAME OVER", app.width/2, app.height/2, size=40, bold=True, fill='red', border='white')

def drawIsoLane(app, r, lane):
    # OPTIMIZATION: Draw ground as one big strip instead of many small squares
    
    # Calculate visible range shifts based on row
    shift = int(r)
    colStart = shift - 15
    colEnd = shift + 15
    width = colEnd - colStart
    
    color = 'mediumSeaGreen'
    topC = 'lightGreen'
    h = 15
    
    if lane.type == 'road': 
        color = 'dimGray'
        topC = 'gray'
        h = 10
    elif lane.type == 'river': 
        color = 'royalBlue'
        topC = 'cornflowerBlue'
        h = 5 
    elif lane.type == 'train':
        color = 'black'
        topC = 'darkGray'
        h = 12

    # Draw ONE big block for the ground
    drawIsoBlock(app, r, colStart, 0, width, 1.0, h, color, topC)
    
    # Road markings (simplified to lines for speed)
    if lane.type == 'road':
        sx1, sy1 = getIsoScreenPos(app, r, colStart, h)
        sx2, sy2 = getIsoScreenPos(app, r, colEnd, h)
        # Offset slightly for center
        drawLine(sx1, sy1, sx2, sy2, fill='white', opacity=30, dashes=True)

    # --- OBJECTS ---
    # Sort objects by column DESCENDING (Back-to-Front painter's algo)
    # High Column = Top-Right of screen (Background)
    # Low Column = Bottom-Left of screen (Foreground)
    
    # Collect all renderables in this lane
    renderList = []
    
    for tCol in lane.trees:
        if colStart < tCol < colEnd:
            renderList.append({'type':'tree', 'col':tCol})
            
    for obs in lane.obstacles:
        c = obs[0]
        if colStart < c < colEnd:
            renderList.append({'type':'obs', 'col':c, 'data':obs})
            
    # SORT: High column (Back) -> Low column (Front)
    renderList.sort(key=lambda x: x['col'], reverse=True)
    
    for item in renderList:
        if item['type'] == 'tree':
            tCol = item['col']
            drawIsoBlock(app, r + 0.3, tCol + 0.3, 15, 0.4, 0.4, 15, 'saddleBrown')
            drawIsoBlock(app, r + 0.1, tCol + 0.1, 30, 0.8, 0.8, 20, 'darkGreen', 'forestGreen')
            
        elif item['type'] == 'obs':
            c = item['col']
            obs = item['data']
            w, color = obs[1], obs[2]
            
            if lane.type == 'road': 
                drawIsoBlock(app, r + 0.2, c, 10, 0.6, w, 12, 'black', color)
                drawIsoBlock(app, r + 0.3, c + 0.2, 22, 0.4, w - 0.4, 6, color, 'lightBlue')
            elif lane.type == 'river': 
                drawIsoBlock(app, r + 0.2, c, 2, 0.6, w, 6, 'saddleBrown', 'sienna')

    if lane.type == 'train':
        if lane.trainState == 'PASSING':
            tx = lane.trainX
            drawIsoBlock(app, r + 0.1, tx, 12, 0.8, 10, 20, 'darkRed', 'crimson')
            sx, sy = getIsoScreenPos(app, r, tx, 35)
            drawCircle(sx, sy - (app.gameTimer % 20), 5 + (app.gameTimer%10), fill='gray', opacity=50)

def drawHUD(app):
    drawLabel(f"{app.score}", app.width/2, 50, size=30, fill='white', bold=True, border='black')

def main():
    runApp(width=400, height=600)

if __name__ == '__main__':
    main()