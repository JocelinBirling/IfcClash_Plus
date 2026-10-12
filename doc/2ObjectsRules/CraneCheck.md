Données d'entrées : Source = éléments à gruter, poids lu dans une propriété (chaîne de repli ordonnée, ex. Qto_Weight → Pset dédié) ; Target = grues (objets positionnés dans la maquette) ; paramètres : points de mesure (axe de la grue = centroïde OBB ou point désigné ; élément = centroïde ou point d'accroche), table des paliers = liste de segments [Lmin, Lmax, C] (capacité C en t ou kg, constante par palier ou interpolée linéairement entre les bornes si deux capacités sont fournies), domaine de validité [portée min, portée max] de la grue, marge de sécurité (% appliqué à C), unité du poids (t, kg, kN). Règle asymétrique. État : à définir (proposition, non implémentée).
Description : règle mesurée à deux objets. Pour chaque paire (élément, grue), calcule la portée L = distance horizontale entre l'axe de la grue et le point de mesure de l'élément, localise le palier de l'abaque contenant L, et compare le poids de l'élément à la capacité C(L) de ce palier, diminuée de la marge de sécurité. Produit le taux de charge = poids / C(L) en scalaire pour la criticité (95 % ≠ 140 %) et les Must. Quatre verdicts par paire : conforme (poids ≤ C × marge), dépassement (poids > C, BCF « découpage ou renfort de grue »), hors domaine (L au-delà de la portée max de la grue — jamais extrapolé, verdict distinct plus grave), non évaluable (poids absent de l'objet — BCF qualité, jamais un faux négatif). Un élément n'est déclaré non grutable que si aucune paire n'est conforme : regroupement des résultats par source + have_no_result. Multi-grues : croisement naturel Source × Target, ou restriction par zone d'affectation (propriété IDS).
Algorithme : pré-filtre spatial par distance OBB (élimine les paires hors de la portée max + marge) ; pour chaque paire : L = distance 2D entre les projections au sol des points de mesure ; recherche du palier contenant L — à une frontière exacte entre deux paliers, le palier le plus restrictif est retenu (règle prudente, cohérente avec la plaque constructeur qui donne toujours la capacité du palier supérieur dès qu'on dépasse la portée) ; C(L) = capacité du palier (ou interpolation linéaire intra-palier si la table fournit deux valeurs) ; lecture du poids avec chaîne de repli (absent → « non évaluable ») ; normalisation des unités (SI en interne) ; taux de charge = poids / C(L) ; comparaison au seuil C(L) × marge ; sortie de la paire avec L, palier retenu, C, poids et taux de charge.
Exemples : (1) Grue à tour, marge 80 %, abaque saisi par paliers :

  
    
      Palier
      Portée (m)
      Capacité (t)
    
  
  
    
      1
      5 – 10
      8,0
    
    
      2
      10 – 15
      6,5
    
    
      3
      15 – 20
      5,0
    
    
      4
      20 – 25
      3,8
    
    
      5
      25 – 30
      2,8
    
    
      6
      30 – 35
      2,2
    
    
      7
      35 – 40
      1,8
    
  




    Une prédalle de 3,5 t posée à 22 m de l'axe : palier 4, C = 3,8 t → conforme exige poids ≤ 3,04 t → dépassement, taux de charge 92 % (arbitrage : renfort de grue mobile). Un bloc-valet de 1,6 t à 38 m : palier 7, C = 1,8 t, seuil 1,44 t → conforme. Un casse-charge de 2 t à 42 m : hors domaine (portée max 40 m) — BCF spécifique « hors portée », quelle que soit la capacité résiduelle apparente. (2) Vérification Must par grue : le taux de charge maximal, regroupé par grue, doit rester < 100 % ; un regroupement par étage identifie les zones où les dépassements se concentrent (déplacer la grue d'un mètre change plusieurs verdicts à la fois). (3) En règle d'activation : le dossier « phasage de grutage » ne s'active que si cette règle have_no_result.
Trois remarques pour l'implémentation :
Le format « paliers » et le polynôme coexistent dans le même moteur : la table de segments est juste un deuxième format de loi pour le Law Check. Beaucoup d'utilisateurs auront la plaque constructeur sous les yeux — recopier 7 lignes de paliers est plus sûr que régresser un polynôme ; l'interpolation linéaire optionnelle intra-palier couvre les abaques donnés en points (elle se désactive en fournissant la même capacité aux deux bornes).
La règle prudente aux frontières mérite d'être écrite noir sur blanc dans la fiche : c'est le genre de choix silencieux qui différencie deux outils de contrôle — exactement l'objectif de standardisation de ton projet.
Cohérence avec le reste du catalogue : portée = distance horizontale point-point (centroïdes projetés au sol), pas une clearance peau-peau — même famille de primitives que le point de mesure paramétrable évoqué pour Clearance Axis To Axis.

