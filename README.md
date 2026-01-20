# Ray Tracing Python – Projet pédagogique

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

## 📁 Structure du projet

```
RayTracing/
│── raytracing_helped.py     # Code principal
│── book_shapes.txt          # Description de la scène (sphères + lumières)
│── frame_00.ppm             # Images générées
│── frame_01.ppm
│── ...
│── animation.gif            # GIF final
│── README.md                # Documentation
```

---

## Description de la scène (`book_shapes.txt`)

La scène est décrite dans un fichier texte simple.

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

### Paramètres disponibles
| Paramètre | Description |
|---------|-------------|
| center | Position de la sphère |
| radius | Rayon |
| color | Couleur RGB |
| specular | Brillance spéculaire |
| reflective | Coefficient de réflexion |
| texture | Texture procédurale (checker) |

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
- `Plane`
- `Light`
- `Scene`

### Textures
- `CheckerTexture` : texture procédurale damier
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

Le format utilisé est **PPM**, simple et lisible.

---

## Génération d’une animation GIF

### Installation d’ImageMagick

```bash
sudo apt install imagemagick
```

---

### Rendu d'une seule image

```bash
python3 raytracing_2.py
```

---

### Rendu de plusieurs frames

```bash
python3 raytracing_2.py --animate
```
Cette commande créra 36 images .ppm pour créer l'animation.

```bash
python3 raytracing_2.py --animate --frames 10
```
Cette commande créra 10 images ppm pour créer l'animation. 
Le nombre de frame peut être ajuster en changeant ce nombre.

---

## 🎓 Conclusion

Ce projet démontre :
- Les principes fondamentaux du **ray tracing**
- La gestion de l’éclairage réaliste
- L’application de textures via UV mapping
- La génération d’animations à partir d’un moteur de rendu

Il constitue une base solide pour des extensions telles que :
- Textures image (PNG/JPG)
- Soft shadows
- Bump mapping
- Caméra mobile

---

✍️ *Projet académique – Ray Tracing en Python*