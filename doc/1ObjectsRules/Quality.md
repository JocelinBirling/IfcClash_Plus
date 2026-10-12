On peut vérifier si les objets sont de qualités.

Entrées : Source = tous objets ; paramètres : type de contrôle (watertight, self-intersection, faces inversées, aire min des faces).
Description : règle de qualité amont utilisant BRepCheck_Analyzer : le solide doit être fermé, non auto-intersectant, correctement orienté. Aucune règle du catalogue ne valide la géométrie elle-même.
Exemples : (1) Avant un lancement de clash, exclure les solides ouverts qui faussent les booléens OCC (source classique de faux négatifs). (2) Dans la cascade : les objets KO alimentent un BCF "qualité de maquette" adressé au maquettiste, pas au métier.




### Clash avec soi-même

### Clash avec ta propre bounding box

### Clash des géométrie dégénéré
Triangle aplatis
faces sans normes
Objetsà  volume nul
