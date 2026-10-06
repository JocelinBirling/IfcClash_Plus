# Description

This rule check if the face of an object is free.

Should we add a geometrie to test.


L'idée est de descendre au niveau des faces afin d'effectuer des tests.
Faire des intersections au niveau des faces ?
Faire des clearance au niveau des faces d'un objets ?



Comment sélectionner les faces ?
    - Par Surface
    - Par largueur ou longueur de la face
    - Par orientation
    - Face Intérieure ou extérieure ?
    - Matériau de chaque couche
    -Is Top Or Bottom Surface
    -Is Side Surface

On pourrait avoir un ensemble de caractéristique pour avoir une sélection précise ces faces en question.



Les types de clash à imaginer

Face Intersect Face 
Face Intersect Object
Face Clearance Face
Face Clearance Object

Face OBB Face
Face OBB Object

Face Orient Face
Face Orient Object




Au sein d'un même objet, on pourrait vérifier. Il faut donc pouvoir filtrer les faces au sein d'un même objets.

L'espace de passage d'une porte
La hauteur d'une surface vitrée


Il faudrait refaire les exceptions mais pour les règles de face.
Je pourrais trouver les deux faces haute de la chambranle d'une porte et vérifier que les deux faces qui s'opposes sont bien à une distance de 0.90 minimum.



# Property

Max Surface
Min Surface
Direction:
- Normals
- Fixed value

Distance: In meter, the length it need to check for intersection.

# Result


# Example

