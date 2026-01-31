from cmu_graphics import *
import random
import math

# ==========================================
# MODEL: Game State & Data
# ==========================================

def onAppStart(app):
    app.highScore = 0
    restartGame(app)

def restartGame(app):
    app.gameOver = False
    app.deathType = None 
    app.score = 0      
    app.coins = 0      
    
    # Grid settings
    app.cols = 10
    app.cellSize = 40
    app.width = app.cols * app.cellSize
    app.height = 600
    
    # Player settings
    app.playerRow = 0 
    app.playerCol = app.cols // 2
    app.playerColor = 'white'
    
    # Animation States
    app.hopTimer = 0   
    app.waveTimer = 0  
    app.gameTimer = 0 # General timer for events
    
    # Camera/Scroll settings
    app.scrollOffset = 0 
    
    # World Generation
    app.lanes = {} 
    
    # Generate initial safe zone
    for i in range(-2, 4):
        createLane(app, i, 'grass')
        
    # Clear trees from start pos
    if 0 in app.lanes and app.playerCol in app.lanes[0].trees:
        app.lanes[0].trees.remove(app.playerCol)
        
    # Generate upcoming world
    for i in range(4, 20):
        createLane(app, i, generateRandomLaneType())

class Lane:
    def __init__(self, laneType, direction, speed):
        self.type = laneType 
        self.direction = direction 
        self.speed = speed
        self.obstacles = [] 
        self.trees = set()  
        self.coins = set()
        
        # Train Specific Properties
        self.trainState = 'IDLE' # IDLE, WARNING, PASSING
        self.trainTimer = random.randint(100, 300) # Time until next event
        self.trainX = -1000 # Position of train head
        
def generateRandomLaneType():
    # Adjusted probabilities to include Train
    return random.choice(['grass', 'grass', 'road', 'road', 'road', 'river', 'river', 'train'])

def createLane(app, rowIndex, laneType):
    direction = random.choice([-1, 1])
    speed = random.randint(5, 15) / 100 
    
    if laneType == 'train':
        speed = 1.2 # Trains are VERY fast
        
    lane = Lane(laneType, direction, speed)
    
    # 1. Generate Moving Obstacles (Road/River)
    if laneType == 'road':
        numCars = random.randint(1, 3)
        for _ in range(numCars):
            pos = random.uniform(0, app.cols)
            width = random.uniform(1.5, 2.5) 
            color = random.choice(['red', 'blue', 'purple', 'orange'])
            lane.obstacles.append([pos, width, color])
            
    elif laneType == 'river':
        numLogs = random.randint(2, 3)
        lane.speed = random.randint(3, 8) / 100 
        for _ in range(numLogs):
            pos = random.uniform(0, app.cols)
            width = random.uniform(2, 4)
            color = 'saddleBrown'
            lane.obstacles.append([pos, width, color])

    # 2. Generate Static Terrain (Trees) & Coins
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
# CONTROLLER: Logic & Movement
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
    if newCol < 0 or newCol >= app.cols: return
    
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
        
    if app.playerRow + 20 not in app.lanes:
        createLane(app, app.playerRow + 20, generateRandomLaneType())

def onStep(app):
    if app.gameOver: return
    
    if app.hopTimer > 0: app.hopTimer -= 1
    app.waveTimer += 0.2
    app.gameTimer += 1
    
    playerLane = app.lanes.get(app.playerRow)
    
    # Update All Lanes
    for rowIdx in app.lanes:
        lane = app.lanes[rowIdx]
        
        # --- TRAIN LOGIC ---
        if lane.type == 'train':
            lane.trainTimer -= 1
            if lane.trainState == 'IDLE':
                if lane.trainTimer <= 0:
                    lane.trainState = 'WARNING'
                    lane.trainTimer = 60 # 2 seconds warning (assuming 30fps)
            elif lane.trainState == 'WARNING':
                if lane.trainTimer <= 0:
                    lane.trainState = 'PASSING'
                    # Set train start pos based on direction
                    if lane.direction == 1: lane.trainX = -15 # Start left
                    else: lane.trainX = app.cols + 15 # Start right
            elif lane.trainState == 'PASSING':
                # Move Train
                lane.trainX += lane.speed * lane.direction
                # Check if done
                if (lane.direction == 1 and lane.trainX > app.cols + 20) or \
                   (lane.direction == -1 and lane.trainX < -20):
                    lane.trainState = 'IDLE'
                    lane.trainTimer = random.randint(150, 400)
                    
        # --- OBSTACLE MOVEMENT ---
        if lane.type != 'grass':
            for obs in lane.obstacles:
                obs[0] += lane.speed * lane.direction
                if lane.direction == 1 and obs[0] > app.cols + 2:
                    obs[0] = -obs[1] - 2
                elif lane.direction == -1 and obs[0] < -obs[1] - 2:
                    obs[0] = app.cols + 2
                
    # --- COLLISIONS ---
    if playerLane:
        # Coins
        if app.playerCol in playerLane.coins:
            playerLane.coins.remove(app.playerCol)
            app.coins += 1

        # Train Collision
        if playerLane.type == 'train' and playerLane.trainState == 'PASSING':
            # Train is VERY wide (length of 10 blocks)
            trainLen = 15
            tx = playerLane.trainX
            # Simple overlap check assuming train is long
            # If train is moving Right, tx is the HEAD (front). Tail is tx - len
            if playerLane.direction == 1:
                if app.playerCol < tx and app.playerCol > tx - trainLen:
                    triggerGameOver(app, 'squished')
            else:
                if app.playerCol > tx and app.playerCol < tx + trainLen:
                    triggerGameOver(app, 'squished')

        # Car Collision
        elif playerLane.type == 'road':
            for obs in playerLane.obstacles:
                carX, carW = obs[0], obs[1]
                if (app.playerCol < carX + carW - 0.2 and 
                    app.playerCol + 1 > carX + 0.2):
                    triggerGameOver(app, 'squished')
        
        # River Logic
        elif playerLane.type == 'river':
            onLog = False
            for obs in playerLane.obstacles:
                logX, logW = obs[0], obs[1]
                if (app.playerCol + 0.3 >= logX and 
                    app.playerCol + 0.7 <= logX + logW):
                    onLog = True
                    app.playerCol += playerLane.speed * playerLane.direction
                    break
            
            if not onLog:
                triggerGameOver(app, 'splashed')
            elif app.playerCol < -1 or app.playerCol > app.cols:
                triggerGameOver(app, 'splashed')

    # Smooth Camera Scroll
    targetScroll = (app.playerRow * app.cellSize)
    app.scrollOffset += (targetScroll - app.scrollOffset) * 0.1

def triggerGameOver(app, type):
    app.gameOver = True
    app.deathType = type

# ==========================================
# VIEW: Drawing
# ==========================================

def redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill='lightBlue')
    
    centerRow = int(app.scrollOffset / app.cellSize)
    rowsOnScreen = int(app.height / app.cellSize) + 2
    startDrawRow = centerRow - 2
    endDrawRow = centerRow + rowsOnScreen
    
    # Draw Lanes
    for r in range(startDrawRow, endDrawRow):
        if r in app.lanes:
            drawLane(app, r, app.lanes[r])
            
    # Draw Player
    baseY = app.height - 100 
    playScreenX = app.playerCol * app.cellSize
    playScreenY = baseY - (app.playerRow * app.cellSize) + app.scrollOffset
    
    if app.gameOver and app.deathType == 'squished':
        flatY = playScreenY + app.cellSize - 10
        drawRect(playScreenX, flatY, app.cellSize, 10, fill='red', border='black')
        drawLabel("X  X", playScreenX + app.cellSize/2, flatY + 5, size=10, bold=True)
    elif app.gameOver and app.deathType == 'splashed':
        cx, cy = playScreenX + app.cellSize/2, playScreenY + app.cellSize/2
        drawCircle(cx, cy, 25, fill=None, border='white', borderWidth=3)
        drawCircle(cx, cy, 15, fill=None, border='white', borderWidth=2)
        drawLabel("splash!", cx, cy - 20, fill='white', size=14, bold=True)
    else:
        hopY = 0
        if app.hopTimer > 0: hopY = 10 * math.sin(app.hopTimer * 0.6)
        
        # Shadow
        shadowY = baseY - (app.playerRow * app.cellSize) + app.scrollOffset + 5
        drawRect(playScreenX, shadowY, app.cellSize, app.cellSize, fill='black', opacity=30)
        
        # Body
        drawRect(playScreenX, playScreenY - hopY, app.cellSize, app.cellSize, fill=app.playerColor)
        drawCircle(playScreenX + 10, playScreenY - hopY + 10, 3, fill='black')
        drawCircle(playScreenX + 30, playScreenY - hopY + 10, 3, fill='black')

    drawHUD(app)

    if app.gameOver:
        drawRect(0, app.height/2 - 60, app.width, 140, fill='black', opacity=80)
        msg = "SQUISHED!" if app.deathType == 'squished' else "DROWNED!"
        color = "red" if app.deathType == 'squished' else "cyan"
        drawLabel(msg, app.width/2, app.height/2 - 20, size=40, fill=color, bold=True, border='white')
        drawLabel(f"Final Score: {app.score}", app.width/2, app.height/2 + 25, size=20, fill='white')
        drawLabel("Press 'r' to Restart", app.width/2, app.height/2 + 50, size=16, fill='lightGrey')

def drawHUD(app):
    drawRect(0, 0, app.width, 45, fill='black', opacity=60)
    drawLabel("SCORE", 40, 15, size=10, fill='lightGray', bold=True)
    drawLabel(f"{app.score}", 40, 32, size=20, fill='white', bold=True)
    drawLabel("BEST", 110, 15, size=10, fill='lightGray', bold=True)
    drawLabel(f"{app.highScore}", 110, 32, size=20, fill='white', bold=True)
    drawCircle(app.width - 70, 22, 12, fill='gold', border='orange', borderWidth=2)
    drawLabel("$", app.width - 70, 22, size=16, fill='orange', bold=True)
    drawLabel(f"{app.coins}", app.width - 30, 22, size=24, fill='gold', bold=True, align='right')

def drawLane(app, rowIndex, lane):
    baseY = app.height - 100
    screenY = baseY - (rowIndex * app.cellSize) + app.scrollOffset
    
    # Backgrounds
    if lane.type == 'road': 
        drawRect(0, screenY, app.width, app.cellSize, fill='dimGray')
        drawLine(0, screenY + 2, app.width, screenY + 2, fill='white', dashes=True)
        drawLine(0, screenY + app.cellSize - 2, app.width, screenY + app.cellSize - 2, fill='white', dashes=True)
    
    elif lane.type == 'train':
        drawRect(0, screenY, app.width, app.cellSize, fill='black')
        # Rails
        drawLine(0, screenY + 10, app.width, screenY + 10, fill='gray')
        drawLine(0, screenY + 30, app.width, screenY + 30, fill='gray')
        # Sleepers
        for i in range(0, app.width, 20):
            drawRect(i, screenY + 8, 5, 24, fill='saddleBrown')
            
    elif lane.type == 'river':
        drawRect(0, screenY, app.width, app.cellSize, fill='cornflowerBlue')
        # Detailed Waves
        for i in range(0, app.width, 40):
            # Create a wave polygon
            offset = (app.waveTimer * 2) % 40
            x = i + offset - 40
            # Draw semi-transparent wave shapes
            drawPolygon(x, screenY + 20, x + 20, screenY + 10, x + 40, screenY + 20, 
                        fill='white', opacity=30)
            drawPolygon(x + 20, screenY + 30, x + 40, screenY + 20, x + 60, screenY + 30, 
                        fill='white', opacity=30)
            
    else: # Grass
        drawRect(0, screenY, app.width, app.cellSize, fill='mediumSeaGreen')
        # Grass texture blades
        for i in range(0, app.width, 60):
             drawPolygon(i, screenY+30, i+5, screenY+10, i+10, screenY+30, fill='lightGreen', opacity=40)

    # Coins
    for coinCol in lane.coins:
        cx = coinCol * app.cellSize + app.cellSize/2
        cy = screenY + app.cellSize/2
        w = 12 + 4 * math.sin(app.waveTimer)
        drawCircle(cx, cy, 10, fill='gold', border='orange') 
        drawOval(cx, cy, w, 20, fill='yellow') 

    # TRAIN LOGIC DRAWING
    if lane.type == 'train':
        # Traffic Light
        lightColor = 'black'
        lightFill = 'darkRed'
        if lane.trainState == 'WARNING':
            # Flash
            if (app.gameTimer // 5) % 2 == 0: lightFill = 'red'
        
        # Draw Light Post (always visible)
        drawRect(app.width - 30, screenY - 20, 5, 25, fill='gray') # Pole
        drawRect(app.width - 40, screenY - 25, 25, 15, fill='black') # Box
        drawCircle(app.width - 35, screenY - 18, 4, fill=lightFill) # Light
        drawCircle(app.width - 20, screenY - 18, 4, fill=lightFill) # Light
        
        # Draw The Train
        if lane.trainState == 'PASSING':
            tx = lane.trainX * app.cellSize
            trainLenPixels = 15 * app.cellSize
            
            # If moving right, tx is HEAD. Rect draws from top-left.
            # We need to draw the rectangle representing the train body.
            if lane.direction == 1:
                drawRect(tx - trainLenPixels, screenY + 2, trainLenPixels, app.cellSize - 4, fill='red', border='white')
                # Windows
                for i in range(10):
                    drawRect(tx - (i*60) - 50, screenY + 8, 30, 15, fill='lightBlue')
            else:
                drawRect(tx, screenY + 2, trainLenPixels, app.cellSize - 4, fill='red', border='white')
                for i in range(10):
                    drawRect(tx + (i*60) + 20, screenY + 8, 30, 15, fill='lightBlue')

    # Standard Obstacles
    for obs in lane.obstacles:
        xPos = obs[0] * app.cellSize
        width = obs[1] * app.cellSize
        color = obs[2]
        
        if lane.type == 'road':
            # Car
            drawRect(xPos, screenY + 5, width, app.cellSize - 10, fill=color, border='black', borderWidth=1)
            drawRect(xPos + 5, screenY + 8, width - 10, app.cellSize - 16, fill='lightBlue', opacity=50)
            # Wheels
            drawCircle(xPos + 10, screenY + app.cellSize - 2, 4, fill='black')
            drawCircle(xPos + width - 10, screenY + app.cellSize - 2, 4, fill='black')
            
        elif lane.type == 'river':
            # Log with wood grain detail
            drawRect(xPos, screenY + 5, width, app.cellSize - 10, fill='saddleBrown', border='black', borderWidth=1)
            drawLine(xPos + 10, screenY + 10, xPos + width - 10, screenY + 10, fill='sienna', lineWidth=2)
            
    # Trees (Detailed)
    for tCol in lane.trees:
        tx = tCol * app.cellSize + app.cellSize/2
        ty = screenY + app.cellSize - 5
        
        # Shadow
        drawOval(tx, ty, 30, 10, fill='black', opacity=30)
        
        # Tree Layers (Pine style)
        # Bottom Layer
        drawPolygon(tx - 15, ty, tx + 15, ty, tx, ty - 25, fill='forestGreen')
        # Middle Layer
        drawPolygon(tx - 12, ty - 15, tx + 12, ty - 15, tx, ty - 35, fill='forestGreen')
        # Top Layer
        drawPolygon(tx - 8, ty - 30, tx + 8, ty - 30, tx, ty - 45, fill='forestGreen')

def main():
    runApp(width=400, height=600)

if __name__ == '__main__':
    main()