# SPDX-License-Identifier: GPL-3.0-or-later
"""Native mouse mode: draggable spherical handles and box translation/rotation."""
from chimerax.mouse_modes import MouseMode
from .core.models import SearchBox
from .core.box_geometry import pick_handle, resize


class BoxMouseMode(MouseMode):
    name = 'CHIPIX box'

    def __init__(self, tool):
        super().__init__(tool.session)
        self.tool = tool
        self.handle = None

    def mouse_down(self, event):
        super().mouse_down(event)
        box = self.tool._box()
        near, far = self.view.clip_plane_points(*event.position())
        self.handle = None if near is None or far is None else pick_handle(box, near, far,
                                  max(self.tool.handle_radius.value(), self.view.pixel_size(box.center)*7))

    def mouse_drag(self, event):
        dx, dy = self.mouse_motion(event)
        tool = self.tool
        box = tool._box()
        axes = self.view.camera.position.axes()
        pixel = self.view.pixel_size(box.center)
        # The shifted binding makes depth reachable without changing the camera.
        delta = tuple(pixel*((-dy*axes[2][i]) if event.shift_down()
                            else dx*axes[0][i]-dy*axes[1][i]) for i in range(3))
        operation = tool.mouse_operation.currentData()
        if operation == 'rotate':
            # Euler controls use the same XYZ convention as the docking transform.
            rotation = (box.rotation[0]+dy*.5, box.rotation[1]+dx*.5, box.rotation[2])
            if event.shift_down():
                rotation = (*box.rotation[:2], box.rotation[2]+dx*.5)
            box = SearchBox(box.center, box.size, tuple((v+180)%360-180 for v in rotation))
        elif operation == 'resize' and self.handle and any(self.handle):
            box = resize(box, self.handle, delta)
        elif operation == 'move' or self.handle == (0,0,0):
            box = SearchBox(tuple(a+b for a,b in zip(box.center, delta)), box.size, box.rotation)
        tool._set_box(box)
