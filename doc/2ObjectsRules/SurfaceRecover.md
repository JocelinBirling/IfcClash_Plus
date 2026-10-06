# Description

This rule check that the surface of two objects cover each other by max and min value.

This common


It could be done from top to bottom, but has well from side to side.

Usage : détecter les objets posés les uns sur les autres mais mal juxtaposés (appui partiel d'une poutre sur un mur : contact réel mais surface d'appui insuffisante).
Test : pour les paires en contact (distance ≈ 0), calculer l'aire de la zone de contact effectif (triangles quasi coplanaires à distance < ε), et la rapporter à la section d'appui attendue.
Résultat : contact_area + ratio.
Difficulté : moyenne à élevée. Très métier mais peu standardisé ; le seuil ε et la notion de « surface attendue » se paramètrent.

# Property

direction = direction to consider the 
min_covering = float or string float, absolute value, string relative value of source
max_covering = float or string float, absolute value, string relative value of source 
Value can be 10 for m² or 10%, 


# Result


# Example

