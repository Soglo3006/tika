# Comparaison des rapports Semgrep — avant / après

**Auteurs :** Alexandre Booh Louha (`Soglo3006`) et Rafi Dahoui (`doctor277`)  
**Branche de travail :** `tache3-semgrep`  
**Référence :** `main`  
[Retour au README](README.md)

## Méthode

Les rapports ont été produits localement avec Semgrep CLI et les mêmes jeux de règles : `p/java`, `p/security-audit`, et `.semgrep/command-injection-process-builder.yaml`.

Le dépôt de référence a été obtenu par `git worktree add ..\tika-baseline main`. Pour éviter la divergence d'identifiants Semgrep, le fichier de règle locale a été copié vers `..\tika-baseline\.semgrep\command-injection-process-builder.yaml` avant le scan de référence.

Exemple PowerShell à la racine du dépôt Tika (l'ordre compte) :

```powershell
# Dans C:\Users\ablbo\tika
git worktree add ..\tika-baseline main
New-Item -ItemType Directory -Force ..\tika-baseline\.semgrep
Copy-Item .\.semgrep\command-injection-process-builder.yaml ..\tika-baseline\.semgrep\

cd ..\tika-baseline
semgrep scan --config p/java --config p/security-audit --config .semgrep/command-injection-process-builder.yaml --json --output ..\tika\semgrep-before-full.json .

cd ..\tika
semgrep scan --config p/java --config p/security-audit --config .semgrep/command-injection-process-builder.yaml --json --output semgrep-after-full.json .
```

Si le worktree existe déjà, ne pas relancer `git worktree add`.

## Résultats mesurés

| Indicateur | Avant | Après |
|---|---:|---:|
| Nombre total de détections | **35** | **42** |
| Nombre de règles effectivement exécutées | **175** | **175** |
| Nouvelles combinaisons règle/fichier | — | **7** |

**Différence nette : +7.**

## Sept résultats nouveaux

| Catégorie | Identifiant de règle | Fichier | Ligne du scan comparatif |
|---|---|---|---:|
| SHA-1 | `java.lang.security.audit.crypto.use-of-sha1.use-of-sha1` | `tika-core/src/main/java/org/apache/tika/digest/DigestHelper.java` | 132 |
| XXE | `java.lang.security.audit.xxe.documentbuilderfactory-disallow-doctype-decl-missing.documentbuilderfactory-disallow-doctype-decl-missing` | `tika-core/src/main/java/org/apache/tika/quality/IFT3913SecurityExamples.java` | 47 |
| Injection SQL | `java.lang.security.audit.formatted-sql-string.formatted-sql-string` | `tika-core/src/main/java/org/apache/tika/quality/IFT3913SecurityExamples.java` | 58 |
| Aléatoire faible | `java.lang.security.audit.crypto.weak-random.weak-random` | `tika-core/src/main/java/org/apache/tika/quality/IFT3913SecurityExamples.java` | 63 |
| Désérialisation | `java.lang.security.audit.object-deserialization.object-deserialization` | `tika-core/src/main/java/org/apache/tika/quality/IFT3913SecurityExamples.java` | 69 |
| Socket non chiffrée | `java.lang.security.audit.crypto.unencrypted-socket.unencrypted-socket` | `tika-core/src/main/java/org/apache/tika/quality/IFT3913SecurityExamples.java` | 78 |
| Commande variable | `semgrep.command-injection-process-builder` | `tika-core/src/main/java/org/apache/tika/quality/IFT3913SecurityExamples.java` | 83 |

Les chemins ci-dessus sont ceux montrés par Semgrep, avec les séparateurs Windows `\` normalisés en `/`. Les lignes peuvent varier si les fichiers sont encore modifiés (en particulier après l'ajout de `Locale.ROOT`).

## Comparaison reproductible

```powershell
$before = Get-Content .\semgrep-before-full.json -Raw | ConvertFrom-Json
$after = Get-Content .\semgrep-after-full.json -Raw | ConvertFrom-Json

$existing = @(
  $before.results | ForEach-Object {
    "$($_.check_id)|$($_.path -replace '\\','/')"
  }
)

$newFindings = @(
  $after.results | Where-Object {
    "$($_.check_id)|$($_.path -replace '\\','/')" -notin $existing
  }
)

"AVANT : $($before.results.Count)"
"APRES : $($after.results.Count)"
"NOUVEAUX : $($newFindings.Count)"
$newFindings | Select-Object check_id, path | Format-Table -AutoSize
```

Résultat observé :

```text
AVANT : 35
APRES : 42
NOUVEAUX : 7
```

### Pourquoi le premier essai donnait 23 ?

Une première comparaison affichait 23 combinaisons règle/fichier inédites parce que la règle `command-injection-process-builder.yaml` était chargée sous des chemins différents, d'où des identifiants `check_id` incohérents sur des fichiers existants. La règle a ensuite été chargée dans **les deux scans** depuis `.semgrep/command-injection-process-builder.yaml`. Cela a ramené le résultat à 7, qui correspondent aux nouveaux exemples.

### Portée et limites

L'absence de combinaison `(règle, fichier)` dans le rapport initial est vérifiée pour ces sept cas. Cette méthode ne prouve pas la nouveauté de plusieurs occurrences d'une même règle dans un même fichier ; les empreintes ou positions seraient nécessaires pour un comparateur général. La présence d'une alerte n'est pas une preuve d'exploitabilité.

Enfin, les deux fichiers JSON de scan sont les artefacts locaux `semgrep-before-full.json` et `semgrep-after-full.json`. Ce document résume leurs données vérifiées ; il ne prétend pas les joindre au dépôt tant qu'ils n'y ont pas été publiés.

## Validation CI

[Exécution GitHub Actions — sept nouvelles détections, code 1](https://github.com/Soglo3006/tika/actions/runs/44010280082/job/133795370410)

Cette exécution valide distinctement le comportement demandé du job Semgrep, indépendamment des échecs observés dans le build Maven.
