# TwineNeuron-1 — Guide utilisateur

## 1. Programmer un neurone
1. Choisir wᵢ ∈ [−7, 7] et b ∈ [−31, 31] (h = 0 en inférence, h = 1 pour lever les égalités).
2. Pour chaque entrée i : ENi_k = bit k de |wᵢ| ; à chaque évaluation : DPᵢ = xᵢ si wᵢ > 0 sinon 0,
   DMᵢ = xᵢ si wᵢ < 0 sinon 0.
3. Biais : ENB_k = bit k de |b| ; DBP = 1 si b > 0, DBM = 1 si b < 0.
4. Appliquer le code, attendre le front montant de CLK (85 ns après le changement à 10 MHz), lire Q.

Le traducteur de référence est `levels()` dans `twine_neuron/sim/tn.py`.

## 2. Portes logiques (validées en transitoire, `results/pre_func.csv`, `results/pre_xor.csv`)
| Porte | w1, w2 | b | h |
|---|---|---|---|
| ET | 2, 2 | −3 | 0 |
| OU | 2, 2 | −1 | 0 |
| NON-ET | −2, −2 | +3 | 0 |
| XOR (2 couches, multiplexé) | OU et NON-ET → ET | | |

## 3. Lire la somme pondérée (mode SAR)
Avec h = 1, Q = 1 ⇔ b ≥ 1 − Σw·x. Recherche dichotomique de b sur [−31, 31] (6 décisions) :
b_min = plus petit b donnant Q = 1, puis Σw·x = 1 − b_min. Exemple simulé : w = (7,7,7,7), x = 1111 →
décisions 0:1, −16:1, −24:1, −28:0, −26:1, −27:1 → Σw·x = 28 (`results/pre_sar.csv`).

## 4. Précautions
- Respecter le budget de stabilisation (≥ 58.1 ns au pire corner post-layout avant le front d'horloge).
- Consommation statique tant qu'une slice est active : mettre tous les EN à 0 (Hi-Z) au repos.
- Les nœuds VP/VM sont à haute impédance (Ru/D) : toute charge externe les ralentit et les décale.

## 5. Re-simuler
Dans le conteneur : `cd /foss/designs/twine_neuron && python3 sim/run_phase2.py func` (pré-layout) ou avec
`TN_NETLIST=pex/twine_neuron_pex.spice TN_RSHUNT=1e12` (post-layout). Corners : `sim/run_phase3.py`,
Monte Carlo : `sim/run_mc.py`.
