# IFT3913 — Tâche 3 : automatisation des tests de sécurité

**Binôme :** Alexandre Booh Louha (`Soglo3006`) et Rafi Dahoui (`doctor277`)  
**Cours :** IFT3913 — Qualité du logiciel, automne 2026  
**Étude de cas :** Apache Tika  
**Dépôt du travail :** https://github.com/Soglo3006/tika  
**Branche :** `tache3-semgrep`  
**Pull request de développement :** https://github.com/Soglo3006/tika/pull/1

> **Portée des résultats.** Les sept constructions de code ont été ajoutées à des fins d'étude de l'analyse statique dans un fork. Elles sont isolées et non invoquées par les fonctionnalités normales de Tika. Nous avons confirmé sept **détections Semgrep nouvelles** ; nous n'affirmons pas avoir démontré sept exploitations réelles.

## 1. Objectif et organisation

Le devoir vise à faire échouer une vérification GitHub Actions lorsqu'un commit introduit un nouveau résultat de sécurité Semgrep, tout en conservant les problèmes historiques comme référence. Il comprend aussi sept catégories de problèmes détectables, la comparaison des rapports avant/après, la justification des choix et une action réutilisable produisant un rickroll en cas d'échec Maven.

Le workflow modifié est `.github/workflows/main-jdk17-build.yml`. Les jobs `build` (Maven) et `security` (Semgrep) sont indépendants : un blocage de sécurité ne masque pas le résultat des tests Maven. Le job `e2e-tests` dépend de `build` et n'est lancé que si celui-ci réussit.

## 2. Conception du contrôle GitHub Actions

### 2.1 Installation et règles

L'étape d'installation exécute `python3 -m pip install semgrep==1.185.0`. La version épinglée réduit la variabilité entre exécutions. Trois configurations sont appliquées :

- `p/java` : règles communautaires relatives au code Java ;
- `p/security-audit` : règles d'audit, dont XXE, SQL et désérialisation ;
- `.semgrep/command-injection-process-builder.yaml` : règle supplémentaire, conservée localement dans le dépôt afin de prendre en compte le septième exemple.

La dernière règle provient du dépôt public `semgrep/semgrep-rules`. Elle est utilisée comme règle d'analyse statique ; une correspondance à son motif ne garantit pas à elle seule une injection de commandes exploitable.

### 2.2 Analyse différentielle

Le workflow effectue un `actions/checkout@v6` avec `fetch-depth: 0`, afin que le commit de référence soit accessible. Il détermine `BASE_SHA` depuis la base de la PR (`github.event.pull_request.base.sha`) ou le commit précédent d'un push (`github.event.before`). Il vérifie que cette valeur n'est ni vide ni entièrement nulle, puis que le commit existe.

La commande essentielle est :

```bash
semgrep scan \
  --config p/java \
  --config p/security-audit \
  --config .semgrep/command-injection-process-builder.yaml \
  --baseline-commit "$BASE_SHA" \
  --error .
```

`--baseline-commit` limite l'analyse différentielle aux nouvelles détections par rapport au commit de référence. `--error` fait terminer la commande avec un code non nul lorsqu'une détection bloquante est présente. Cela fait échouer le job `security`, sans nécessairement empêcher `build` de s'exécuter.

**Choix et limites :** les configurations distantes `p/java` et `p/security-audit` peuvent évoluer ; le gel de la version du CLI ne fige pas à lui seul le contenu des règles. Pour une reproductibilité stricte, il faudrait aussi figer toutes les règles téléchargées. Les branches concernées sont `main`, pour les PR et les pushs.

### 2.3 Validation réelle

Deux comportements ont été observés :

1. Sur la version initiale de la PR, l'étape Semgrep réussissait sans nouvelle détection, malgré les problèmes préexistants dans Tika.
2. Après l'introduction des exemples, le job `Semgrep security check` a signalé **7 findings, 7 blocking**, sur les fichiers modifiés, et s'est terminé avec le **code 1**.

Preuve : [exécution de la CI où les 7 nouveaux problèmes sont bloquants](https://github.com/Soglo3006/tika/actions/runs/44010280082/job/133795370410).  
Preuve après corrections de formatage : [nouvelle exécution du job de sécurité](https://github.com/Soglo3006/tika/actions/runs/44014212687/job/133808115085).

Cet échec rouge est **attendu pour le critère Semgrep** : il prouve que la vérification rejette les nouvelles constructions signalées.

## 3. Sept catégories introduites et détectées

| # | Catégorie | Fichier et méthode | Règle Semgrep | Ligne dans le rapport comparatif |
|---|---|---|---|---:|
| 1 | Hachage cryptographique faible (SHA-1) | `DigestHelper.java` — `sha1Demo` | `crypto.use-of-sha1` | 132 |
| 2 | Entités externes XML (XXE) | `IFT3913SecurityExamples.java` — `xmlExample` | `xxe.documentbuilderfactory-disallow-doctype-decl-missing` | 47 |
| 3 | Construction SQL non paramétrée | `IFT3913SecurityExamples.java` — `sqlExample` | `formatted-sql-string` | 58 |
| 4 | Aléatoire non cryptographique | `IFT3913SecurityExamples.java` — `weakTokenExample` | `crypto.weak-random` | 63 |
| 5 | Désérialisation Java non filtrée | `IFT3913SecurityExamples.java` — `deserializeExample` | `object-deserialization` | 69 |
| 6 | Socket TCP non chiffrée | `IFT3913SecurityExamples.java` — `socketExample` | `crypto.unencrypted-socket` | 78 |
| 7 | Construction d'une commande variable | `IFT3913SecurityExamples.java` — `commandExample` | `semgrep.command-injection-process-builder` | 83 |

Les numéros de ligne proviennent du rapport `semgrep-after-full.json` relevé lors de la comparaison et **peuvent se décaler après des corrections ultérieures** (notamment l'ajout de `Locale.ROOT` à l'exemple SQL).

**1 — SHA-1.** Nous avons choisi `DigestHelper.java` car cette classe manipule déjà le calcul d'empreintes. La méthode de démonstration utilise `MessageDigest.getInstance("SHA1")`. SHA-1 est inadapté lorsqu'une résistance moderne aux collisions est nécessaire. Semgrep signale `use-of-sha1`. Une alternative appropriée à cet usage est SHA-256.

**2 — XXE.** Nous avons créé une méthode de démonstration XML dans `IFT3913SecurityExamples.java`, module `tika-core`, car Tika est un analyseur de documents et le risque XML y est pertinent. Un `DocumentBuilderFactory` est créé sans désactivation explicite des déclarations DOCTYPE et des entités externes. Semgrep signale ce défaut de configuration. Pour des entrées XML non fiables, il faut désactiver les entités externes/DOCTYPE selon les besoins.

**3 — SQL.** La méthode `sqlExample` construit une chaîne SQL en y incorporant directement `documentName`, puis l'utilise dans `executeQuery`. Si l'entrée était non fiable, la structure de la requête pourrait être influencée. Semgrep signale `formatted-sql-string`. Le remède est une requête paramétrée avec `PreparedStatement`. L'ajout ultérieur de `Locale.ROOT`, nécessaire pour le plugin Maven Forbidden APIs, **ne supprime pas** le risque de construction SQL non paramétrée ni la détection Semgrep.

**4 — Aléatoire.** `weakTokenExample` utilise `Math.random()` pour une valeur présentée comme un jeton. Cet aléatoire n'offre pas les propriétés cryptographiques nécessaires à un secret. Semgrep signale `weak-random`. Le remède est `SecureRandom` quand une imprévisibilité de sécurité est nécessaire.

**5 — Désérialisation.** `deserializeExample` utilise `ObjectInputStream.readObject()` sur un flux fourni. En présence d'entrées non fiables et selon les classes disponibles, une désérialisation Java native peut produire des comportements indésirables. Semgrep signale `object-deserialization`. Il faut éviter la désérialisation native d'entrées non fiables ou appliquer des restrictions strictes.

**6 — Socket non chiffrée.** `socketExample` retourne `new Socket(host, port)`. Une socket TCP ne protège pas les échanges par chiffrement. Semgrep signale `unencrypted-socket`. Employer TLS (par exemple `SSLSocket`) lorsqu'il faut protéger confidentialité et intégrité du trafic.

**7 — Commande variable.** `commandExample` construit `new ProcessBuilder(command)`. Une commande déterminée à partir de données non fiables est risquée si elle est ensuite exécutée. La règle locale `command-injection-process-builder` la signale. **Le processus n'est pas lancé dans notre démonstration** ; la détection est donc un avertissement sur un motif susceptible de devenir dangereux. Il convient de valider explicitement les exécutables et arguments avant exécution.

**Justification de l'emplacement :** `DigestHelper.java` s'inscrit dans le domaine du hachage ; les autres exemples sont regroupés dans une classe isolée du module `tika-core`, pour éviter de modifier des chemins applicatifs et pour faciliter une comparaison contrôlée des résultats. Le choix est pratique pour la mesure de l'analyse statique, mais ne démontre pas l'existence de sept voies d'attaque fonctionnelles dans Tika.

## 4. Comparaison des rapports avant / après

Une copie de la branche `main` a été créée au moyen de `git worktree`. Les deux arbres ont été analysés avec les **mêmes trois configurations de règles**, en plaçant également la règle locale au même chemin relatif `.semgrep/command-injection-process-builder.yaml`.

| Mesure | Avant (`main`) | Après (`tache3-semgrep`) |
|---|---:|---:|
| Détections totales | **35** | **42** |
| Règles effectivement exécutées | 175 | 175 |
| Détections nouvelles attribuées aux démonstrations | — | **7** |

L'écart est de **+7**, soit sept nouvelles combinaisons `(règle, fichier)` : une dans `DigestHelper.java`, six dans `IFT3913SecurityExamples.java`. Un premier essai de comparaison donnait 23 différences parce que la règle additionnelle était chargée sous deux chemins différents, ce qui changeait les identifiants de règle. Après harmonisation du chemin, sept nouvelles combinaisons ont été observées.

Cette méthode de comparaison par `(check_id, path)` suffit à identifier ces sept exemples, mais ne différencie pas plusieurs détections d'une même règle au sein d'un même fichier ; une comparaison plus générale utiliserait aussi l'empreinte et l'emplacement de chaque finding.

Détails, protocole reproductible et liste des résultats : [**Comparaison Semgrep avant/après**](comparaison-semgrep.md).

## 5. Rickroll réutilisable, uniquement après un échec de test

L'action composite est enregistrée dans `.github/actions/rickroll/action.yml`. Elle écrit une notice GitHub Actions contenant le lien vers la vidéo Rickroll et le message `A test failed. Rickroll activated!`.

La condition initiale se basait uniquement sur l'échec de l'étape Maven. Elle a été améliorée afin de ne pas lancer le Rickroll pour les échecs sans rapport avec des tests, tels que Checkstyle, Forbidden APIs ou la compilation.

Le script `.github/scripts/check_failed_tests.py` parcourt les résumés texte générés par Maven Surefire et Failsafe (`**/surefire-reports/*.txt` et `**/failsafe-reports/*.txt`). Il lit les nombres `Failures` et `Errors` dans les lignes `Tests run:`. Ce choix évite d'introduire un analyseur XML supplémentaire, qui avait généré une alerte Semgrep sans rapport avec les sept exemples Java. Si l'un d'eux est supérieur à zéro, le script définit la sortie GitHub Actions `test_failed=true`. Sinon, la sortie vaut `false`.

Le workflow exécute ensuite :

```yaml
- name: Detect failed Maven tests
  id: detect_failed_tests
  if: ${{ failure() && steps.maven_tests.outcome == 'failure' }}
  run: python3 .github/scripts/check_failed_tests.py

- name: Rickroll on failed Maven tests
  if: ${{ failure() && steps.detect_failed_tests.outputs.test_failed == 'true' }}
  uses: ./.github/actions/rickroll
```

La même logique s'applique au job E2E.

**Justification :** le rapport Surefire/Failsafe apporte une preuve qu'un cas de test a réellement échoué ou a produit une erreur, ce qui répond plus précisément à la consigne qu'un déclenchement sur n'importe quel échec Maven. En l'absence de rapport de test en échec, le Rickroll ne se déclenche pas.

**Validation avant cette amélioration :** lors de l'exécution [GitHub Actions du commit `ad56f23`](https://github.com/Soglo3006/tika/actions/runs/44054080092), le test `S3PipeIntegrationTest` a effectivement déclaré `Errors: 1`, en raison du refus HTTP 401 de l'image Docker MinIO. L'action Rickroll précédente s'était alors exécutée. Cela confirmait le fonctionnement de l'action, sans encore prouver que sa condition discriminait les échecs non liés aux tests.

**Validation de la condition améliorée :** le job [GitHub Actions du commit de validation XML](https://github.com/Soglo3006/tika/actions/runs/44102857689/job/134107222872) a analysé 539 rapports Maven, identifié le test `S3PipeIntegrationTest` en erreur et exécuté le Rickroll après cette détection. Une dernière correction a remplacé l'analyse XML par la lecture des résumés texte afin d'éviter une huitième alerte Semgrep ; cette variante requiert une nouvelle validation CI. Le comportement attendu reste `test_failed=true` si un test Maven échoue et l'absence de Rickroll si aucune suite ne contient de `failure` ou d'`error`.

## 6. Difficultés et validation Maven

- **Checkstyle :** 86 erreurs de format, principalement des fins de ligne CRLF et des fins de fichier sans retour à la ligne. Après normalisation en LF, `mvn -pl tika-core -am validate` a produit `BUILD SUCCESS` et zéro violation.
- **Forbidden APIs :** le plugin refusait `String.format` sans locale explicite ; le code a été corrigé en ajoutant `Locale.ROOT`. Le scan Semgrep ciblé a **conservé les cinq détections attendues** dans le fichier de démonstration.
- **Intégration S3 :** des exécutions complètes du job Maven ont échoué dans `tika-pipes-s3-integration-tests` : le téléchargement de `quay.io/minio/minio:latest` a retourné `401 UNAUTHORIZED`. Cet échec observé est lié à une dépendance Docker du test et non au job de sécurité. Les builds Windows ont été rapportés comme réussis lors de la dernière validation. Nous n'avons pas modifié la configuration Docker, hors périmètre de la tâche.

Ces résultats ne signifient pas que l'intégralité de la suite Maven Linux a réussi ; la limite due à MinIO doit être distinguée du succès des modules précédents et du succès du contrôle Semgrep.

## 7. Conclusion

L'analyse différentielle Semgrep est opérationnelle dans GitHub Actions : sans nouvelle détection le contrôle peut réussir, alors qu'après introduction des sept exemples, il identifie **7 résultats bloquants** et échoue avec le code 1. La comparaison locale totale de 35 à 42 détections corrobore ces sept ajouts. Une action Rickroll composite a été intégrée ; sa condition consulte désormais les rapports Maven afin de se déclencher seulement lorsqu'un cas de test échoue ou produit une erreur. Les limites restantes portent notamment sur l'isolement des exemples et la couverture des règles.

## 8. Assistance et références

**Assistance IA :** ChatGPT a été utilisé pour proposer des démarches d'intégration, d'analyse, de résolution d'erreurs et pour structurer ce document ; les nombres et les comportements présentés proviennent des analyses Semgrep et des exécutions GitHub Actions effectivement observées.

- [Documentation Semgrep](https://semgrep.dev/docs/)
- [Documentation GitHub Actions](https://docs.github.com/en/actions)
- [Apache Tika](https://tika.apache.org/)
- [PR de développement](https://github.com/Soglo3006/tika/pull/1)
