from cmu_graphics import *

def onAppStart(app):
    app.sqSize = 200

def redrawAll(app):
    cx, cy = app.width/2, app.height/2
    drawRect(cx, cy, app.sqSize, app.sqSize, fill='purple', align='center')
    drawLabel('Hello World!', cx, cy, fill='white', 
              align='center', bold=True, size=20)

def main():
    runApp()

main()