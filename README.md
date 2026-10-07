# my_pgp — première étape

Implémentation en Python 3, sans dépendance externe : interface en ligne de
commande, aide `-h`, XOR et AES-128 en modes bloc et flux, RSA et PGP-XOR, erreurs sur stderr avec code 84.
PGP-AES reste à implémenter ; son utilisation renvoie une erreur explicite.

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
- `src/aes.py` : fonctions `encrypt` et `decrypt` pour AES-128, implémentées.
- `src/rsa.py` : fonctions `encrypt`, `decrypt` et `generate_keys`, implémentées.
- `src/pgp_xor.py` : combinaison RSA et XOR, implémentée.
- `src/pgp_aes.py` : fonctions `encrypt` et `decrypt` pour PGP-AES, à compléter.

`make` crée le lanceur `my_pgp`, qui exécute `src/my_pgp.py`.
Conserver le dossier `src` à côté du lanceur.
Les règles `clean`, `fclean` et `re` sont disponibles.

Pour XOR, chaque bloc du message est inversé pour obtenir sa représentation numérique
little-endian, puis combiné avec les octets de la clé par XOR. Le déchiffrement
fait l'opération inverse. Cela reproduit l'exemple du sujet.

En mode bloc (`-b`), le LF final est ignoré à l'entrée et le texte déchiffré est
suivi d'un LF, comme dans l'exemple. Le message doit avoir la taille de la clé.
En mode flux, les retours à la ligne du texte sont conservés et le dernier bloc
est complété avec des octets nuls. Ces octets sont conservés au déchiffrement :
sans longueur d'origine, on ne peut pas les distinguer des données réelles.

## AES-128

AES est implémenté en Python : expansion de clé, SubBytes, ShiftRows,
MixColumns, AddRoundKey et transformations inverses. La matrice est remplie
colonne par colonne. Le cœur suit FIPS 197 :
https://csrc.nist.gov/pubs/fips/197/final

La clé doit contenir exactement 32 chiffres hexadécimaux (16 octets).
Pour reproduire l'exemple du sujet, la clé et le chiffré sont convertis en
little-endian **par mots de 4 octets** ; le message clair garde son ordre.
Cette convention est vérifiée séparément des vecteurs AES standard.

```sh
printf 'All men must die\n' | ./my_pgp aes -c -b 57696e74657220697320636f6d696e67
# 744ce22c385958348f0df26eceb62eef
printf '744ce22c385958348f0df26eceb62eef\n' | ./my_pgp aes -d -b 57696e74657220697320636f6d696e67
# All men must die
```

En bloc, le texte doit faire exactement 16 octets après retrait du LF final.
En flux, chaque bloc de 16 octets est chiffré indépendamment ; le dernier est
complété avec des zéros, conservés au déchiffrement. AES-192 et AES-256 ne sont
pas encore implémentés.

## RSA

Génération avec λ(n) = ppcm(p − 1, q − 1), le plus grand premier de Fermat
admissible parmi 65537, 257, 17, 5 et 3, puis d = e⁻¹ mod λ(n).
Les premiers sont supposés premiers, comme autorisé par le sujet.
Les clés ont le format `exposant-module`, chaque nombre étant en little-endian.

```sh
./my_pgp rsa -g d3 e3
# public key: 0101-19bb
# private key: 9d5b-19bb
printf 'WF\n' | ./my_pgp rsa -c 0101-19bb
# 8f84
printf '8f84\n' | ./my_pgp rsa -d 9d5b-19bb
# WF
```

RSA traite une seule ligne avec ou sans `-b`, ignore le LF final à l'entrée
et ajoute un LF à la sortie. La valeur little-endian du message doit être
strictement inférieure au module. Cette implémentation suit le RSA sans padding
du sujet ; la longueur d'origine et les octets nuls terminaux ne sont pas conservés.

## PGP-XOR

La clé est au format `clé_XOR:clé_RSA`. Le chiffrement affiche la clé XOR
chiffrée par RSA, puis le message chiffré par XOR, sur deux lignes.
Au déchiffrement, passer la première ligne avant `:` avec la clé RSA privée,
et uniquement la deuxième ligne sur l'entrée standard.

```sh
printf 'AB\n' | ./my_pgp pgp-xor -c -b 5746:0101-19bb
# 8f84
# 1507
printf '1507\n' | ./my_pgp pgp-xor -d -b 8f84:9d5b-19bb
# AB
```

Les modes bloc et flux suivent les conventions XOR. En mode bloc, la taille du
chiffré permet de restaurer les octets nuls terminaux de la clé récupérée par RSA.
En flux, la longueur de clé n'est pas transmise : utiliser une clé XOR sans octet
nul terminal, car RSA renvoie une représentation minimale du nombre.

## Commandes de test

Les commandes suivantes couvrent les systèmes, les modes bloc (`-b`) et flux,
ainsi que les cas d'erreur. Elles sont à lancer depuis la racine du projet.

### Compilation et tests automatisés

```sh
# Construire le lanceur
make

# Afficher l'aide
./my_pgp -h

# Exécuter toute la suite de tests unittest
make tests_run

# Nettoyer les fichiers temporaires Python
make clean

# Supprimer aussi le lanceur
make fclean

# Recréer complètement le lanceur
make re
```

### XOR

```sh
# Flux : chiffrement d'un message de longueur quelconque
printf 'ABC' | ./my_pgp xor -c 0102
# 43430141

# Flux : déchiffrement (le zéro de remplissage est conservé)
printf '43430141\n' | ./my_pgp xor -d 0102
# ABC<octet NUL>

# Bloc : chiffrement (la longueur du message doit être celle de la clé)
printf 'You know nothing, Jon Snow\n' |
  ./my_pgp xor -c -b 576861742069732064656164206d6179206e6576657220646965
# 20070f2700071c6a4449060a490515164e4e12190b190011063c

# Bloc : déchiffrement
printf '20070f2700071c6a4449060a490515164e4e12190b190011063c\n' |
  ./my_pgp xor -d -b 576861742069732064656164206d6179206e6576657220646965
# You know nothing, Jon Snow

# Flux binaire (les 256 octets sont chiffrés puis déchiffrés)
python3 -c 'import sys; sys.stdout.buffer.write(bytes(range(256)))' |
  ./my_pgp xor -c aabbcc > /tmp/xor.hex
./my_pgp xor -d aabbcc < /tmp/xor.hex > /tmp/xor.clear
python3 -c 'import sys; print(len(sys.stdin.buffer.read()))' < /tmp/xor.clear
# 258 (256 octets + le remplissage éventuel et le LF de sortie)
rm -f /tmp/xor.hex /tmp/xor.clear
```

### AES-128

```sh
# Flux : un bloc complet
printf 'All men must die\n' | ./my_pgp aes -c \
  57696e74657220697320636f6d696e67
# 744ce22c385958348f0df26eceb62eef

# Flux : déchiffrement
printf '744ce22c385958348f0df26eceb62eef\n' | ./my_pgp aes -d \
  57696e74657220697320636f6d696e67
# All men must die

# Flux : dernier bloc complété par des zéros, puis déchiffrement
printf 'ABC' | ./my_pgp aes -c 000102030405060708090a0b0c0d0e0f > /tmp/aes.hex
cat /tmp/aes.hex
./my_pgp aes -d 000102030405060708090a0b0c0d0e0f < /tmp/aes.hex
# ABC<octets NUL>

# Bloc : chiffrement et déchiffrement d'exactement 16 octets
printf '1234567890abcdef\n' | ./my_pgp aes -c -b \
  000102030405060708090a0b0c0d0e0f > /tmp/aes-block.hex
./my_pgp aes -d -b 000102030405060708090a0b0c0d0e0f < /tmp/aes-block.hex
# 1234567890abcdef
rm -f /tmp/aes.hex /tmp/aes-block.hex
```

En bloc, un message différent de 16 octets doit être refusé.

### RSA

```sh
# Générer une paire de clés à partir de deux nombres premiers
./my_pgp rsa -g d3 e3
# public key: 0101-19bb
# private key: 9d5b-19bb

# Chiffrer puis déchiffrer une ligne
printf 'WF\n' | ./my_pgp rsa -c 0101-19bb
# 8f84
printf '8f84\n' | ./my_pgp rsa -d 9d5b-19bb
# WF

# RSA accepte aussi l'option -b (elle n'a pas d'effet supplémentaire)
printf 'WF\n' | ./my_pgp rsa -c -b 0101-19bb
printf '8f84\n' | ./my_pgp rsa -d -b 9d5b-19bb
```

### PGP-XOR

```sh
# Bloc : le résultat contient d'abord la clé XOR chiffrée, puis le message
printf 'AB\n' | ./my_pgp pgp-xor -c -b 5746:0101-19bb
# 8f84
# 1507

# Bloc : déchiffrer avec la clé RSA privée et la clé XOR récupérée
printf '1507\n' | ./my_pgp pgp-xor -d -b 8f84:9d5b-19bb
# AB

# Flux : chiffrement et déchiffrement d'un message de longueur quelconque
printf 'ABC' | ./my_pgp pgp-xor -c 0102:0101-19bb > /tmp/pgp-xor.out
head -n 1 /tmp/pgp-xor.out
tail -n 1 /tmp/pgp-xor.out |
  ./my_pgp pgp-xor -d "$(head -n 1 /tmp/pgp-xor.out):9d5b-19bb"
rm -f /tmp/pgp-xor.out
```

### Système non implémenté

```sh
# PGP-AES doit échouer avec le code 84 et un message sur stderr
printf 'test' | ./my_pgp pgp-aes -c 00 2>/tmp/my_pgp.err
test "$?" -eq 84
cat /tmp/my_pgp.err
rm -f /tmp/my_pgp.err
```

### Vérification des entrées invalides

Chaque commande ci-dessous doit retourner `84` et écrire une erreur sur
`stderr` :

```sh
./my_pgp unknown -c aa
./my_pgp xor -c zz
./my_pgp xor -c -b aaaa <<<'A'
./my_pgp xor -d aa <<<'zz'
./my_pgp aes -c aa
./my_pgp rsa -g aa
./my_pgp pgp-xor -c 01:0101-19bb <<<'A'
```
