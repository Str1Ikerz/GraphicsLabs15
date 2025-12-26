import tkinter as tk
import math
from tkinter import messagebox, filedialog


class PolyhedronViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Проективные преобразования — гексаэдр и додекаэдр")
        self.root.geometry("900x700")

        self.vertices = []
        self.edges = []
        self.faces = []

        self.rotation_x = 0
        self.rotation_y = 0
        self.rotation_z = 0

        self.center_x = 450
        self.center_y = 350
        self.scale = 130

        self.orthographic = True
        self.figure_type = "Гексаэдр"

        self.create_widgets()
        self.create_figure()
        self.draw()

        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)

    # ---------- Фигуры ----------

    def create_figure(self):
        if self.figure_type == "Гексаэдр":
            self.create_hexahedron()
        else:
            self.create_dodecahedron()

    def create_hexahedron(self):
        self.vertices = [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
        ]

        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

        self.faces = [
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [0, 1, 5, 4],
            [2, 3, 7, 6],
            [0, 3, 7, 4],
            [1, 2, 6, 5]
        ]

    def create_dodecahedron(self):
        phi = (1 + math.sqrt(5)) / 2
        inv = 1 / phi

        cube = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        extra = [
            (0, inv, phi), (0, inv, -phi), (0, -inv, phi), (0, -inv, -phi),
            (inv, phi, 0), (inv, -phi, 0), (-inv, phi, 0), (-inv, -phi, 0),
            (phi, 0, inv), (phi, 0, -inv), (-phi, 0, inv), (-phi, 0, -inv)
        ]

        self.vertices = [self.normalize(v) for v in (cube + extra)]

        self.faces = [
            [0, 1, 9, 8, 4],
            [1, 0, 3, 11, 9],
            [0, 4, 6, 2, 3],
            [4, 8, 10, 5, 6],
            [8, 9, 13, 12, 10],
            [9, 11, 19, 13, 8],
            [11, 3, 2, 14, 19],
            [2, 6, 5, 7, 14],
            [5, 10, 12, 15, 7],
            [12, 13, 19, 17, 15],
            [14, 7, 15, 17, 18],
            [19, 14, 18, 16, 17]
        ]

        edge_set = set()
        for face in self.faces:
            for i in range(len(face)):
                a, b = face[i], face[(i + 1) % len(face)]
                edge_set.add(tuple(sorted((a, b))))
        self.edges = list(edge_set)

    # ---------- Математика ----------

    def normalize(self, v):
        x, y, z = v
        l = math.sqrt(x*x + y*y + z*z)
        return (x/l, y/l, z/l) if l else (0, 0, 0)

    def rotate(self, v):
        x, y, z = v

        y, z = y*math.cos(self.rotation_x) - z*math.sin(self.rotation_x), \
               y*math.sin(self.rotation_x) + z*math.cos(self.rotation_x)

        x, z = x*math.cos(self.rotation_y) + z*math.sin(self.rotation_y), \
              -x*math.sin(self.rotation_y) + z*math.cos(self.rotation_y)

        x, y = x*math.cos(self.rotation_z) - y*math.sin(self.rotation_z), \
               x*math.sin(self.rotation_z) + y*math.cos(self.rotation_z)

        return x, y, z

    def project(self, v):
        x, y, z = v
        if self.orthographic:
            xp, yp = x, y
        else:
            d = 3
            f = d / (d - z) if d != z else 1
            xp, yp = x * f, y * f

        return self.center_x + xp * self.scale, self.center_y - yp * self.scale

    # ---------- Интерфейс ----------

    def create_widgets(self):
        top = tk.Frame(self.root)
        top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.proj_var = tk.BooleanVar(value=True)
        tk.Radiobutton(top, text="Ортогональная",
                       variable=self.proj_var, value=True,
                       command=self.update_projection).pack(side=tk.LEFT)

        tk.Radiobutton(top, text="Центральная",
                       variable=self.proj_var, value=False,
                       command=self.update_projection).pack(side=tk.LEFT)

        self.fig_var = tk.StringVar(value="Гексаэдр")
        tk.OptionMenu(top, self.fig_var, "Гексаэдр", "Додекаэдр",
                      command=self.change_figure).pack(side=tk.LEFT, padx=20)

        tk.Button(top, text="Сохранить в OBJ",
                  command=self.save_to_obj).pack(side=tk.LEFT, padx=10)

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    # ---------- События ----------

    def update_projection(self):
        self.orthographic = self.proj_var.get()
        self.draw()

    def change_figure(self, value):
        self.figure_type = value
        self.create_figure()
        self.draw()

    def on_mouse_click(self, e):
        self.last_x, self.last_y = e.x, e.y

    def on_mouse_drag(self, e):
        self.rotation_y += (e.x - self.last_x) * 0.01
        self.rotation_x += (e.y - self.last_y) * 0.01
        self.last_x, self.last_y = e.x, e.y
        self.draw()

    # ---------- Рисование ----------

    def draw(self):
        self.canvas.delete("all")
        proj = [self.project(self.rotate(v)) for v in self.vertices]

        for a, b in self.edges:
            self.canvas.create_line(*proj[a], *proj[b], width=2, fill="blue")

        for x, y in proj:
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="red")

        text = f"Фигура: {self.figure_type} | Проекция: " \
               f"{'Ортогональная' if self.orthographic else 'Центральная'}"
        self.canvas.create_text(10, 10, anchor=tk.NW, text=text)

    # ---------- Экспорт ----------

    def save_to_obj(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".obj",
            filetypes=[("OBJ files", "*.obj")]
        )
        if not path:
            return

        try:
            with open(path, "w") as f:
                for v in self.vertices:
                    f.write(f"v {v[0]} {v[1]} {v[2]}\n")
                f.write("\n")
                for face in self.faces:
                    f.write("f " + " ".join(str(i+1) for i in face) + "\n")

            messagebox.showinfo("Готово", "OBJ файл сохранён")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


def main():
    root = tk.Tk()
    PolyhedronViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
