# Description

Cette règle doit permettre de déterminer si la vue est libre entre deux objets. 
On doit pouvoir définir un nombre de rayon qui vont partir de l'objet A, ou de l'objet B.

De A vers B ou de B vers A, c'est pareille pour le résultat. Mais cela peut être plus facile pour multiplier les cas de figure.

10 de chaque côté, on est sûr de pas avoir loupé d'endroit spécifique.

Le nombre de touche doit se faire en pourcentage, tolerance=10%, implique qu'au moins 10% des tirs émis touche la cible.

On doit également faire un filtre sur les faces. On va lancer des rayons que depuis les faces qui sont orientés vers la cible.
Si les faces sont grandes, on devrait en envoyer plusieurs par face.

En ce qui concerne la direction du rayon, cela n'est pas clair.

On doit également pouvoir renseigner une distance maximum du rayon.


# Property

Context Objects: A list of object that will act as wall against the ray produced. If the ray hit a context object, we can say that there is no direct view.

View :
Partial View
Total View


# Result


# Example
This can check if a camera can see an object. It's an easy check if we have no information about the field of view of the camera.
