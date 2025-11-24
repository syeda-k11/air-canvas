import numpy as np
import cv2

class Canvas:
    def __init__(self, brush_size=10):
        self.points = []
        self.current_color = (255, 0, 0)  # Default red
        self.brush_size = brush_size
        self.eraser_mode = False
        self.eraser_size = 30
        self.canvas_img = None
    
    def add_point(self, point):
        self.points.append((point, self.current_color, self.brush_size, self.eraser_mode))
    
    def change_color(self, color):
        self.current_color = color
    
    def set_brush_size(self, size):
        self.brush_size = size
    
    def set_eraser(self, enable):
        self.eraser_mode = enable
    
    def clear(self):
        self.points = []
    
    def get_canvas_overlay(self, height, width):
        if self.canvas_img is None or self.canvas_img.shape[0] != height or self.canvas_img.shape[1] != width:
            self.canvas_img = np.zeros((height, width, 3), dtype=np.uint8)
        else:
            self.canvas_img.fill(0)
        
        for point_info in self.points:
            point, color, size, is_eraser = point_info
            if is_eraser:
                cv2.circle(self.canvas_img, point, self.eraser_size, (0, 0, 0), -1)
            else:
                cv2.circle(self.canvas_img, point, size, color, -1)
        
        return self.canvas_img