"""
BasicWindow example, showcasing the pyglGA SDK ECSS
    
glGA SDK v2021.0.5 ECSS (Entity Component System in a Scenegraph)
@Coopyright 2020-2021 George Papagiannakis
    
The classes below are all related to the GUI and Display of 3D 
content using the OpenGL, GLSL and SDL2, ImGUI APIs, on top of the
Elements ECSS package
"""

from __future__         import annotations
from asyncore import dispatcher
from math import sin, cos, radians
from enum import Enum
from random import uniform;
import imgui.integrations
import numpy as np

import OpenGL.GL as gl;
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform,  RenderMesh
from Elements.pyECSS.Event import Event

from Elements.pyGLV.GUI.Viewer import  RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera
from Elements.utils.terrain import generateTerrain
from Elements.utils.normals import Convert
from OpenGL.GL import GL_LINES

from Elements.utils.Shortcuts import displayGUI_text
example_description = \
"Live 1 - CSD5328\n"

import numpy as np

class GameObjectEntity(Entity):
    def __init__(self, name=None, type=None, id=None) -> None:
        super().__init__(name, type, id);

        # Gameobject basic properties
        self._color          = [1, 0.5, 0.2, 1.0]; # this will be used as a uniform var
        # Create basic components of a primitive object
        self.trans          = BasicTransform(name="trans", trs=util.identity());
        self.mesh           = RenderMesh(name="mesh");
        # self.shaderDec      = ShaderGLDecorator(Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG));
        self.shaderDec      = ShaderGLDecorator(Shader(vertex_source= Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG));
        self.vArray         = VertexArray();
        self.visible        = True; # used for visibility in the scenegraph

        # Add components to entity
        scene = Scene();
        scene.world.createEntity(self);
        scene.world.addComponent(self, self.trans);
        scene.world.addComponent(self, self.mesh);
        scene.world.addComponent(self, self.shaderDec);
        scene.world.addComponent(self, self.vArray);
    
    @property
    def color(self):
        return self._color;
    @color.setter
    def color(self, colorArray):
        self._color = colorArray;

    def drawSelfGui(self, imgui):
        # changed, value = imgui.color_edit3("Color", self.color[0], self.color[1], self.color[2]);
        imgui.begin("TRS, Visibility toggles") # ass

        imgui.text(f"Name: {self.name}")
        changed, newVisibility = imgui.checkbox(f"Visible ##{self.name}", self.visible); # We need to add the {self.name} to the label to differentiate between multiple objects
        if changed:
            self.visible = newVisibility
            print(f"Visible of {self.name} toggled to {self.visible}")


        # Decompose current matrix
        translation, rotation, scale = decomposeTRS(self.trans.trs)

        # Convert rotation from radians to degrees for UI sliders
        rotation_deg = np.degrees(rotation)

        imgui.push_item_width(100)

        changed_tx, translation[0] = imgui.slider_float(f"##Translate X {self.name}", translation[0], -10.0, 10.0)
        imgui.same_line()
        changed_ty, translation[1] = imgui.slider_float(f"##Translate Y {self.name}", translation[1], -10.0, 10.0)
        imgui.same_line()
        changed_tz, translation[2] = imgui.slider_float(f"##Translate Z {self.name}", translation[2], -10.0, 10.0)

        changed_rx, rotation_deg[0] = imgui.slider_float(f"##Rotate X {self.name}", rotation_deg[0], -180.0, 180.0)
        imgui.same_line()
        changed_ry, rotation_deg[1] = imgui.slider_float(f"##Rotate Y {self.name}", rotation_deg[1], -180.0, 180.0)
        imgui.same_line()
        changed_rz, rotation_deg[2] = imgui.slider_float(f"##Rotate Z {self.name}", rotation_deg[2], -180.0, 180.0)

        changed_sx, scale[0] = imgui.slider_float(f"##Scale X {self.name}", scale[0], 0.1, 10.0)
        imgui.same_line()
        changed_sy, scale[1] = imgui.slider_float(f"##Scale Y {self.name}", scale[1], 0.1, 10.0)
        imgui.same_line()
        changed_sz, scale[2] = imgui.slider_float(f"##Scale Z {self.name}", scale[2], 0.1, 10.0)

        imgui.pop_item_width()

        # If anything changed, recombine
        if any([changed_tx, changed_ty, changed_tz,
                changed_rx, changed_ry, changed_rz,
                changed_sx, changed_sy, changed_sz]):
            
            # Convert rotation back to radians
            rotation = np.radians(rotation_deg)

            # Compose new matrix
            new_trs = composeTRS(translation, rotation, scale)
            
            # Update matrix
            self.trans.trs[:] = new_trs

        # Optionally display values
        imgui.text(f"Translation: {translation}")
        imgui.text(f"Rotation (deg): {rotation_deg}")
        imgui.text(f"Scale: {scale}")


        imgui.end()

    def preDraw(self):
        # Set the shader uniform variables
        self.shaderDec.setUniformVariable(key='modelViewProj', value=self.trans.l2cam, mat4=True);
    
    def SetVertexAttributes(self, vertex, color, index, normals = None):
        self.mesh.vertex_attributes.append(vertex);
        self.mesh.vertex_attributes.append(color);
        if normals is not None:
            self.mesh.vertex_attributes.append(normals);
        self.mesh.vertex_index.append(index);

def CubeSpawn(cubename = "Cube"): 
    cube = GameObjectEntity(cubename);
    vertices = [
        [-0.5, -0.5, 0.5, 1.0],
        [-0.5, 0.5, 0.5, 1.0],
        [0.5, 0.5, 0.5, 1.0],
        [0.5, -0.5, 0.5, 1.0], 
        [-0.5, -0.5, -0.5, 1.0], 
        [-0.5, 0.5, -0.5, 1.0], 
        [0.5, 0.5, -0.5, 1.0], 
        [0.5, -0.5, -0.5, 1.0]
    ];
    colors = [
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0]                    
    ];
    # OR
    # colors =  [cube.color] * len(vertices) 
    
    
    #index arrays for above vertex Arrays
    indices = np.array(
        (
            1,0,3, 1,3,2, 
            2,3,7, 2,7,6,
            3,0,4, 3,4,7,
            6,5,1, 6,1,2,
            4,5,6, 4,6,7,
            5,4,0, 5,0,1
        ),
        dtype=np.uint32
    ) #rhombus out of two triangles

    vertices, colors, indices, normals = Convert(vertices, colors, indices, produceNormals=True);
    cube.SetVertexAttributes(vertices, colors, indices, normals);

    
    return cube;

def generatePyramid(name="Pyramid"):
    pyramid = GameObjectEntity(name)

    # Vertex positions (4D: x, y, z, w)
    vertices = [
        [0.0, 1.0, 0.0, 1.0],    # Apex (top)
        [-0.5, -0.5, 0.5, 1.0],  # Base front-left
        [0.5, -0.5, 0.5, 1.0],   # Base front-right
        [0.5, -0.5, -0.5, 1.0],  # Base back-right
        [-0.5, -0.5, -0.5, 1.0]  # Base back-left
    ]

    # Vertex colors (RGBA)
    colors = [
        [0.5, 0.3, 0.0, 1.0],  # Apex color
        [0.5, 0.3, 0.0, 1.0],  # Base colors
        [0.5, 0.3, 0.0, 1.0],
        [0.5, 0.3, 0.0, 1.0],
        [0.5, 0.3, 0.0, 1.0]
    ]

    # Indices defining the faces (triangles)
    indices = np.array([
        # Base (two triangles)
        1, 2, 3,
        1, 3, 4,
        # Side faces (4 triangles)
        0, 1, 2,  # Front
        0, 2, 3,  # Right
        0, 3, 4,  # Back
        0, 4, 1   # Left
    ], dtype=np.uint32)

    # Generate normals, convert vertex format, etc.
    vertices, colors, indices, normals = Convert(vertices, colors, indices, produceNormals=True)
    pyramid.SetVertexAttributes(vertices, colors, indices, normals)

    return pyramid

def spawnColorCube(name):
    cube = GameObjectEntity(name);
    vertices = [
        [-0.666, -0.666, 0.666, 1.0],
        [-0.666, 0.666, 0.666, 1.0],
        [0.666, 0.666, 0.666, 1.0],
        [0.666, -0.666, 0.666, 1.0], 
        [-0.666, -0.666, -0.666, 1.0], 
        [-0.666, 0.666, -0.666, 1.0], 
        [0.666, 0.666, -0.666, 1.0], 
        [0.666, -0.666, -0.666, 1.0]
    ];
    colors = [
        [1.0, 0.0, 0.0, 1.0],
        [0.75, 0.75, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [0.75, 0.75, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [0.75, 0.75, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [0.75, 0.75, 0.0, 1.0]                    
    ];
    # OR
    # colors =  [cube.color] * len(vertices) 
    
    
    #index arrays for above vertex Arrays
    indices = np.array(
        (
            1,0,3, 1,3,2, 
            2,3,7, 2,7,6,
            3,0,4, 3,4,7,
            6,5,1, 6,1,2,
            4,5,6, 4,6,7,
            5,4,0, 5,0,1
        ),
        dtype=np.uint32
    ) #rhombus out of two triangles

    vertices, colors, indices, normals = Convert(vertices, colors, indices, produceNormals=True);
    cube.SetVertexAttributes(vertices, colors, indices, normals);

    cube.trans.trs = util.translate(3, 0.5, 2);
    
    return cube;

def generateQuad(name, r, g, b):
    quad = GameObjectEntity(name);
    vertices = [
        [-0.5, -0.5, 0.5, 1.0],
        [-0.5, 0.5, 0.5, 1.0],
        [0.5, 0.5, 0.5, 1.0],
        [-0.5, -0.5, 0.5, 1.0],
        [0.5, -0.5, 0.5, 1.0],
        [0.5, 0.5, 0.5, 1.0],
    ];
    colors = [
        [r, 0, 0, 1.0],
        [r, 0, 0, 1.0],
        [r, 0, 0, 1.0],
        [0, 0, r, 1.0],                   
        [0, 0, r, 1.0],                   
        [0, 0, r, 1.0]           
    ];
    # OR
    # colors =  [cube.color] * len(vertices) 
    
    
    #index arrays for above vertex Arrays
    indices = np.array(
        (
            0,1,2, 3,4,5 
        ),
        dtype=np.uint32
    ) #rhombus out of two triangles

    vertices, colors, indices, normals = Convert(vertices, colors, indices, produceNormals=True);
    quad.SetVertexAttributes(vertices, colors, indices, normals);

    return quad;

def ter_gen(cubename = "ter"): 
    cube = GameObjectEntity(cubename);
    vertices = [
        [-0.5, -0.5, 0.5, 1.0],
        [-0.5, 0.5, 0.5, 1.0],
        [0.5, 0.5, 0.5, 1.0],
        [0.5, -0.5, 0.5, 1.0], 
        [-0.5, -0.5, -0.5, 1.0], 
        [-0.5, 0.5, -0.5, 1.0], 
        [0.5, 0.5, -0.5, 1.0], 
        [0.5, -0.5, -0.5, 1.0]
    ];
    colors = [
        [0.1, 0.1, 0.1, 1.0],
        [0.2, 0.2, 0.2, 1.0],
        [0.3, 0.3, 0.3, 1.0],
        [0.4, 0.4, 0.4, 1.0],
        [0.6, 0.6, 0.6, 1.0],
        [0.7, 0.7, 0.7, 1.0],
        [0.8, 0.8, 0.8, 1.0],
        [1.0, 1.0, 1.0, 1.0]                    
    ];
    # OR
    # colors =  [cube.color] * len(vertices) 
    
    
    #index arrays for above vertex Arrays
    indices = np.array(
        (
            1,0,3, 1,3,2, 
            2,3,7, 2,7,6,
            3,0,4, 3,4,7,
            6,5,1, 6,1,2,
            4,5,6, 4,6,7,
            5,4,0, 5,0,1
        ),
        dtype=np.uint32
    ) #rhombus out of two triangles

    vertices, colors, indices, normals = Convert(vertices, colors, indices, produceNormals=True);
    cube.SetVertexAttributes(vertices, colors, indices, normals);

    return cube;


def main(imguiFlag = False):
    ##########################################################
    # Instantiate a simple complete ECSS with Entities, 
    # Components, Camera, Shader, VertexArray and RenderMesh
    #########################################################
    
    winWidth = 1024
    winHeight = 1024
    
    scene = Scene()    

    # Initialize Systems used for this script
    # Very important
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())
    
    # Scenegraph with Entities, Components
    rootEntity = scene.world.createEntity(Entity(name="Root"))

    # Spawn Camera
    mainCamera = SimpleCamera("Simple Camera")
    # Camera Settings
    mainCamera.trans2.trs = util.translate(0, 0, 8) # VIEW
    mainCamera.trans1.trs = util.rotate((1, 0, 0), -45); 

    #-----------------------------------------
    # quad
    quad = scene.world.createEntity(Entity("Quad"))
    scene.world.addEntityChild(rootEntity, quad)

    quad_Obj = generateQuad("quad", 1.0, 0.0, 0.0)

    quad_Obj.trans.trs = util.translate(2.0, 0.0, 0.0);

    trans = BasicTransform(name="trans", trs=util.identity());    
    scene.world.addComponent(quad, trans)
    
    scene.world.addEntityChild(quad, quad_Obj)

    quad.getChild(0).trs = util.translate(0, 0.5, 0)

    # terrain
    terrain = scene.world.createEntity(Entity("terrain"))
    scene.world.addEntityChild(rootEntity, terrain)
    
    trans = BasicTransform(name="trans", trs=util.identity());    
    scene.world.addComponent(terrain, trans)
    
    terrain_Obj: GameObjectEntity = ter_gen("ter")
    scene.world.addEntityChild(terrain, terrain_Obj)
    
    terrain.getChild(0).trs = util.scale(20.0, 0.1, 20.0)

    # house
    home1 = scene.world.createEntity(Entity("Home"))
    scene.world.addEntityChild(rootEntity, home1)

    trans = BasicTransform(name="trans", trs=util.identity());    
    scene.world.addComponent(home1, trans)
    
    houseCube: GameObjectEntity = CubeSpawn("Cube")
    scene.world.addEntityChild(home1, houseCube) # add entity child to home 1
    
    houseRoof: GameObjectEntity = generatePyramid("Roof, woof woof")
    scene.world.addEntityChild(home1, houseRoof)
    
    home1.getChild(0).trs = util.translate(0, 0.5, 0)
    houseRoof.trans.trs = util.translate(0, 1, 0)

    # cube

    Cube = scene.world.createEntity(Entity("cube"))
    scene.world.addEntityChild(rootEntity, Cube)

    trans = BasicTransform(name="trans", trs=util.identity())   
    scene.world.addComponent(Cube, trans)

    Cube_Obj: GameObjectEntity = spawnColorCube("cuby")
    scene.world.addEntityChild(Cube, Cube_Obj)

    # ---------------------------

    # add axes

    # axes = scene.world.createEntity(Entity(name="axes"))
    # scene.world.addEntityChild(rootEntity, axes)
    # axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))

    # Stinky, but gameObjectEntity needs some more work,
    # as well as terrain generation
    # axesVertices = np.array([
    #     [-1.0, 0.0, 0.0, 1.0],  # X-axis start
    #     [1.0, 0.0, 0.0, 1.0],   # X-axis end
    #     [0.0, -1.0, 0.0, 1.0],  # Y-axis start
    #     [0.0, 1.0, 0.0, 1.0],   # Y-axis end
    #     [0.0, 0.0, -1.0, 1.0],  # Z-axis start
    #     [0.0, 0.0, 1.0, 1.0]    # Z-axis end
    # ], dtype=np.float32)
# 
    # axesColours = np.array([
    #     [1.0, 0.0, 0.0, 1.0],  # Red for X-axis
    #     [1.0, 0.0, 0.0, 1.0],
    #     [0.0, 1.0, 0.0, 1.0],  # Green for Y-axis
    #     [0.0, 1.0, 0.0, 1.0],
    #     [0.0, 0.0, 1.0, 1.0],  # Blue for Z-axis
    #     [0.0, 0.0, 1.0, 1.0]
    # ], dtype=np.float32)
# 
    # axesIndeces = np.array([
    #     0, 1,  # X-axis
    #     2, 3,  # Y-axis
    #     4, 5   # Z-axis
    # ], dtype=np.uint32)

    # Reshape the arrays to match the expected format, 1d is bad, 2d is good, I am not happy
    # axesVertices = axesVertices.reshape(-1, 4)  # 6 vertices, 4 components each
    # axesColours = axesColours.reshape(-1, 4)

    # axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
    # axes_mesh.vertex_attributes.append(axesVertices)
    # axes_mesh.vertex_attributes.append(axesColours)
    # axes_mesh.vertex_index.append(axesIndeces)

    # axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(
    #    Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
    
    # axesGameObjectEntity: GameObjectEntity = GameObjectEntity(name="Axes GameObject Entity")
    # scene.world.addEntityChild(axes, axesGameObjectEntity)

    # scene.world.addComponent(axes, VertexArray(primitive=GL_LINES))

    # terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)
    
    # MAIN RENDERING LOOP
    running = True
    scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "Elements: A CameraSystem Example", customImGUIdecorator = ImGUIecssDecorator2)

    #imGUIecss = scene.gContext


    # ---------------------------------------------------------
    #   Run pre render GLInit traversal for once!
    #   pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
    #   needs an active GL context
    # ---------------------------------------------------------
    
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glDisable(gl.GL_CULL_FACE);

    # gl.glDepthMask(gl.GL_FALSE);  
    gl.glEnable(gl.GL_DEPTH_TEST);
    gl.glDepthFunc(gl.GL_LESS);
    scene.world.traverse_visit(initUpdate, rootEntity)
    

    ############################################
    # Instantiate all Event-related key objects
    ############################################
    
    # instantiate new EventManager
    # need to pass that instance to all event publishers e.g. ImGUIDecorator
    eManager = scene.world.eventManager
    gWindow = scene.renderWindow
    gGUI = scene.gContext
    
    #simple Event actuator System
    renderGLEventActuator = RenderGLStateSystem()
    
    #setup Events and add them to the EventManager
    updateTRS = Event(name="OnUpdateTRS", id=100, value=None)
    updateBackground = Event(name="OnUpdateBackground", id=200, value=None)
    eManager._events[updateTRS.name] = updateTRS
    eManager._events[updateBackground.name] = updateBackground


    eManager._subscribers[updateTRS.name] = gGUI
    eManager._subscribers[updateBackground.name] = gGUI
   
    eManager._subscribers['OnUpdateWireframe'] = gWindow
    eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
    eManager._subscribers['OnUpdateCamera'] = gWindow
    eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
    

    # Add RenderWindow to the EventManager publishers
    eManager._publishers[updateBackground.name] = gGUI

    theta = 2

    while running:
        # Other imgui settings

        # UPDATES:
        #
        #
        # transUpdate: Update the transforms of all entities in the scenegraph
        # camUpdate: Update the camera transforms, else everything moves to screenspace
        # renderUpdate: Update the render state of all entities in the scenegraph
        #
        scene.world.traverse_visit(transUpdate, scene.world.root) 

        scene.world.traverse_visit_pre_camera(camUpdate, mainCamera.camera)
        scene.world.traverse_visit(camUpdate, terrain)
        # scene.world.traverse_visit(camUpdate, axes) # Ugh
        scene.world.traverse_visit(camUpdate, quad) # Break these shit down, else we need to handle the render_post() function differently
        scene.world.traverse_visit(camUpdate, houseCube) # Break these shit down, else we need to handle the render_post() function differently
        scene.world.traverse_visit(camUpdate, houseRoof)
        scene.world.traverse_visit(camUpdate, Cube)

        # --- Terrain

        # --- Axes
        # axes_shader.setUniformVariable(key='modelViewProj', value=terrain_trans.l2cam, mat4=True);  
        
        # call SDLWindow/ImGUI display() and ImGUI event input process
        running = scene.render()
        displayGUI_text(example_description)

        # GameObjectEntity realted GUI

        # call the GL State render System

        # Actual breakdown rendering is done here 
        # --- Home 1
        quad_Obj.preDraw() # Set the shader uniform variables, could be done once, I just don't give a fuck
        scene.world.traverse_visit(renderUpdate, quad_Obj) # This draws everything when at scene.world.root, stupid af

        terrain_Obj.preDraw()
        scene.world.traverse_visit(renderUpdate, terrain_Obj)

        houseCube.preDraw()
        scene.world.traverse_visit(renderUpdate, houseCube)

        houseRoof.preDraw()
        scene.world.traverse_visit(renderUpdate, houseRoof)

        Cube_Obj.preDraw()
        scene.world.traverse_visit(renderUpdate, Cube_Obj)
        
        Cube_Obj.trans.trs =  util.scale(1, 1, 1) @ util.rotate((0, 1, 0), theta) @ util.translate(2, 0, 2)

        theta += 2

        scene.world.traverse_visit(renderUpdate, terrain)


        #if terrainGameObjectEntity.visible:
            #terrainGameObjectEntity.preDraw() # Very hacky shit, but works, we could use the terrain differently ngl
            # Render the terrain
        #    scene.world.traverse_visit(renderUpdate, terrain)

        #if axesGameObjectEntity.visible:
            #axesGameObjectEntity.preDraw()
        #    scene.world.traverse_visit(renderUpdate, axes)

        """
        So let me breakdown what is going on here:

        We have a terrain mesh that is generated as an entity and not a gameObjectEntity,
        meaning, predraw, imgui toggles and all of that shit CANNOT be used.... so what can we do?

        We override the axes/terrain entities with gameObjectEntity objects that work as toggles
        and literally NOTHING ELSE, even the preDraw calls are redundant as the camera/shaders/transforms
        ect, are updated before, due to the scene.world.root visits.

        Is it stupid? ofc, does it work? ofc, is there a better way to do this without 
        changing the source, completely oveloading the type or end up with a gun to my throat??? nu-uh,
        worked on it for about 3 and a half hours, I can't find a better solution.

            -Peaky, 8/7/2025 5:37 AM
        """

        # ImGUI post-display calls and SDLWindow swap 
        scene.render_post()
        
    scene.shutdown()


if __name__ == "__main__":    #
    main(imguiFlag = True)