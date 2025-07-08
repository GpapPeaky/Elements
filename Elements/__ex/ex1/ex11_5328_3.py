import numpy as np
import math

from OpenGL.GL import GL_TRIANGLES

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.Event import Event

from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem # Required for the wireframe toggle

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.utils.Shortcuts import displayGUI_text
example_description = \
"Exercise 1.1 - CSD5328\n"

winWidth = 1024
winHeight = 768

scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))

entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))

#Simple Cube
# vertexCube = np.array([
#     [-0.5, -0.5, 0.5, 1.0],
#     [-0.5, 0.5, 0.5, 1.0],
#     [0.5, 0.5, 0.5, 1.0],
#     [0.5, -0.5, 0.5, 1.0], 
#     [-0.5, -0.5, -0.5, 1.0], 
#     [-0.5, 0.5, -0.5, 1.0], 
#     [0.5, 0.5, -0.5, 1.0], 
#     [0.5, -0.5, -0.5, 1.0]
# ],dtype=np.float32) 
# colorCube = np.array([
#     [0.0, 0.0, 0.0, 1.0],
#     [1.0, 0.0, 0.0, 1.0],
#     [1.0, 1.0, 0.0, 1.0],
#     [0.0, 1.0, 0.0, 1.0],
#     [0.0, 0.0, 1.0, 1.0],
#     [1.0, 0.0, 1.0, 1.0],
#     [1.0, 1.0, 1.0, 1.0],
#     [0.0, 1.0, 1.0, 1.0]
# ], dtype=np.float32)
# 
# #index arrays for above vertex Arrays
# 
# indexCube = np.array((1,0,3, 1,3,2, 
#                   2,3,7, 2,7,6,
#                   3,0,4, 3,4,7,
#                   6,5,1, 6,1,2,
#                   4,5,6, 4,6,7,
#                   5,4,0, 5,0,1), np.uint32) #rhombus out of two triangles
# 
# 
# 
# 
# ## ADD CUBE ##
# # attach a simple cube in a RenderMesh so that VertexArray can pick it up
# mesh4.vertex_attributes.append(vertexCube)
# mesh4.vertex_attributes.append(colorCube)
# mesh4.vertex_index.append(indexCube)
# vArray4 = scene.world.addComponent(node4, VertexArray())
# decorated components and systems with sample, default pass-through shader with uniform MVP

#Simple sphere
vertexSphere = []
colorSphere = []

#index arrays for above vertex Arrays
indexSphere = []

def generateSphere(radius=0.2, sectorCount=3, stackCount=3):
    global vertexSphere, colorSphere, indexSphere
    vertexSphere = []
    colorSphere = []
    indexSphere = []

    for i in range(stackCount + 1):
        stackAngle = math.pi / 2 - i * math.pi / stackCount  # from pi/2 to -pi/2
        xy = radius * math.cos(stackAngle)
        z = radius * math.sin(stackAngle)

        for j in range(sectorCount + 1):
            sectorAngle = j * 2 * math.pi / sectorCount  # from 0 to 2pi

            x = xy * math.cos(sectorAngle)
            y = xy * math.sin(sectorAngle)

            # Normalize coords
            # Divide them by their length
            length = math.sqrt(x * x + y * y + z * z)
            if length > 0: # Avoid division by zero
                xn, yn, zn = x / length, y / length, z / length

            # Add vertex position
            vertexSphere.append((x, y, z))

            # Add a simple color (you can change this to a better coloring scheme)
            colorSphere.append((xn, yn, zn, 1.0))

    # Indices
    for i in range(stackCount):
        for j in range(sectorCount):
            first = i * (sectorCount + 1) + j
            second = first + sectorCount + 1

            indexSphere.append((first, second, first + 1))
            indexSphere.append((second, second + 1, first + 1))

# Generate the sphere vertices and indices
generateSphere(2, 36, 12)

## Add sphere ##
# attach a simple Sphere in a RenderMesh so that VertexArray can pick it up
mesh4.vertex_attributes.append(vertexSphere)
mesh4.vertex_attributes.append(colorSphere)
mesh4.vertex_index.append(indexSphere)
vArray4 = scene.world.addComponent(node4, VertexArray(primitive=GL_TRIANGLES))

########

model = util.translate(0.0,0.0,0.5)@util.scale(3)
eye = util.vec(1.0, 1.0, 1.0)
target = util.vec(0,0.0,0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)

# projMat = util.perspective(120.0, 1.33, 0.1, 100.0)
projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -10, 10.0)

mvpMat =  projMat @ view @ model

shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

# Systems
initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

scene.world.print()

running = True
# MAIN RENDERING LOOP
scene.init(imgui = True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "Ex1.1 CSD5328")

# Event manager, after the scene initialisation

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()

eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._publishers['OnUpdateWireframe'] = gGUI

eManager._subscribers['OnUpdateCamera'] = gWindow 
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
eManager._publishers['OnUpdateCamera'] = gGUI

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

# Wireframe toggle
wireFrameToggle = False

while running:
    running = scene.render()
    displayGUI_text(example_description)

    changed = gGUI._checkbox
    currentWireframeState = gGUI._checkbox
    if changed:
        wireFrameToggle = currentWireframeState
        event = Event(name = 'OnUpdateWireframe', id = None, value = wireFrameToggle)
        eManager.notify('OnUpdateWireframe', event)

    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()
    
scene.shutdown()

