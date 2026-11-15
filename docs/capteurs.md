---
title: Capteurs
description: Le calendrier, les capteurs et les services créés par MEL Collecte.
---

# Capteurs

Chaque adresse crée un appareil **Collectes MEL**. Les identifiants exacts des entités dépendent de la langue choisie : ils sont visibles sur la page de l'appareil.

## Collectes

| Entité | État | Attributs utiles |
|---|---|---|
| Calendrier **Collectes des déchets** | Toutes les collectes à venir (90 jours par défaut) | `derniere_mise_a_jour`, `nombre_evenements` |
| **Prochaine collecte** | Date et heure du prochain passage | `types`, `types_friendly`, `couleurs`, `debut`, `fin` |
| **Jours avant prochaine collecte** | Nombre de jours, `0` le jour même | `next_collection_date`, `next_collection_type` |
| **Collecte *type*** | Prochain passage pour ce type de déchet | `couleur`, `debut`, `fin` |
| **Collecte *type* dans** | Nombre de jours avant ce passage | `prochaine_collecte`, `type_libelle`, `couleur` |
| **Alertes collecte** | Nombre d'informations publiées par la MEL | `alerts`, `last_alert_name`, `last_alert_message` |

Un capteur est créé pour chaque type de déchet collecté à votre adresse. Les codes utilisés par la MEL :

| Code | Type | Bac |
|---|---|---|
| `omr` | Ordures ménagères résiduelles | <span class="mel-swatch" style="--c:#7b8794"></span> gris |
| `emb` | Emballages recyclables | <span class="mel-swatch" style="--c:#f0b90b"></span> jaune |
| `dv`, `bio` | Biodéchets | <span class="mel-swatch" style="--c:#8d5b3a"></span> marron |
| `verre` | Verre | <span class="mel-swatch" style="--c:#2e9d5c"></span> borne |
| `enc` | Encombrants | sur rendez-vous |

## Déchèteries

| Entité | État | Attributs utiles |
|---|---|---|
| **Déchèterie la plus proche** | Nom de la déchèterie | `adresse`, `distance_km`, `ouverte`, `horaires_du_jour`, `fermeture`, `prochaine_ouverture`, `decheteries` (les cinq plus proches) |
| **Déchèterie ouverte** | Activé quand la déchèterie la plus proche est ouverte | `nom`, `fermeture`, `prochaine_ouverture` |
| **Prochaine déchèterie mobile** | Date et heure du prochain passage parmi les trois plus proches | `nom`, `adresse`, `distance_km`, `debut`, `fin`, `passages` (le prochain passage de chaque site des environs) |

Les capteurs de déchèterie portent des attributs `latitude` et `longitude` : ils s'affichent donc sur la carte **Plan** de Home Assistant.

Les horaires suivent ceux publiés par la MEL (été et hiver, dimanche matin). Les déchèteries sont fermées le 1er janvier, le 1er mai et le 25 décembre, comme le prévoit leur règlement d'accès.

## Services

| Service | Rôle |
|---|---|
| `mel_collecte.force_refresh` | Relit tout de suite les données de la MEL. Paramètre facultatif `entry_id` pour une seule adresse |
| `mel_collecte.set_collection_offset` | Règle le délai de l'événement de rappel : `hours_before`, 24 par défaut |

## D'où viennent les données

L'intégration lit la plateforme Publidata, celle qui alimente la page « déchets » du site de la MEL. Trois lectures par mise à jour pour les collectes (adresse, collectes, alertes) et quatre pour les lieux (déchèteries, déchèteries mobiles, composteurs, bornes à verre). Par défaut, cela arrive une fois par semaine. Aucun compte n'est nécessaire et rien n'est envoyé d'autre que l'adresse saisie.
