# Synthèse des algorithmes de my_pgp

Le projet implémente cinq systèmes en Python, sans bibliothèque de chiffrement
externe. `src/my_pgp.py` sélectionne le système, lit l'entrée standard et écrit
le résultat. Les erreurs sont envoyées sur stderr avec un code de retour 84.

| Système | Principe | Clé | Fichier |
| --- | --- | --- | --- |
| XOR | Combinaison bit à bit avec une clé | Octets non vides | `src/xor.py` |
| AES | Chiffrement symétrique AES-128 | 16 octets | `src/aes.py` |
| RSA | Exponentiation modulaire asymétrique | Exposant et module | `src/rsa.py` |
| PGP-XOR | XOR pour le message, RSA pour la clé | Clé XOR et clé RSA | `src/pgp_xor.py` |
| PGP-AES | AES-128 pour le message, RSA pour la clé | Clé AES et clé RSA | `src/pgp_aes.py` |

## Conventions communes

- `-c` chiffre du texte ou des octets et produit de l'hexadécimal.
- `-d` lit du chiffré hexadécimal et produit les octets clairs.
- Deux chiffres hexadécimaux représentent un octet.
- `-b` traite un seul bloc, retire le LF final à l'entrée et ajoute un LF
  au texte déchiffré. Un retour à la ligne interne est refusé.
- Sans `-b`, XOR et AES traitent plusieurs blocs, conservent les retours à la
  ligne du clair et complètent le dernier bloc avec des zéros. Les zéros restent
  au déchiffrement : la longueur originale n'est pas transmise.
- RSA traite toujours une seule ligne, avec ou sans `-b`.

Le « mode flux » du programme désigne le traitement de plusieurs blocs ; AES
reste un chiffrement par blocs.

## XOR

Pour chaque bit, XOR vaut 1 si les deux bits diffèrent, sinon 0. L'opération
est réversible : `(message XOR clé) XOR clé = message`.

1. Découper le message en blocs de la longueur de la clé.
2. Compléter le dernier bloc avec des zéros si nécessaire.
3. Inverser l'ordre des octets du bloc, selon la convention du projet.
4. Appliquer XOR entre chaque octet et l'octet correspondant de la clé.

Au déchiffrement, appliquer XOR puis inverser les octets du bloc. En mode
bloc, le message doit avoir exactement la taille de la clé ; le chiffré doit
toujours contenir des blocs complets.

## AES-128

AES utilise une clé de 128 bits et des blocs de 128 bits, soit 16 octets.
Chaque bloc est organisé en une matrice de 4 × 4 octets, remplie par colonnes.
L'expansion de clé produit onze clés de tour.

Le chiffrement commence par **AddRoundKey**, un XOR avec la première clé.
Il applique ensuite dix tours :

1. **SubBytes** : remplacer chaque octet avec la table S-box.
2. **ShiftRows** : décaler circulairement les lignes de la matrice.
3. **MixColumns** : mélanger les colonnes par des calculs dans GF(2⁸).
4. **AddRoundKey** : appliquer XOR avec la clé du tour.

Le dixième tour omet MixColumns. La multiplication dans GF(2⁸) utilise le
polynôme `0x11b`. Le déchiffrement applique les transformations inverses et les
clés de tour dans l'ordre inverse.

À l'interface, la clé et le chiffré sont convertis en little-endian par mots
de quatre octets : chaque groupe de quatre octets est inversé. Le clair garde
son ordre. Chaque bloc est chiffré indépendamment, comme en ECB, sans IV.
AES-192 et AES-256 sont aussi disponibles avec le système `aes` (12 et 14 tours) ;
PGP-AES reste limité à AES-128.

## RSA

RSA utilise une clé publique pour chiffrer et une clé privée pour déchiffrer.
Le programme reçoit deux nombres premiers distincts `p` et `q` en hexadécimal
little-endian ; il suppose leur primalité sans la tester.

La génération (`rsa -g P Q`) calcule :

1. `n = p × q`, le module.
2. `λ(n) = ppcm(p − 1, q − 1)`, la fonction de Carmichael.
3. `e`, le plus grand exposant admissible parmi `65537, 257, 17, 5, 3`,
   inférieur à `λ(n)` et premier avec `λ(n)`.
4. `d = e⁻¹ mod λ(n)`, donc `e × d ≡ 1 mod λ(n)`.

La clé publique est `(e, n)`, la clé privée `(d, n)`. Leur format CLI est
`exposant-module`, avec chaque entier encodé en little-endian.

Le message est interprété comme un entier little-endian `m`, avec `m < n` :

```python
c = pow(m, e, n)  # Chiffrement : m puissance e modulo n.
m = pow(c, d, n)  # Déchiffrement : c puissance d modulo n.
```

La fonction Python `pow` à trois arguments réalise l'exponentiation modulaire
sans construire la puissance entière. RSA renvoie le nombre sur le minimum
d'octets nécessaire : les octets nuls terminaux du clair ne sont pas conservés.
Cette version n'utilise pas de padding RSA.

## PGP-XOR et PGP-AES

Ces systèmes combinent un chiffrement symétrique du message et RSA pour
transporter la clé symétrique. La clé est fournie par l'utilisateur.

Au chiffrement, la commande reçoit `clé_symétrique:clé_RSA_publique` :

1. Chiffrer la clé symétrique avec RSA.
2. Chiffrer le message avec XOR ou AES-128.
3. Afficher la clé chiffrée en hexadécimal sur la première ligne, puis le
   message chiffré sur la deuxième.

Au déchiffrement, la commande reçoit `clé_chiffrée:clé_RSA_privée`, avec le
message chiffré seul sur l'entrée standard :

1. Déchiffrer la clé avec RSA.
2. Restaurer sa longueur lorsque celle-ci est connue.
3. Déchiffrer le message avec la clé récupérée.

**PGP-XOR** accepte une clé non vide de longueur variable. En bloc, la taille
du message permet de restaurer ses zéros terminaux. En flux, cette longueur
n'est pas transmise : une clé terminant par zéro n'est pas restituée fidèlement.

**PGP-AES** exige une clé de 16 octets au chiffrement. Au déchiffrement, la clé
RSA récupérée est complétée à droite avec des zéros jusqu'à 16 octets, en bloc
comme en flux. Une clé récupérée de plus de 16 octets est refusée. Le module RSA
doit être supérieur à la valeur entière de la clé AES.

## Limites de cette implémentation

Ces constructions sont pédagogiques : XOR répète sa clé, AES chiffre les blocs
indépendamment et RSA est sans padding. Les formats hybrides ne comportent ni
signature, ni authentification, ni vérification d'intégrité. Ils ne constituent
pas une implémentation complète du format OpenPGP.

## Vérification

`make tests_run` exécute les tests de l'interface, les vecteurs XOR, AES et RSA,
ainsi que les tests des deux systèmes hybrides. Les tests PGP-AES vérifient sa
composition avec RSA et AES, les aller-retours en bloc et en flux, la restauration
des clés contenant des zéros terminaux et les entrées invalides.
