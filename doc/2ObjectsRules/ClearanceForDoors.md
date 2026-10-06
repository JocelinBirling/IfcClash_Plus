Je veux faire une règle spécifique pour assurer que rien n'est devant les portes.
On va assurer les méthodes classiques pour récupérer les informations sur le dévant dérières.

Le type de porte (IfcDoorType) — l'attribut OperationType décrit le mécanisme : SingleSwingLeft, SingleSwingRight, DoubleDoorSingleSwing, SlidingToLeft, etc. L'attribut ParameterTakesPrecedence indique si ces paramètres priment sur la géométrie. C'est le "côté" (gauche/droite) qui y est défini.

La géométrie (mise en avant principale) — le sens d'ouverture est surtout exprimé par la représentation de la forme (IfcProductDefinitionShape) :
Le panneau de porte (IfcDoorPanelProperties ou directement dans la géométrie) est placé en position ouverte ou fermée selon la méthode de construction (SweptSolid, Brep...) ;
Une représentation additionnelle de type Curve2D (souvent un arc de cercle en plan) matérialise le balayage du vantail (le "quart de cercle" d'ouverture typique des plans 2D). La direction de cet arc et la position de la charnière indiquent le sens d'ouverture.

Le placement local (IfcLocalPlacement) — l'axe du IfcPlacement de la porte donne son orientation dans le mur ; combiné au type d'opération (gauche/droite), on en déduit le sens complet (vers l'intérieur/extérieur, charnière à droite/gauche).

La convention "vue depuis quel côté" pour gauche/droite est définie par la règle IsLeft/IsRight dans la spécification IfcDoorType.OperationType.



On proposant plusieurs méthodes, on assuera qu'au moins une des méthodes fonctionne.