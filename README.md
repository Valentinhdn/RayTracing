# Ray Tracing Python – Projet Outils mathématiques pour la modélisation

## 📌 Description générale

Ce projet est une implémentation **complète d’un moteur de ray tracing en Python**, inspirée de l’ouvrage *Computer Graphics from Scratch* (Gabriel Gambetta).

Le moteur permet de :
- Rendre une scène 3D composée de **sphères et de plans**
- Gérer **plusieurs types de lumières** (ambiante, ponctuelle, directionnelle)
- Calculer l’**ombrage diffus et spéculaire (Phong)**
- Gérer les **ombres**
- Implémenter des **réflexions récursives**
- Appliquer des **textures procédurales (damier)** via un mapping UV sphérique
- Générer des images **PPM**
- Produire une **animation GIF** à partir de plusieurs frames

---

## ⚠️ Compatibilité système

Le code à été conçu à l'origine pour fonctionner sur **Linux**. 
Nous avons donc ajouter un contrôle du système d'exploitation pour exécuter les commandes appropriées en fonction du système *Linux* ou *Windows*. 

Si vous êtes sur **Windows**, il faut que le chemin d'accès soit : 
```text
C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe
```
Si ce n'est pas le cas, alors il faut changer le chemin d'accès dans la fonction `main()` du fichier `raytracing_FINAL.py`. 

---

## 📁 Structure du projet

```
RayTracing/
│── raytracing_FINAL.py     # Code principal
│── book_shapes.txt         # Scène : 4 sphères + 3 lumières
|── shapes_move.txt         # Scène : 3 sphères + 3 lumières
|── triangle_scene.txt      # Scène : 1 triangle + 2 lumières
│── output.ppm              # Image unique
│── animation.gif           # GIF final
│── README.md               # Documentation
```

---

## Description des scènes (`book_shapes.txt`, `shapes_move.txt`, `triangle_scene.txt`)

Les scènes sont décrites dans des fichier texte.

### Exemple de sphère
```txt
sphere {
    center = (0, -1, 3)
    radius = 1
    color = (255, 0, 0)
    specular = 500
    reflective = 0.3
    texture = checker
}
```

### Exemple de triangle 
```txt
triangle {
    v0 = (-1, -1, 4)
    v1 = (1, -1, 4)
    v2 = (0, 1, 4)
    color = (255, 200, 50)
    specular = 300
    reflective = 0.4
}
```

### Paramètres disponibles
| Paramètre | Description |
|---------|-------------|
| center | Position de la sphère |
| radius | Rayon |
| color | Couleur RGB |
| specular | Brillance spéculaire |
| reflective | Coefficient de réflexion |
| texture | Texture procédurale (checker) |
| v0, V1, V2 | Sommets du triangle |

---

## 💡 Types de lumières

### Lumière ambiante
```txt
light {
    type = ambient
    intensity = 0.2
}
```

### Lumière ponctuelle
```txt
light {
    type = point
    intensity = 0.6
    position = (2, 1, 0)
}
```

### Lumière directionnelle
```txt
light {
    type = directional
    intensity = 0.2
    direction = (1, 4, 4)
}
```

---

## Architecture du code

### Classes mathématiques
- `Vector` : opérations vectorielles (addition, produit scalaire, normalisation…)

### Objets de la scène
- `Sphere`
- `Triangle`
- `Plane`
- `Light`
- `Scene`

### Textures
- `CheckerTexture` : texture damier
- Mapping UV sphérique via la fonction `sphere_uv()`

---

## Modèle d’illumination

Le modèle utilisé est **Phong**, incluant :
- Lumière ambiante
- Diffuse (Lambert)
- Spéculaire
- Atténuation avec la distance (lumière ponctuelle)

Fonction principale :
```python
compute_lighting(P, N, V, specular, scene, current_object)
trace_ray(O, D, t_min, t_max, scene, depth=3)

```

---

## 🌑 Ombres

Les ombres sont calculées par **rayons d’ombre** :
- Un rayon est lancé du point d’intersection vers la lumière
- Si un objet bloque ce rayon → pas d’éclairage direct

---

## Réflexions

Les réflexions sont gérées récursivement dans `trace_ray()` :
- Profondeur maximale configurable
- Mélange entre couleur locale et couleur réfléchie

---

## Génération des images PPM

Chaque frame est générée avec :
```python
render_image(scene)
save_ppm(image, filename)
```

Le format utilisé est **PPM**.

---

## Génération d’une animation GIF

### Installation d’ImageMagick

Sur **Linux** :
```bash
sudo apt install imagemagick
```
Sur **Windows** :
```bash
winget install ImageMagick.ImageMagick
```

### Rendu d'une seule image

```bash
python3 raytracing_FINAL.py
```

### Rendu de plusieurs frames

```bash
python3 raytracing_FINAL.py --animate
```
Cette commande créra 36 images .ppm pour créer l'animation GIF.

```bash
python3 raytracing_FINAL.py --animate --frames 10
```
Cette commande créra 10 images ppm pour créer l'animation GIF. 
Le nombre de frame peut être ajuster en changeant ce nombre.

### Choix de la scène

```bash
python3 raytracing_FINAL.py --scene triangle
```
Cette commande permet de selectionné la scène à afficher (ici, scèce triangle).

| Valeur   | Fichier utilisé    |
| -------- | ------------------ |
| triangle | triangle_scene.txt |
| sphere   | book_shapes.txt    |
| move     | shapes_move.txt    |

---

## Paramètres disponibles

| Paramètre     | Description   |
| ------------- | ------------- |
| --animate     | Pour géner un GIF et non un ppm |
| --frames X    | Nombres d'images pour le GIF (défaut : 36) |
| --scene [nom] | Choisir la scène (triangle, sphere, move) |

---

## Commandes système

La fonction `main()` utilise des commandes pour automatiser la génération et l'ouverture des images. 

Les commandes ont été conçues pour fonctionner sur **Linux** : 
```python
command = "convert -delay 10 -loop 0 frame_*.ppm animation.gif"
```
```python
commandRun = "eog animation.gif"
commandRun = "eog output.ppm"
```
```python
subprocess.run("rm frame_*.ppm", shell=True)
```

Sur **Windows**, ces commandes ont été remplacées par : 
```python
command = "magick -delay 10 -loop 0 frame_*.ppm animation.gif"
```
```python
commandRun = "start animation.gif"
commandRun = "start output.ppm"
```
```python
subprocess.run("del frame_*.ppm", shell=True)
```

---

## 🎓 Conclusion

Ce projet démontre :
- Les principes fondamentaux du **ray tracing**
- La gestion de l’éclairage réaliste
- L’application de textures via UV mapping
- La génération d’animations à partir d’un moteur de rendu

Il constitue une base solide pour des extensions telles que :
- Textures image (PNG/JPG)
- Ombre douce (Soft shadows)
- Bump mapping
- Caméra mobile
- Mouvement et accélération

---

✍️ ***Valentin HODONOU & Clément PACAULT***