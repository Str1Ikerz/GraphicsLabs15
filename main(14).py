import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math


class Canvas3D:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        self.scale = 50
        self.zoom_factor = 1.0
        self.rotation_x = 0.0
        self.rotation_y = 0.0

    def project(self, x, y, z):
        cos_x = math.cos(self.rotation_x)
        sin_x = math.sin(self.rotation_x)
        cos_y = math.cos(self.rotation_y)
        sin_y = math.sin(self.rotation_y)

        y_rot = y * cos_x - z * sin_x
        z_rot = y * sin_x + z * cos_x

        x_rot = x * cos_y + z_rot * sin_y
        z_final = -x * sin_y + z_rot * cos_y

        x_proj = x_rot * self.scale * self.zoom_factor + self.center_x
        y_proj = -y_rot * self.scale * self.zoom_factor + self.center_y
        return x_proj, y_proj, z_final

    def draw_axes(self, canvas):
        x_end = self.project(5, 0, 0)
        y_end = self.project(0, 5, 0)
        z_end = self.project(0, 0, 5)
        cx, cy = self.center_x, self.center_y
        canvas.create_line(cx, cy, x_end[0], x_end[1], fill="red", width=2, arrow=tk.LAST)
        canvas.create_line(cx, cy, y_end[0], y_end[1], fill="green", width=2, arrow=tk.LAST)
        canvas.create_line(cx, cy, z_end[0], z_end[1], fill="blue", width=2, arrow=tk.LAST)
        canvas.create_text(x_end[0] + 10, x_end[1], text="X", fill="red")
        canvas.create_text(y_end[0], y_end[1] - 10, text="Y", fill="green")
        canvas.create_text(z_end[0], z_end[1] + 10, text="Z", fill="blue")

    def draw_grid(self, canvas, step=1, size=10):
        for i in range(-size, size + 1, step):
            start = self.project(-size, 0, i)
            end = self.project(size, 0, i)
            canvas.create_line(start[0], start[1], end[0], end[1], fill="lightgray")
            start = self.project(i, 0, -size)
            end = self.project(i, 0, size)
            canvas.create_line(start[0], start[1], end[0], end[1], fill="lightgray")

    def draw_with_zbuffer(self, canvas, polygons):
        zbuffer = [[float('inf')] * self.width for _ in range(self.height)]
        colorbuffer = [['#ffffff'] * self.width for _ in range(self.height)]

        for poly in polygons:
            projected = [self.project(x, y, z) for (x, y, z) in poly['vertices_3d']]
            n = len(projected)

            triangles = []
            if n == 3:
                triangles = [projected]
            elif n >= 4:
                for i in range(2, n):
                    triangles.append([projected[0], projected[i - 1], projected[i]])

            for tri in triangles:
                (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = tri

                min_x = max(0, int(min(x1, x2, x3)))
                max_x = min(self.width - 1, int(max(x1, x2, x3)))
                min_y = max(0, int(min(y1, y2, y3)))
                max_y = min(self.height - 1, int(max(y1, y2, y3)))

                denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
                if abs(denom) < 1e-6:
                    continue

                for y in range(min_y, max_y + 1):
                    for x in range(min_x, max_x + 1):
                        a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / denom
                        b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / denom
                        c = 1 - a - b
                        if a >= 0 and b >= 0 and c >= 0:
                            z = a * z1 + b * z2 + c * z3
                            if z < zbuffer[y][x]:
                                zbuffer[y][x] = z
                                colorbuffer[y][x] = poly['color']

        for y in range(self.height):
            for x in range(self.width):
                if colorbuffer[y][x] != '#ffffff':
                    canvas.create_rectangle(x, y, x + 1, y + 1,
                                            fill=colorbuffer[y][x], outline='')


class GraphicsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа — Вариант 9 (z-буфер)")
        self.root.geometry("1000x650")

        self.canvas = tk.Canvas(root, bg="white", width=800, height=600)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        control_frame = tk.Frame(root)
        control_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)

        scale_frame = tk.LabelFrame(control_frame, text="Масштаб")
        scale_frame.pack(pady=5, fill=tk.X)
        self.scale_var = tk.DoubleVar(value=1.0)
        ttk.Scale(scale_frame, from_=0.5, to=2.0,
                  variable=self.scale_var,
                  orient=tk.HORIZONTAL,
                  command=self.update_scale).pack(padx=5, pady=5)

        rotate_frame = tk.LabelFrame(control_frame, text="Вращение")
        rotate_frame.pack(pady=5, fill=tk.X)
        tk.Button(rotate_frame, text="Вращать X (+)", command=self.rotate_x_pos).pack(pady=2)
        tk.Button(rotate_frame, text="Вращать X (-)", command=self.rotate_x_neg).pack(pady=2)
        tk.Button(rotate_frame, text="Вращать Y (+)", command=self.rotate_y_pos).pack(pady=2)
        tk.Button(rotate_frame, text="Вращать Y (-)", command=self.rotate_y_neg).pack(pady=2)

        action_frame = tk.LabelFrame(control_frame, text="Действия")
        action_frame.pack(pady=10, fill=tk.X)
        tk.Button(action_frame, text="Перерисовать", command=self.redraw).pack(pady=5)
        tk.Button(action_frame, text="Сохранить в OBJ", command=self.save_to_obj).pack(pady=5)

        self.polygons = self.create_objects()
        self.canvas3d = Canvas3D(800, 600)
        self.redraw()


    def create_objects(self):
        cube_v = [
            (-4, -1, -1), (-2, -1, -1), (-2, 1, -1), (-4, 1, -1),
            (-4, -1, 1), (-2, -1, 1), (-2, 1, 1), (-4, 1, 1)
        ]
        cube_faces = [
            [0,1,2,3], [4,5,6,7], [0,1,5,4],
            [2,3,7,6], [0,3,7,4], [1,2,6,5]
        ]
        cube = [{"vertices_3d": [cube_v[i] for i in face], "color": "#ADD8E6"}
                for face in cube_faces]

        p = [(0, 2, 0), (-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)]
        pyramid_faces = [
            [p[0], p[1], p[2]],
            [p[0], p[2], p[3]],
            [p[0], p[3], p[4]],
            [p[0], p[4], p[1]],
            [p[1], p[2], p[3], p[4]]
        ]
        pyramid = [{"vertices_3d": face, "color": "#90EE90"}
                   for face in pyramid_faces]

        arbitrary = [{
            "vertices_3d": [(3, 0, 0), (4, 1.5, 0), (5, 0, 1), (4, -1, 0)],
            "color": "#FFA500"
        }]

        return cube + pyramid + arbitrary


    def update_scale(self, event=None):
        self.canvas3d.zoom_factor = self.scale_var.get()
        self.redraw()

    def rotate_x_pos(self): self.canvas3d.rotation_x += 0.1; self.redraw()
    def rotate_x_neg(self): self.canvas3d.rotation_x -= 0.1; self.redraw()
    def rotate_y_pos(self): self.canvas3d.rotation_y += 0.1; self.redraw()
    def rotate_y_neg(self): self.canvas3d.rotation_y -= 0.1; self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        self.canvas3d.draw_axes(self.canvas)
        self.canvas3d.draw_grid(self.canvas)
        self.canvas3d.draw_with_zbuffer(self.canvas, self.polygons)


    def save_to_obj(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".obj",
            filetypes=[("Wavefront OBJ", "*.obj")]
        )
        if not path:
            return

        vertices = []
        faces = []
        v_map = {}
        idx = 0

        for poly in self.polygons:
            face = []
            for v in poly["vertices_3d"]:
                if v not in v_map:
                    v_map[v] = idx
                    vertices.append(v)
                    idx += 1
                face.append(v_map[v])
            faces.append(face)

        with open(path, "w", encoding="utf-8") as f:
            f.write("# OBJ export from z-buffer lab\n")
            for v in vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            f.write("\n")
            for face in faces:
                f.write("f " + " ".join(str(i + 1) for i in face) + "\n")

        messagebox.showinfo("Готово", "OBJ-файл сохранён")


if __name__ == "__main__":
    root = tk.Tk()
    app = GraphicsApp(root)
    root.mainloop()
