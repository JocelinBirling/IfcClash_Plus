# Faces extrêmes : carte de hauteur rasterisée contre les fonctions existantes

Côté : **top**. Maquettes : Ifc2x3_Duplex_Architecture.ifc, Ifc2x3_Duplex_Mechanical.ifc. Éléments : 810 ; sous-ensemble où toutes les méthodes ont abouti : 810 (limite Python 20 s par appel). Carte : maille 0.01 m, de 64 à 1024 mailles par côté.

Généré par `scripts/benchmark_extreme_faces.py`.

## Vitesse (sous-ensemble commun)

| Méthode | Total | Moyenne / élément | Médiane | Max | Gain de cpp_raster |
|---|---|---|---|---|---|
| `py_brep_rays` | 517.62 s | 639.0 ms | 198.4 ms | 7.26 s | ×2 549 |
| `cpp_brep_rays` | 142.39 s | 175.8 ms | 70.0 ms | 1.53 s | ×701 |
| `py_mesh_shapely` | 18.86 s | 23.3 ms | 1.1 ms | 1.75 s | ×93 |
| `cpp_mesh_geos` | 7.13 s | 8.8 ms | 311 µs | 702.0 ms | ×35 |
| `cpp_sampled` | 209.3 ms | 258 µs | 48 µs | 5.5 ms | ×1.03 |
| `cpp_raster` | 203.1 ms | 251 µs | 98 µs | 4.1 ms | — |
| `cpp_raster_coarse` | 27.2 ms | 34 µs | 15 µs | 317 µs | ×0.13 |
| `cpp_auto` | 62.1 ms | 77 µs | 42 µs | 659 µs | ×0.31 |

Par taille de maillage (temps cumulés) :

| Triangles | Éléments | `py_brep_rays` | `cpp_brep_rays` | `py_mesh_shapely` | `cpp_mesh_geos` | `cpp_sampled` | `cpp_raster` | `cpp_raster_coarse` | `cpp_auto` |
|---|---|---|---|---|---|---|---|---|---|
| < 100 | 471 | 66.15 s | 23.53 s | 301.5 ms | 71.7 ms | 15.1 ms | 136.5 ms | 10.1 ms | 12.4 ms |
| 100 – 999 | 325 | 400.67 s | 115.80 s | 12.02 s | 4.75 s | 157.3 ms | 60.6 ms | 14.8 ms | 44.2 ms |
| ≥ 1 000 | 14 | 50.80 s | 3.07 s | 6.54 s | 2.30 s | 36.9 ms | 6.0 ms | 2.4 ms | 5.6 ms |

Seuil de `cpp_auto` (échantillonnage sous le seuil, carte au-delà), temps cumulés recalculés à partir des mesures `cpp_sampled` et `cpp_raster` :

| Seuil (triangles) | 0 (carte seule) | 50 | 100 | 150 | 200 | 300 | 500 | 1000 | ∞ (échantillonnage seul) |
|---|---|---|---|---|---|---|---|---|---|
| Total | 203.1 ms | 111.6 ms | 81.7 ms | 75.8 ms | 72.4 ms | 73.9 ms | 82.0 ms | 178.4 ms | 209.3 ms |

Meilleur choix possible élément par élément : 66.3 ms.

Aucun appel Python au-delà de la limite.


## Qualité (méthodes sur triangles, sous-ensemble commun)

| Méthode | Couverture moyenne | Couverture min | Éléments à couverture < 99 % | Manqué vs carte fine | En trop vs carte fine | Jaccard moyen vs carte fine |
|---|---|---|---|---|---|---|
| `py_mesh_shapely` | 0.7656 | 0.0000 | 299 | 344.797 m² (14.676 %) | 113.764 m² (4.842 %) | 0.7437 |
| `cpp_mesh_geos` | 0.7656 | 0.0000 | 299 | 344.797 m² (14.676 %) | 113.764 m² (4.842 %) | 0.7437 |
| `cpp_sampled` | 1.0000 | 0.9992 | 0 | 0.367 m² (0.016 %) | 0.002 m² (0.000 %) | 0.9753 |
| `cpp_raster` | 0.9999 | 0.9893 | 1 | 0.061 m² (0.003 %) | 2.934 m² (0.125 %) | 0.9284 |
| `cpp_raster_coarse` | 0.9984 | 0.7678 | 6 | 0.367 m² (0.016 %) | 8.148 m² (0.347 %) | 0.8120 |
| `cpp_auto` | 0.9999 | 0.9893 | 1 | 0.311 m² (0.013 %) | 0.578 m² (0.025 %) | 0.9577 |

Surface en plan vue selon la carte fine : 2349.3 m² (triangles cumulés).

## Éléments les plus lents (méthode d'Above, `py_brep_rays`)

| Élément | Triangles | py_brep_rays | cpp_brep_rays | cpp_sampled | cpp_raster |
|---|---|---|---|---|---|
| Ifc2x3_Duplex_Mechanical.ifc #85312 IfcFlowController | 4002 | 7.26 s | 308.3 ms | 5.0 ms | 674 µs |
| Ifc2x3_Duplex_Mechanical.ifc #85270 IfcFlowController | 4002 | 7.25 s | 279.7 ms | 4.9 ms | 480 µs |
| Ifc2x3_Duplex_Mechanical.ifc #67719 IfcFlowMovingDevice | 3805 | 6.99 s | 536.0 ms | 5.5 ms | 664 µs |
| Ifc2x3_Duplex_Mechanical.ifc #32595 IfcFlowMovingDevice | 3805 | 6.76 s | 516.8 ms | 5.5 ms | 655 µs |
| Ifc2x3_Duplex_Mechanical.ifc #84050 IfcFlowController | 4002 | 6.11 s | 242.0 ms | 5.2 ms | 479 µs |
| Ifc2x3_Duplex_Mechanical.ifc #84355 IfcFlowController | 4002 | 5.93 s | 245.8 ms | 5.1 ms | 688 µs |
| Ifc2x3_Duplex_Mechanical.ifc #115533 IfcFlowMovingDevice | 682 | 2.64 s | 1.53 s | 768 µs | 226 µs |
| Ifc2x3_Duplex_Mechanical.ifc #115421 IfcFlowMovingDevice | 682 | 2.62 s | 1.52 s | 781 µs | 225 µs |
| Ifc2x3_Duplex_Mechanical.ifc #99588 IfcFlowFitting | 740 | 2.61 s | 684.2 ms | 927 µs | 200 µs |
| Ifc2x3_Duplex_Mechanical.ifc #14598 IfcFlowFitting | 740 | 2.41 s | 665.8 ms | 938 µs | 263 µs |
