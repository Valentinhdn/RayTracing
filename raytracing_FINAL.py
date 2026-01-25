import math
import re
import argparse
import subprocess
import sys

INF = float('inf')
BACKGROUND_COLOR = (0, 0, 0)

CANVAS_WIDTH = 500
CANVAS_HEIGHT = 500
VIEWPORT_WIDTH = 2.0
VIEWPORT_HEIGHT = 2.0
VIEWPORT_DISTANCE = 1.0

class Vector:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other):
        return Vector(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def length(self):
        return math.sqrt(self.dot(self))
    
    def normalize(self):
        l = self.length()
        if l == 0:
            return Vector(0, 0, 0)
        return Vector(self.x / l, self.y / l, self.z / l)
    
    def __repr__(self):
        return f"Vector({self.x}, {self.y}, {self.z})"


class Sphere:
    def __init__(self, center, radius, color, specular, reflective=0.0, texture=None):
        self.center = center
        self.radius = radius
        self.color = color
        self.specular = specular
        self.reflective = reflective
        self.texture = texture

class Plane:
    def __init__(self, point, normal, color, specular=100, reflective=0.0, texture=None):
        self.point = point
        self.normal = normal.normalize()
        self.color = color
        self.specular = specular
        self.reflective = reflective
        self.texture = texture

class Triangle:
    def __init__(self, v0, v1, v2, color, specular=100, reflective=0.0, texture=None):
        self.v0 = v0
        self.v1 = v1
        self.v2 = v2
        self.color = color
        self.specular = specular
        self.reflective = reflective
        self.texture = texture
        self.normal = (v1 - v0).cross(v2 - v0).normalize()

class Light:
    def __init__(self, light_type, intensity, position=None, direction=None):
        self.type = light_type
        self.intensity = intensity
        self.position = position
        self.direction = direction

class Scene:
    def __init__(self, spheres, planes, lights, triangles=None):
        self.Spheres = spheres
        self.Planes = planes
        self.Lights = lights
        self.Triangles = triangles if triangles else []

class CheckerTexture:
    def __init__(self, color1, color2, scale=10):
        self.color1 = color1
        self.color2 = color2
        self.scale = scale

    def get_color(self, u, v):
        if int(u * self.scale) % 2 == int(v * self.scale) % 2:
            return self.color1
        return self.color2


def canvas_to_viewport(x, y):
    """Convert canvas coordinates to viewport coordinates"""
    vx = x * VIEWPORT_WIDTH / CANVAS_WIDTH
    vy = y * VIEWPORT_HEIGHT / CANVAS_HEIGHT
    vz = VIEWPORT_DISTANCE
    return Vector(vx, vy, vz)


def intersect_ray_sphere(O, D, sphere):
    """
    Calculate ray-sphere intersection.
    Returns tuple (t1, t2) of intersection parameters, or (INF, INF) if no intersection.
    O: Vector origin
    D: Vector direction
    sphere: Sphere object
    """
    r = sphere.radius
    CO = O - sphere.center
    
    a = D.dot(D)
    b = 2 * CO.dot(D)
    c = CO.dot(CO) - r * r
    
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return INF, INF
    
    sqrt_disc = math.sqrt(discriminant)
    t1 = (-b + sqrt_disc) / (2 * a)
    t2 = (-b - sqrt_disc) / (2 * a)
    
    return t1, t2

def intersect_ray_plane(O, D, plane):
    denom = plane.normal.dot(D)
    if abs(denom) < 1e-6:
        return INF

    t = (plane.point - O).dot(plane.normal) / denom
    if t > 0:
        return t
    return INF


def intersect_ray_triangle(O, D, triangle):
    EPSILON = 1e-6

    v0, v1, v2 = triangle.v0, triangle.v1, triangle.v2
    edge1 = v1 - v0
    edge2 = v2 - v0

    h = D.cross(edge2)
    a = edge1.dot(h)
    if -EPSILON < a < EPSILON:
        return INF

    f = 1.0 / a
    s = O - v0
    u = f * s.dot(h)
    if u < 0.0 or u > 1.0:
        return INF

    q = s.cross(edge1)
    v = f * D.dot(q)
    if v < 0.0 or u + v > 1.0:
        return INF

    t = f * edge2.dot(q)
    if t > EPSILON:
        return t

    return INF


def compute_lighting(P, N, V, s, scene, current_sphere=None):
    """
    Compute lighting at point P with normal N and view direction V.
    Based on Computer Graphics from Scratch by Gabriel Gambetta.
    P: Vector point
    N: Vector normal (unit vector)
    V: Vector view direction
    s: specular coefficient (-1 for no specular)
    scene: Scene object
    Returns: lighting intensity between 0 and infinity (typically clamped to [0, 1])
    """
    i = 0.0
    
    for light in scene.Lights:
        if light.type == "ambient":
            i += light.intensity
        else:
            if light.type == "point":
                L = light.position - P
                t_max = L.length()
            else:
                L = light.direction.normalize() * (-1)
                t_max = INF

            L_dir = L.normalize()
            
            blocked = False

            for sphere in scene.Spheres:
                if sphere is current_sphere:
                    continue
                t1, t2 = intersect_ray_sphere(P, L_dir, sphere)
                if 0.001 < t1 < t_max or 0.001 < t2 < t_max:
                    blocked = True
                    break

            if not blocked:
                for tri in scene.Triangles:
                    if tri is current_sphere:
                        continue
                    t = intersect_ray_triangle(P, L_dir, tri)
                    if 0.001 < t < t_max:
                        blocked = True
                        break

            if blocked:
                continue

            n_dot_l = N.dot(L_dir)
            if n_dot_l > 0:
                i += light.intensity * n_dot_l
            
            if light.type == "point":
                distance = L.length()
                attenuation = 1 / (1 + 0.1 * distance + 0.01 * distance * distance)
                i += light.intensity * n_dot_l * attenuation
            
            if s != -1 and s > 0:
                N_dot_L = N.dot(L_dir)
                if N_dot_L > 0:
                    R = (N * (2 * N_dot_L)) - L_dir
                    r_dot_v = R.dot(V)
                    if r_dot_v > 0:
                        i += light.intensity * pow(
                            r_dot_v / (R.length() * V.length()),
                            s
                        )
    
    return i


def reflect_ray(R, N):
    """Reflect incoming ray R around normal N"""
    return R - N * (2 * R.dot(N))


def trace_ray(O, D, t_min, t_max, scene, depth=3):
    """
    Trace a ray and return the color at the nearest intersection.
    Supports reflections up to `depth`.
    """
    closest_t = INF
    closest_object = None
    object_type = None

    for plane in scene.Planes:
        t = intersect_ray_plane(O, D, plane)
        if t_min <= t <= t_max and t < closest_t:
            closest_t = t
            closest_object = plane
            object_type = "plane"

    for sphere in scene.Spheres:
        t1, t2 = intersect_ray_sphere(O, D, sphere)

        if t_min <= t1 <= t_max and t1 < closest_t:
            closest_t = t1
            closest_object = sphere
            object_type = "sphere"

        if t_min <= t2 <= t_max and t2 < closest_t:
            closest_t = t2
            closest_object = sphere
            object_type = "sphere"
            
    for triangle in scene.Triangles:
        t = intersect_ray_triangle(O, D, triangle)
        if t_min <= t <= t_max and t < closest_t:
            closest_t = t
            closest_object = triangle
            object_type = "triangle"

    if closest_object is None:
        return BACKGROUND_COLOR

    P = O + (D * closest_t)
    V = D * (-1)

    if object_type == "sphere":
        N = (P - closest_object.center).normalize()
        base_color = closest_object.color
    elif object_type == "plane":
        N = closest_object.normal
        base_color = closest_object.color
    else:
        N = closest_object.normal
        base_color = closest_object.color

    if N.dot(D) > 0:
        N = N * -1

    lighting = compute_lighting(
        P, N, V,
        closest_object.specular,
        scene,
        closest_object
    )
    lighting = max(0, min(1, lighting))

    if closest_object.texture:
        u, v = sphere_uv(P, closest_object) if object_type == "sphere" else (0, 0)
        base_color = closest_object.texture.get_color(u, v)
    else:
        base_color = closest_object.color

    local_color = (
        int(base_color[0] * lighting),
        int(base_color[1] * lighting),
        int(base_color[2] * lighting),
    )

    reflective = closest_object.reflective

    if depth <= 0 or reflective <= 0:
        return local_color

    R_dir = reflect_ray(D, N).normalize()
    reflect_origin = P + N * 0.001
    reflected_color = trace_ray(reflect_origin, R_dir, 0.001, INF, scene, depth - 1)

    r = int(local_color[0] * (1 - reflective) + reflected_color[0] * reflective)
    g = int(local_color[1] * (1 - reflective) + reflected_color[1] * reflective)
    b = int(local_color[2] * (1 - reflective) + reflected_color[2] * reflective)
    return (r, g, b)


# Partiellement généré par ChatGPT
def parse_input_file(input_file):
    """Parse book_shapes.txt format"""
    spheres = []
    lights = []
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    sphere_blocks = re.findall(r'sphere\s*\{([^}]+)\}', content, re.DOTALL)
    
    for block in sphere_blocks:
        sphere_data = {}
        
        center_match = re.search(r'center\s*=\s*\(([^)]+)\)', block)
        if center_match:
            values = [float(x.strip()) for x in center_match.group(1).split(',')]
            sphere_data['center'] = Vector(values[0], values[1], values[2])
        
        radius_match = re.search(r'radius\s*=\s*([\d.]+)', block)
        if radius_match:
            sphere_data['radius'] = float(radius_match.group(1))
        
        color_match = re.search(r'color\s*=\s*\(([^)]+)\)', block)
        if color_match:
            values = [int(float(x.strip())) for x in color_match.group(1).split(',')]
            sphere_data['color'] = tuple(values)
        
        specular_match = re.search(r'specular\s*=\s*([\d.]+)', block)
        if specular_match:
            sphere_data['specular'] = float(specular_match.group(1))

        reflective_match = re.search(r'reflective\s*=\s*([\d.]+)', block)
        if reflective_match:
            sphere_data['reflective'] = float(reflective_match.group(1))

        texture_match = re.search(r'texture\s*=\s*(\w+)', block)
        if texture_match:
            if texture_match.group(1) == "checker":
                sphere_data['texture'] = CheckerTexture(
                    (255,255,255), 
                    (0,0,0), 
                    scale=10
                )
        
        if all(k in sphere_data for k in ['center', 'radius', 'color']):
            sphere = Sphere(
                sphere_data['center'],
                sphere_data['radius'],
                sphere_data['color'],
                sphere_data.get('specular', 100),
                sphere_data.get('reflective', 0.0),
                sphere_data.get('texture', None)
            )
            spheres.append(sphere)
    
    light_blocks = re.findall(r'light\s*\{([^}]+)\}', content, re.DOTALL)
    
    for block in light_blocks:
        light_data = {}
        
        type_match = re.search(r'type\s*=\s*(\w+)', block)
        if type_match:
            light_data['type'] = type_match.group(1)
        
        intensity_match = re.search(r'intensity\s*=\s*([\d.]+)', block)
        if intensity_match:
            light_data['intensity'] = float(intensity_match.group(1))
        
        position_match = re.search(r'position\s*=\s*\(([^)]+)\)', block)
        if position_match:
            values = [float(x.strip()) for x in position_match.group(1).split(',')]
            light_data['position'] = Vector(values[0], values[1], values[2])
        
        direction_match = re.search(r'direction\s*=\s*\(([^)]+)\)', block)
        if direction_match:
            values = [float(x.strip()) for x in direction_match.group(1).split(',')]
            light_data['direction'] = Vector(values[0], values[1], values[2])

        if 'type' in light_data and 'intensity' in light_data:
            light = Light(
                light_data['type'],
                light_data['intensity'],
                light_data.get('position'),
                light_data.get('direction')
            )
            lights.append(light)
    
    return spheres, lights

# Partiellement généré par ChatGPT
def parse_triangle_file(input_file):
    triangles = []
    lights = []

    with open(input_file, 'r') as f:
        content = f.read()

    tri_blocks = re.findall(r'triangle\s*\{([^}]+)\}', content, re.DOTALL)
    for block in tri_blocks:
        data = {}
        def vec(name):
            m = re.search(rf'{name}\s*=\s*\(([^)]+)\)', block)
            if not m:
                return None
            vals = [float(x.strip()) for x in m.group(1).split(',')]
            return Vector(vals[0], vals[1], vals[2])

        data["v0"] = vec("v0")
        data["v1"] = vec("v1")
        data["v2"] = vec("v2")

        color_match = re.search(r'color\s*=\s*\(([^)]+)\)', block)
        spec_match = re.search(r'specular\s*=\s*([\d.]+)', block)
        refl_match = re.search(r'reflective\s*=\s*([\d.]+)', block)

        if color_match:
            data["color"] = tuple(int(float(x.strip())) for x in color_match.group(1).split(','))

        if all(k in data for k in ["v0", "v1", "v2", "color"]):
            triangles.append(Triangle(
                data["v0"],
                data["v1"],
                data["v2"],
                data["color"],
                float(spec_match.group(1)) if spec_match else 100,
                float(refl_match.group(1)) if refl_match else 0.0,
                None
            ))

    light_blocks = re.findall(r'light\s*\{([^}]+)\}', content, re.DOTALL)
    for block in light_blocks:
        light_data = {}
        type_match = re.search(r'type\s*=\s*(\w+)', block)
        intensity_match = re.search(r'intensity\s*=\s*([\d.]+)', block)
        position_match = re.search(r'position\s*=\s*\(([^)]+)\)', block)
        direction_match = re.search(r'direction\s*=\s*\(([^)]+)\)', block)

        if type_match:
            light_data['type'] = type_match.group(1)
        if intensity_match:
            light_data['intensity'] = float(intensity_match.group(1))
        if position_match:
            vals = [float(x.strip()) for x in position_match.group(1).split(',')]
            light_data['position'] = Vector(*vals)
        if direction_match:
            vals = [float(x.strip()) for x in direction_match.group(1).split(',')]
            light_data['direction'] = Vector(*vals)

        if 'type' in light_data and 'intensity' in light_data:
            lights.append(Light(
                light_data['type'],
                light_data['intensity'],
                light_data.get('position'),
                light_data.get('direction')
            ))

    return triangles, lights


def sphere_uv(P, sphere):
    p = (P - sphere.center).normalize()

    u = 0.5 + math.atan2(p.z, p.x) / (2 * math.pi)
    v = 0.5 - math.asin(p.y) / math.pi

    return u, v


def create_scene():
    """Create scene with spheres and lights from book_shapes.txt"""
    spheres, lights = parse_input_file('book_shapes.txt')
    planes = [
        Plane(Vector(0, -2, 0), Vector(0, 1, 0), (200, 200, 200)),      # sol
        Plane(Vector(0, 0, 10), Vector(0, 0, -1), (180, 190, 200)),     # mur fond
        Plane(Vector(-5, 0, 0), Vector(1, 0, 0), (100, 50, 200)),       # mur gauche
        Plane(Vector(5, 0, 0), Vector(-1, 0, 0), (200, 0, 0)),          # mur droit
        Plane(Vector(0, 5, 0), Vector(0, -1, 0), (200, 200, 200))       # plafond
    ]
    
    return Scene(spheres, planes, lights)


def create_triangle_scene():
    triangles, lights = parse_triangle_file("triangle_scene.txt")
    spheres = []
    planes = [
        Plane(Vector(0, -2, 0), Vector(0, 1, 0), (200, 200, 200)),      # sol
        Plane(Vector(0, 0, 10), Vector(0, 0, -1), (180, 190, 200)),     # mur fond
        Plane(Vector(-5, 0, 0), Vector(1, 0, 0), (100, 50, 200)),       # mur gauche
        Plane(Vector(5, 0, 0), Vector(-1, 0, 0), (200, 0, 0)),          # mur droit
        Plane(Vector(0, 5, 0), Vector(0, -1, 0), (200, 200, 200))       # plafond
    ]

    return Scene(spheres, planes, lights, triangles=triangles)


def create_scene_moove():
    """Create scene with spheres and lights from book_shapes.txt"""
    spheres, lights = parse_input_file('shapes_move.txt')
    planes = [
        Plane(Vector(0, -2, 0), Vector(0, 1, 0), (200, 200, 200)),      # sol
        Plane(Vector(0, 0, 10), Vector(0, 0, -1), (180, 190, 200)),     # mur fond
        Plane(Vector(-5, 0, 0), Vector(1, 0, 0), (100, 50, 200)),       # mur gauche
        Plane(Vector(5, 0, 0), Vector(-1, 0, 0), (200, 0, 0)),          # mur droit
        Plane(Vector(0, 5, 0), Vector(0, -1, 0), (200, 200, 200))       # plafond
    ]
    
    return Scene(spheres, planes, lights)


def orbit_light(center, radius, angle_deg, height=2):
    angle = math.radians(angle_deg)
    return Vector(
        center.x + radius * math.cos(angle),
        height,
        center.z + radius * math.sin(angle)
    )


def animate_spheres(scene, initial_centers, frame, total_frames):
    angle_base = 360 * frame / total_frames

    for i, sphere in enumerate(scene.Spheres):
        base = initial_centers[i]
        radius = 1.5 + 0.5 * i 
        speed = 1.0 + 0.3 * i
        phase = angle_base * speed + i * 45
        angle = math.radians(phase)
        sphere.center = Vector(
            base.x + radius * math.cos(angle),
            base.y + math.sin(angle) * 0.8,
            base.z + radius * math.sin(angle) 
        )


def render_image(scene, width=CANVAS_WIDTH, height=CANVAS_HEIGHT):
    """Render scene to PPM image"""
    image = []
    
    for y in range(height // 2, -height // 2, -1):
        row = []
        for x in range(-width // 2, width // 2):
            D = canvas_to_viewport(x, y).normalize()
            O = Vector(0, 0, 0)
            color = trace_ray(O, D, 1.0, INF, scene, depth=3)
            row.append(color)
        image.append(row)
    
    return image


def save_ppm(image, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, filename='output.ppm'):
    """Save image to PPM file"""
    with open(filename, 'w') as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for row in image:
            for pixel in row:
                f.write(f"{pixel[0]} {pixel[1]} {pixel[2]} ")
            f.write("\n")
    print(f"Image saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Raytracer Python")
    parser.add_argument("--animate", action="store_true", help="Activer le mode animation")
    parser.add_argument("--frames", type=int, default=36, help="Nombre de frames pour l'animation (défaut: 36)")
    parser.add_argument("--scene", choices=["sphere", "triangle", "move"], default="sphere", help="Choisir la scène à afficher")
    
    args = parser.parse_args()

    print("Creating scene...")
    if args.scene == "triangle":
        scene = create_triangle_scene()
        print(f"Triangle scene created with {len(scene.Triangles)} triangle(s)")
    elif args.scene == "move":
        scene = create_scene_moove()
        print(f"Scene created with {len(scene.Spheres)} spheres and {len(scene.Lights)} lights")
    elif args.scene == "sphere":
        scene = create_scene()
        print(f"Scene created with {len(scene.Spheres)} spheres and {len(scene.Lights)} lights")

    if args.animate:
        nb_frames = args.frames
        radius = 5
        height = 3

        initial_centers = []
        if args.scene == "move":
            for sphere in scene.Spheres:
                initial_centers.append(Vector(sphere.center.x, sphere.center.y, sphere.center.z))
        
        print(f"Starting animation with {nb_frames} frames...")

        for i in range(nb_frames):
            angle = (360 / nb_frames) * i

            if len(scene.Lights) > 1:
                if args.scene == "move" and len(scene.Spheres) > 0:
                    animate_spheres(scene, initial_centers, i, nb_frames)
                if len(scene.Spheres) > 0:
                    center = scene.Spheres[0].center
                elif len(scene.Triangles) > 0:
                    cx = sum(t.v0.x + t.v1.x + t.v2.x for t in scene.Triangles) / (3 * len(scene.Triangles))
                    cy = sum(t.v0.y + t.v1.y + t.v2.y for t in scene.Triangles) / (3 * len(scene.Triangles))
                    cz = sum(t.v0.z + t.v1.z + t.v2.z for t in scene.Triangles) / (3 * len(scene.Triangles))
                    center = Vector(cx, cy, cz)
                else:
                    center = Vector(0, 0, 5)

                if args.scene != "move":
                    scene.Lights[1].position = orbit_light(
                    center,
                    radius=radius,
                    angle_deg=angle,
                    height=height
                ) 

            print(f"Rendering frame {i+1}/{nb_frames} (angle={angle:.1f})")
            image = render_image(scene)

            filename = f"frame_{i:02d}.ppm"
            save_ppm(image, filename=filename)
            
        print("Rendering complete. Generating GIF...")

        if sys.platform.startswith('linux'):
            command = "convert -delay 10 -loop 0 frame_*.ppm animation.gif"
        else:
            magick_path = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
            command = f'"{magick_path}" -delay 10 -loop 0 "frame_*.ppm" animation.gif'

        try:
            subprocess.run(command, shell=True, check=True)
            print("------------------------------------------------")
            print("SUCCESS: Animation saved as 'animation.gif'")
            print("------------------------------------------------")
            print("Cleaning up temporary .ppm files...")
            if sys.platform.startswith('linux'):
                subprocess.run("rm frame_*.ppm", shell=True)
            else:
                subprocess.run("del frame_*.ppm", shell=True)
            print("Cleanup frame_*.ppm complete.")
                
        except subprocess.CalledProcessError:
            print("ERROR: The 'convert' command failed.")
            print("Make sure ImageMagick is installed correctly.")
        except FileNotFoundError:
            print("ERROR: Command not found. Is ImageMagick installed?")

        
        if sys.platform.startswith('linux'):
            commandRun = "eog animation.gif"
        else:
            commandRun = "start animation.gif"
        print("Opening the GIF with eog...")
        try:
            print("GIF opened successfully.")
            subprocess.run(commandRun, shell=True, check=True)
        except subprocess.CalledProcessError:
            print("ERROR: Could not open the GIF with eog.")

    else:
        print("Rendering single static frame...")
        image = render_image(scene)
        save_ppm(image, filename='output.ppm')
        print("Single frame rendered.")

        print("Opening the image with eog...")

        if sys.platform.startswith('linux'):
            commandRun = "eog output.ppm"
        else:
            commandRun = "start output.ppm"
        
        try:
            print("Image opened successfully.")
            subprocess.run(commandRun, shell=True, check=True)
        except subprocess.CalledProcessError:
            print("ERROR: Could not open the image with eog.")

if __name__ == "__main__":
    main()

