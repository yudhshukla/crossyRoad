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
    app.deathType = None # 'squished' or 'splashed'
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
        
def generateRandomLaneType():
    return random.choice(['grass', 'grass', 'road', 'road', 'road', 'river', 'river'])

def createLane(app, rowIndex, laneType):
    direction = random.choice([-1, 1])
    speed = random.randint(5, 15) / 100 
    lane = Lane(laneType, direction, speed)
    
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

    if laneType == 'grass':
        numTrees = random.randint(0, 3) 
        for _ in range(numTrees):
            tCol = random.randint(0, app.cols - 1)
            lane.trees.add(tCol)
            
    if laneType in ['grass', 'road']:
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
    
    playerLane = app.lanes.get(app.playerRow)
    
    # 1. Update Obstacles
    for rowIdx in app.lanes:
        lane = app.lanes[rowIdx]
        if lane.type == 'grass': continue
        
        for obs in lane.obstacles:
            obs[0] += lane.speed * lane.direction
            if lane.direction == 1 and obs[0] > app.cols + 2:
                obs[0] = -obs[1] - 2
            elif lane.direction == -1 and obs[0] < -obs[1] - 2:
                obs[0] = app.cols + 2
                
    # 2. Check Collisions
    if playerLane:
        # Coins
        if app.playerCol in playerLane.coins:
            playerLane.coins.remove(app.playerCol)
            app.coins += 1

        # Car Collision
        if playerLane.type == 'road':
            for obs in playerLane.obstacles:
                carX, carW = obs[0], obs[1]
                # Hitbox check
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
                 # Carried off screen
                triggerGameOver(app, 'splashed')

    # 3. Smooth Camera Scroll
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
            
    # Calculate Player Screen Position
    baseY = app.height - 100 
    playScreenX = app.playerCol * app.cellSize
    playScreenY = baseY - (app.playerRow * app.cellSize) + app.scrollOffset
    
    # --- DRAW PLAYER OR DEATH ANIMATION ---
    if app.gameOver and app.deathType == 'squished':
        # SQUISH: Draw flat pancake
        # Shift Y down so it's on the road
        flatY = playScreenY + app.cellSize - 10
        drawRect(playScreenX, flatY, app.cellSize, 10, fill='red', border='black')
        # X eyes
        drawLabel("X  X", playScreenX + app.cellSize/2, flatY + 5, size=10, bold=True)
        
    elif app.gameOver and app.deathType == 'splashed':
        # SPLASH: Draw Ripple
        # Center of the cell
        cx = playScreenX + app.cellSize/2
        cy = playScreenY + app.cellSize/2
        drawCircle(cx, cy, 25, fill=None, border='white', borderWidth=3)
        drawCircle(cx, cy, 15, fill=None, border='white', borderWidth=2)
        drawLabel("splash!", cx, cy - 20, fill='white', size=14, bold=True)
        
    else:
        # NORMAL PLAYER
        hopY = 0
        if app.hopTimer > 0:
            hopY = 10 * math.sin(app.hopTimer * 0.6)
            
        # Shadow
        shadowY = baseY - (app.playerRow * app.cellSize) + app.scrollOffset + 5
        drawRect(playScreenX, shadowY, app.cellSize, app.cellSize, fill='black', opacity=30)
        
        # Body
        drawRect(playScreenX, playScreenY - hopY, app.cellSize, app.cellSize, fill=app.playerColor)
        drawCircle(playScreenX + 10, playScreenY - hopY + 10, 3, fill='black')
        drawCircle(playScreenX + 30, playScreenY - hopY + 10, 3, fill='black')

    # --- NEW UI OVERLAY ---
    drawHUD(app)

    # Game Over Screen
    if app.gameOver:
        drawRect(0, app.height/2 - 60, app.width, 140, fill='black', opacity=80)
        
        msg = "SQUISHED!" if app.deathType == 'squished' else "DROWNED!"
        color = "red" if app.deathType == 'squished' else "cyan"
        
        drawLabel(msg, app.width/2, app.height/2 - 20, size=40, fill=color, bold=True, border='white')
        drawLabel(f"Final Score: {app.score}", app.width/2, app.height/2 + 25, size=20, fill='white')
        drawLabel("Press 'r' to Restart", app.width/2, app.height/2 + 50, size=16, fill='lightGrey')

def drawHUD(app):
    # Top Bar Background
    drawRect(0, 0, app.width, 45, fill='black', opacity=60)
    
    # Score (Top Left)
    drawLabel("SCORE", 40, 15, size=10, fill='lightGray', bold=True)
    drawLabel(f"{app.score}", 40, 32, size=20, fill='white', bold=True)
    
    # High Score (Top Middle-ish)
    drawLabel("BEST", 110, 15, size=10, fill='lightGray', bold=True)
    drawLabel(f"{app.highScore}", 110, 32, size=20, fill='white', bold=True)
    
    # Coins (Top Right)
    # Draw a coin icon
    drawCircle(app.width - 70, 22, 12, fill='gold', border='orange', borderWidth=2)
    drawLabel("$", app.width - 70, 22, size=16, fill='orange', bold=True)
    
    drawLabel(f"{app.coins}", app.width - 30, 22, size=24, fill='gold', bold=True, align='right')

def drawLane(app, rowIndex, lane):
    baseY = app.height - 100
    screenY = baseY - (rowIndex * app.cellSize) + app.scrollOffset
    
    # Background
    color = 'lightGreen'
    if lane.type == 'road': color = 'dimGray' # Darker road for better contrast
    elif lane.type == 'river': color = 'cornflowerBlue'
    drawRect(0, screenY, app.width, app.cellSize, fill=color)
    
    # Road Striping
    if lane.type == 'road':
         drawLine(0, screenY + 2, app.width, screenY + 2, fill='white', dashes=True)
         drawLine(0, screenY + app.cellSize - 2, app.width, screenY + app.cellSize - 2, fill='white', dashes=True)

    # Water Waves
    if lane.type == 'river':
        for i in range(5):
            waveX = (i * 100 + app.waveTimer * 10) % app.width
            drawLabel("~ ~ ~", waveX, screenY + app.cellSize/2, size=16, fill='white', opacity=60)

    # Coins
    for coinCol in lane.coins:
        cx = coinCol * app.cellSize + app.cellSize/2
        cy = screenY + app.cellSize/2
        # Coin spin effect (visual only)
        w = 12 + 4 * math.sin(app.waveTimer)
        drawCircle(cx, cy, 10, fill='gold', border='orange') # Backing
        drawOval(cx, cy, w, 20, fill='yellow') # Spinning inner

    # Obstacles
    for obs in lane.obstacles:
        xPos = obs[0] * app.cellSize
        width = obs[1] * app.cellSize
        color = obs[2]
        
        if lane.type == 'road':
            # Car
            drawRect(xPos, screenY + 5, width, app.cellSize - 10, fill=color, border='black', borderWidth=1)
            drawRect(xPos + 5, screenY + 8, width - 10, app.cellSize - 16, fill='lightBlue', opacity=50)
            # Headlights
            drawCircle(xPos + width - 2, screenY + 12, 3, fill='yellow')
            drawCircle(xPos + width - 2, screenY + app.cellSize - 12, 3, fill='yellow')
        elif lane.type == 'river':
            # Log
            drawRect(xPos, screenY + 5, width, app.cellSize - 10, fill='saddleBrown', border='black', borderWidth=1)
            
    # Trees
    for tCol in lane.trees:
        tx = tCol * app.cellSize
        drawRect(tx + 12, screenY + 20, 16, 20, fill='saddleBrown')
        drawCircle(tx + 20, screenY + 15, 18, fill='darkGreen', border='black', borderWidth=1)

def main():
    runApp(width=400, height=600)

if __name__ == '__main__':
    main()