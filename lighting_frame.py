from tkinter import *
from dataclasses import dataclass, field

@dataclass
class Bake_settings():
    point_scale: float = 1.0
    area_scale: float = 1.0

@dataclass
class Render_settings():
    overbrightbits: int = 0
    gamma: float = 1.0
    compensate: float = 0.0
    hdr: bool = False
    light_scale: float = 1.0

class Lighting_frame():
    def __init__(self, root):
        frame = Frame(root, padx = 5, pady = 5)
        frame.pack()

        l_render = Label(frame, text="Rendering settings")
        l_render.pack()

        obb = Scale(
            frame,
            from_ = 0,
            to = 2,
            showvalue=0,
            tickinterval=1,
            resolution=1,
            orient=HORIZONTAL,
            label="Overbright bits")
        obb.pack(fill=X)
        obb.set(0)

        l_light = Label(frame, text="Light settings")
        l_light.pack()

        gamma = Scale(
            frame,
            from_ = 0.5,
            to = 4.0,
            tickinterval=0.5,
            resolution=0.1,
            orient=HORIZONTAL,
            label="Gamma")
        gamma.pack(fill=X)
        gamma.set(1.0)

        compensate = Scale(
            frame,
            from_ = 0.5,
            to = 4.0,
            tickinterval=0.5,
            resolution=0.1,
            orient=HORIZONTAL,
            label="Compensate")
        compensate.pack(fill=X)
        compensate.set(1.0)

        light_scale = Scale(
            frame,
            from_ = 0.1,
            to = 10.0,
            tickinterval=2.0,
            resolution=0.1,
            orient=HORIZONTAL,
            label="Light scale")
        light_scale.pack(fill=X)
        light_scale.set(1.0)

        l_baking = Label(frame, text="Bake settings")
        l_baking.pack()
        
        point_scale = Scale(
            frame,
            from_ = 0.1,
            to = 10.0,
            tickinterval=2.0,
            resolution=0.1,
            orient=HORIZONTAL,
            label="Point scale")
        point_scale.pack(fill=X)
        point_scale.set(1.0)

        area_scale = Scale(
            frame,
            from_ = 0.1,
            to = 10.0,
            tickinterval=2.0,
            resolution=0.1,
            orient=HORIZONTAL,
            label="Area scale")
        area_scale.pack(fill=X)
        area_scale.set(1.0)

        self.btn_bake = Button(
            frame,
            text = "Bake Lighting",
            height = 1
        )
        self.btn_bake.pack(fill=X)

        self.btn_bounce = Button(
            frame,
            text = "Add light bounce",
            height = 1
        )
        self.btn_bounce.pack(fill=X)

        self.btn_pack = Button(
            frame,
            text = "Pack Lighting",
            height = 1
        )
        self.btn_pack.pack(fill=X)

        self.frame = frame
        self.focus = frame
        self.obb = obb
        self.gamma = gamma
        self.compensate = compensate
        self.light_scale = light_scale
        self.point_scale = point_scale
        self.area_scale = area_scale
    
    def get_render_settings(self):
        current_settings = Render_settings()
        current_settings.hdr = False # TODO: Implement me!
        current_settings.gamma = self.gamma.get()
        current_settings.compensate = self.compensate.get()
        current_settings.overbrightbits = self.obb.get()
        current_settings.light_scale = self.light_scale.get()
        return current_settings
    
    def get_bake_settings(self):
        current_settings = Bake_settings()
        current_settings.point_scale = self.point_scale.get()
        current_settings.area_scale = self.area_scale.get()
        return current_settings

if __name__ == "__main__":
	print("Please run 'main.py'")