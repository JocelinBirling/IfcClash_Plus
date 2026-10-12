Stair Check (conformité géométrique d'escalier)
Entrées : Source = escaliers (IfcStair + marches) ; paramètres : hauteur de marche min/max, giron min/max, régularité, largeur min, hauteur de garde-corps.
Description : reconstruit la ligne de foulée depuis la géométrie (détection des marches par tranches d'altitude), mesure pas-à-pas. Règle complexe car elle décompose un objet unique en sous-objets fonctionnels.
Exemples : (1) ERP : hauteur de marche 16-18 cm, giron ≥ 24 cm, toutes les marches identiques à 5 mm. (2) La largeur de la volée entre mains courantes doit rester ≥ 1,40 m. (3) En Select : sortir les escaliers non conformes pour reprise archi.

