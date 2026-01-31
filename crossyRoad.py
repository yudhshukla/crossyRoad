from cmu_graphics import *
import random
import math

# ==========================================
# MODEL: Same Logic, New View Settings
# ==========================================

def onAppStart(app):
    app.highScore = 0
    restartGame(app)

def restartGame(app):
    app.gameOver = False
    app.deathType = None 
    app.score = 0      
    app.coins = 0      
    
    app.cols = 9 # Reduced slightly to keep 3D view centered
    
    # 3D Settings
    app.tileW = 24  # Half-width of a tile
    app.tileH = 14  # Half-height of a tile
    
    app.playerRow = 0 
    app.playerCol = app.cols // 2
    app.playerColor = 'white'
    
    app.hopTimer = 0   
    app.waveTimer = 0  
    app.gameTimer = 0 
    
    app.particles = []
    
    # Camera follows player smoothly
    app.camRow = 0.0
    app.camCol = 4.0
    
    app.lanes = {} 
    
    for i in range(-5, 5): # Generate more lanes behind for 3D visibility
        createLane(app, i, 'grass')
        
    if 0 in app.lanes and app.playerCol in app.lanes[0].trees:
        app.lanes[0].trees.remove(app.playerCol)
        
    for i in range(5, 30):
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
        numCars = random.randint(1, 2)
        for _ in range(numCars):
            pos = random.uniform(0, app.cols)
            width = random.uniform(1.2, 1.8) # Smaller width for 3D
            color = random.choice(['crimson', 'royalBlue', 'purple', 'orange', 'white'])
            lane.obstacles.append([pos, width, color])
            
    elif laneType == 'river':
        numLogs = random.randint(2, 3)
        lane.speed = random.randint(3, 8) / 100 
        for _ in range(numLogs):
            pos = random.uniform(0, app.cols)
            width = random.uniform(2, 3)
            color = 'saddleBrown'
            lane.obstacles.append([pos, width, color])

    if laneType == 'grass':
        numTrees = random.randint(0, 3) 
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

    if newRow < 0: return 
    # Allow slightly wider movement in 3D looks better
    if newCol < -1 or newCol > app.cols: return 
    
    targetLane = app.lanes.get(newRow)
    if targetLane and newCol in targetLane.trees:
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
                if lane.direction == 1 and obs[0] > app.cols + 4:
                    obs[0] = -obs[1] - 4
                elif lane.direction == -1 and obs[0] < -obs[1] - 4:
                    obs[0] = app.cols + 4
                
    if playerLane:
        # Check integer proximity for coins
        if abs(app.playerCol - int(app.playerCol)) < 0.2:
            checkCol = int(pythonRound(app.playerCol))
            if checkCol in playerLane.coins:
                playerLane.coins.remove(checkCol)
                app.coins += 1

        if playerLane.type == 'train' and playerLane.trainState == 'PASSING':
            trainWidth = 15 
            tx = playerLane.trainX
            if (app.playerCol > tx - trainWidth and app.playerCol < tx) or \
               (app.playerCol > tx and app.playerCol < tx + trainWidth):
                    # Close enough hit
                    if abs(tx - app.playerCol) < trainWidth: # Simplified check
                        triggerGameOver(app, 'squished')

        elif playerLane.type == 'road':
            for obs in playerLane.obstacles:
                carX, carW = obs[0], obs[1]
                if (app.playerCol < carX + carW - 0.2 and 
                    app.playerCol + 0.8 > carX + 0.2):
                    triggerGameOver(app, 'squished')
        
        elif playerLane.type == 'river':
            onLog = False
            for obs in playerLane.obstacles:
                logX, logW = obs[0], obs[1]
                if (app.playerCol + 0.3 >= logX and 
                    app.playerCol + 0.5 <= logX + logW):
                    onLog = True
                    app.playerCol += playerLane.speed * playerLane.direction
                    break
            
            if not onLog:
                triggerGameOver(app, 'splashed')
            elif app.playerCol < -2 or app.playerCol > app.cols + 2:
                triggerGameOver(app, 'splashed')

def triggerGameOver(app, type):
    app.gameOver = True
    app.deathType = type
    createParticles(app, type)

def createParticles(app, type):
    sx, sy = getIsoScreenPos(app, app.playerRow, app.playerCol, 0)
    
    colors = []
    if type == 'squished': colors = ['red', 'orange', 'white', 'gray']
    else: colors = ['white', 'cyan', 'blue', 'lightBlue']
        
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
# VIEW: ISOMETRIC ENGINE
# ==========================================

def getIsoScreenPos(app, row, col, zHeight):
    # Center of screen
    cx, cy = app.width / 2, app.height / 2 + 100
    
    # Calculate offset from camera
    dRow = row - app.camRow
    dCol = col - app.camCol
    
    # Isometric formula
    # x goes Down-Right, y goes Up-Right
    screenX = cx + (dCol - dRow) * app.tileW
    screenY = cy + (dCol + dRow) * app.tileH - zHeight
    
    return screenX, screenY

def drawIsoBlock(app, row, col, z, width, depth, height, color, topColor=None):
    # Draws a 3D block at grid coordinates
    # width/depth are in grid units (usually 1.0)
    # height is in pixels
    
    if topColor is None: topColor = color
    
    # Get coordinates of the base footprint
    # (r, c)
    x1, y1 = getIsoScreenPos(app, row, col, z)
    # (r+depth, c)
    x2, y2 = getIsoScreenPos(app, row + depth, col, z)
    # (r+depth, c+width)
    x3, y3 = getIsoScreenPos(app, row + depth, col + width, z)
    # (r, c+width)
    x4, y4 = getIsoScreenPos(app, row, col + width, z)
    
    # Draw Faces
    # Top Face (offset by height)
    ty1, ty2, ty3, ty4 = y1-height, y2-height, y3-height, y4-height
    
    # Left Face (visible if we look from bottom right) -> coords x2,y2 to x1,y1
    drawPolygon(x1, y1, x2, y2, x2, ty2, x1, ty1, fill=color, border=None)
    # Right Face
    drawPolygon(x2, y2, x3, y3, x3, ty3, x2, ty2, fill=color, opacity=80, border=None)
    # Top Face
    drawPolygon(x1, ty1, x2, ty2, x3, ty3, x4, ty4, fill=topColor, border=None)

def redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill='lightSkyBlue')
    
    # Render Order: Back to Front (Low Row to High Row)
    # Visible Range
    startRow = int(app.camRow) - 10
    endRow = int(app.camRow) + 12
    
    for r in range(startRow, endRow):
        if r in app.lanes:
            drawIsoLane(app, r, app.lanes[r])
            
    # Draw Player
    # We must insert the player into the render loop at the correct row
    # but for simplicity in this version, drawing him last (on top) usually works 
    # unless he is behind a tall tree in the next row.
    # To fix visuals, we draw player *after* his row is drawn but *before* next row.
    
    # Re-loop to find player slot? 
    # Actually, simpler: draw player independently on top for now. 
    # 3D Sorting is complex, this is "Step 1".
    
    if not app.gameOver or app.deathType != 'splashed':
        pz = 0
        if app.hopTimer > 0: pz = 15 * math.sin(app.hopTimer * 0.6)
        
        # Flatten player if squished
        h = 16
        if app.gameOver and app.deathType == 'squished': 
            h = 4
            pz = 0
            
        drawIsoBlock(app, app.playerRow, app.playerCol, 0, 0.8, 0.8, h, 'lightGray', app.playerColor)
        
        # Eyes
        sx, sy = getIsoScreenPos(app, app.playerRow, app.playerCol, pz + h - 5)
        drawCircle(sx - 5, sy, 2, fill='black')
        drawCircle(sx + 3, sy + 2, 2, fill='black')

    # Particles
    for p in app.particles:
        drawCircle(p[0], p[1], p[6], fill=p[4])

    drawHUD(app)
    
    if app.gameOver:
        drawLabel("GAME OVER", app.width/2, app.height/2, size=40, bold=True, fill='red', border='white')

def drawIsoLane(app, r, lane):
    # 1. Draw Ground Tiles
    # We draw from left col to right col (back to front in iso)
    for c in range(-2, app.cols + 3):
        color = 'mediumSeaGreen'
        topC = 'lightGreen'
        h = 15 # block height
        
        if lane.type == 'road': 
            color = 'dimGray'
            topC = 'gray'
            h = 10
        elif lane.type == 'river': 
            color = 'royalBlue'
            topC = 'cornflowerBlue'
            h = 5 # River is lower
            
        elif lane.type == 'train':
            color = 'black'
            topC = 'black'
            h = 12

        drawIsoBlock(app, r, c, 0, 1.0, 1.0, h, color, topC)
        
        # Road Markings
        if lane.type == 'road':
             sx, sy = getIsoScreenPos(app, r, c, h)
             # approximate middle
             drawCircle(sx, sy, 2, fill='white', opacity=30)

    # 2. Draw Lane Objects
    
    # Trees
    for tCol in lane.trees:
        # Trunk
        drawIsoBlock(app, r + 0.3, tCol + 0.3, 15, 0.4, 0.4, 15, 'saddleBrown')
        # Leaves (Pyramid-ish)
        drawIsoBlock(app, r + 0.1, tCol + 0.1, 30, 0.8, 0.8, 20, 'darkGreen', 'forestGreen')
        drawIsoBlock(app, r + 0.2, tCol + 0.2, 45, 0.6, 0.6, 15, 'darkGreen', 'forestGreen')

    # Obstacles
    for obs in lane.obstacles:
        # obs = [col, width, color]
        c, w, color = obs[0], obs[1], obs[2]
        
        if lane.type == 'road': # Cars
            # Body
            drawIsoBlock(app, r + 0.2, c, 10, w, 0.6, 12, 'black', color)
            # Top
            drawIsoBlock(app, r + 0.3, c + 0.2, 22, w - 0.4, 0.4, 6, color, 'lightBlue')
            
        elif lane.type == 'river': # Logs
            drawIsoBlock(app, r + 0.2, c, 2, w, 0.6, 6, 'saddleBrown', 'sienna')

    # Train
    if lane.type == 'train':
        # Tracks
        for c in range(-2, app.cols + 3):
             sx, sy = getIsoScreenPos(app, r, c, 12)
             drawRect(sx, sy, 4, 4, fill='saddleBrown', align='center')

        if lane.trainState == 'PASSING':
            tx = lane.trainX
            # Draw Train Blocks
            # Head
            drawIsoBlock(app, r + 0.1, tx, 12, 10, 0.8, 20, 'darkRed', 'crimson')
            # Smoke
            sx, sy = getIsoScreenPos(app, r, tx + (5 if lane.direction==1 else 0), 35)
            drawCircle(sx, sy - (app.gameTimer % 20), 5 + (app.gameTimer%10), fill='gray', opacity=50)

def drawHUD(app):
    drawLabel(f"{app.score}", app.width/2, 50, size=30, fill='white', bold=True, border='black')

def main():
    runApp(width=400, height=600)

if __name__ == '__main__':
    main()