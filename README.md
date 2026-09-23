# my_pgp — première étape

Implémentation en Python 3, sans dépendance externe : interface en ligne de
commande, aide `-h`, XOR en modes bloc et flux, erreurs sur stderr avec code 84.
AES, RSA et PGP restent à implémenter ; leur utilisation renvoie une erreur explicite.

```sh
make
./my_pgp -h
printf 'You know nothing, Jon Snow\n' | ./my_pgp xor -c -b 576861742069732064656164206d6179206e6576657220646965
# 20070f2700071c6a4449060a490515164e4e12190b190011063c
printf '20070f2700071c6a4449060a490515164e4e12190b190011063c\n' | ./my_pgp xor -d -b 576861742069732064656164206d6179206e6576657220646965
# You know nothing, Jon Snow
make tests_run
```

Organisation du code :

- `src/my_pgp.py` : arguments, aide, entrées/sorties et sélection du système.
- `src/xor.py` : fonctions `encrypt` et `decrypt` pour XOR, implémentées.
- `src/aes.py` : fonctions `encrypt` et `decrypt` pour AES, à compléter.
- `src/rsa.py` : fonctions `encrypt`, `decrypt` et `generate_keys`, à compléter.
- `src/pgp_xor.py` : fonctions `encrypt` et `decrypt` pour PGP-XOR, à compléter.
- `src/pgp_aes.py` : fonctions `encrypt` et `decrypt` pour PGP-AES, à compléter.

`make` crée le lanceur `my_pgp`, qui exécute `src/my_pgp.py`.
Conserver le dossier `src` à côté du lanceur.
Les règles `clean`, `fclean` et `re` sont disponibles.

Chaque bloc du message est inversé pour obtenir sa représentation numérique
little-endian, puis combiné avec les octets de la clé par XOR. Le déchiffrement
fait l'opération inverse. Cela reproduit l'exemple du sujet.

En mode bloc (`-b`), le LF final est ignoré à l'entrée et le texte déchiffré est
suivi d'un LF, comme dans l'exemple. Le message doit avoir la taille de la clé.
En mode flux, les retours à la ligne du texte sont conservés et le dernier bloc
est complété avec des octets nuls. Ces octets sont conservés au déchiffrement :
sans longueur d'origine, on ne peut pas les distinguer des données réelles.
