# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import numpy #To process coordinates in bulk.
import numpy.linalg #To project window coordinates onto the scene.
from PyQt5.QtGui import QImage
import qimage2ndarray #To convert QImage to Numpy arrays.

from cura.CuraApplication import CuraApplication
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator #To put the scene node on the correct build plate.
from cura.Scene.CuraSceneNode import CuraSceneNode #To create a scene node that causes the support to be drawn/erased.
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator #To create a scene node that can be sliced.
from UM.Job import Job #The interface we're implementing.
from UM.Logger import Logger
from UM.Math.Vector import Vector #To use the mesh builder.
from UM.Mesh.MeshBuilder import MeshBuilder #To create the support structure in 3D.
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation #To create the scene node.

##  Background task to process an image of where the user would like support.
#
#   The coordinates on the cursor are projected onto the scene to place a mesh
#   that creates or removes support.
class ConstructSupportJob(Job):
    def __init__(self, buffer: QImage, depth_image: QImage):
        super().__init__()
        #These parameters need to be obtained outside of the thread so that they are all in sync with the original capture.
        self._buffer = buffer
        self._depth_image = depth_image
        camera = CuraApplication.getInstance().getController().getScene().getActiveCamera()
        self._camera_projection = camera.getProjectionMatrix()
        self._camera_transformation = camera.getWorldTransformation()
        self._camera_position = camera.getPosition()

    def run(self):
        Logger.log("d", "Constructing/removing support.")

        to_support = qimage2ndarray.raw_view(self._buffer)
        depth = qimage2ndarray.recarray_view(self._depth_image)
        depth.a = 0 #Discard alpha channel.
        depth = depth.view(dtype = numpy.int32).astype(numpy.float32) / 1000 #Conflate the R, G and B channels to one 24-bit (cast to 32) float. Divide by 1000 to get mm.
        support_positions_2d = numpy.array(numpy.where(numpy.bitwise_and(to_support == 255, depth < 16777))) #All the 2D coordinates on the screen where we want support.
        support_depths = numpy.take(depth, support_positions_2d[0, :] * depth.shape[1] + support_positions_2d[1, :]) #The depth at those pixels.
        inverted_projection = numpy.linalg.inv(self._camera_projection.getData().copy())
        transformation = self._camera_transformation.getData()

        #For each pixel, get the near and far plane.
        near = numpy.ndarray((4, support_positions_2d.shape[1]))
        near.fill(1)
        near[0: support_positions_2d.shape[0], 0: support_positions_2d.shape[1]] = support_positions_2d
        near[2,:].fill(-1)
        near = numpy.dot(inverted_projection, near)
        near = numpy.dot(transformation, near)
        near = near[0:3] / near[3]
        far = numpy.ndarray((4, support_positions_2d.shape[1]))
        far.fill(1)
        far[0: support_positions_2d.shape[0], 0: support_positions_2d.shape[1]] = support_positions_2d
        far = numpy.dot(inverted_projection, far)
        far = numpy.dot(transformation, far)
        far = far[0:3] / far[3]

        #Direction is from near plane pixel to far plane pixel, normalised.
        direction = far - near
        direction /= numpy.linalg.norm(direction, axis = 0)

        #Final position is in the direction of the pixel, moving with <depth> mm away from the camera position.
        support_positions_3d = (direction * support_depths).transpose() + self._camera_position.getData()

        #Create the 3D mesh.
        builder = MeshBuilder()
        for index, position in enumerate(support_positions_3d):
            builder.addDiamond(1, 2, 1, center = Vector(x = position[0], y = position[1], z = position[2]))

        #Create the scene node and add it to the scene.
        mesh_data = builder.build()
        scene = CuraApplication.getInstance().getController().getScene()
        new_node = CuraSceneNode(parent = scene.getRoot(), name = "CustomSupport")
        new_node.setSelectable(True)
        new_node.setMeshData(mesh_data)
        new_node.addDecorator(BuildPlateDecorator(CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate))
        new_node.addDecorator(SliceableObjectDecorator())
        operation = AddSceneNodeOperation(new_node, scene.getRoot())
        operation.push()

        scene.sceneChanged.emit(new_node)