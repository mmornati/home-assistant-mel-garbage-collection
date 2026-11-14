---
title: Questions fréquentes
description: Réponses aux questions courantes sur MEL Collecte.
---

# Questions fréquentes

## Mon adresse n'est pas trouvée

L'intégration ne couvre que les 95 communes de la Métropole Européenne de Lille. Écrivez l'adresse avec le nom de la commune, par exemple `12 rue de Paris, Tourcoing`. Si elle reste introuvable, essayez sans le numéro.

## Les heures de passage sont décalées d'une heure

Jusqu’à la version 1.5.0, les créneaux publiés en heure locale étaient lus comme des heures UTC : une collecte de 18 h 30 apparaissait à 19 h 30 en hiver. Mettez l'intégration à jour.

## Les cartes n'apparaissent pas dans « Ajouter une carte »

Redémarrez Home Assistant après l'installation, puis rechargez la page du navigateur en vidant le cache. Dans l'application mobile : **Paramètres → Application compagnon → Débogage → Vider le cache de l'interface**.

## La carte affiche « Aucune adresse MEL Collecte n'est configurée »

L'intégration est installée mais aucune adresse n'a été ajoutée, ou sa première lecture a échoué. Regardez **Paramètres → Appareils et services → MEL Collecte**.

## Une collecte a été reportée et le calendrier ne le montre pas

Le calendrier vient du planning régulier de la MEL. Les reports (jours fériés, grèves, intempéries) sont annoncés par la MEL sous forme d'informations : elles apparaissent dans la carte « Prochaine collecte » et dans le capteur **Alertes collecte**.

## La déchèterie est indiquée ouverte alors qu'elle est fermée

Les horaires sont ceux publiés par la MEL. Une fermeture exceptionnelle qui n'y figure pas ne peut pas être connue de l'intégration. Dans le doute, le service déchets de la MEL répond au 0 800 711 771 (appel gratuit).

## Les distances ne correspondent pas à mon trajet

Les distances sont calculées à vol d'oiseau depuis votre adresse. Le lien **Itinéraire** donne le trajet réel.

## Combien de fois l'intégration interroge-t-elle la MEL ?

Une fois par semaine par défaut. Les capteurs recalculent leur état à partir des données déjà en mémoire, sans nouvelle requête. Le service `mel_collecte.force_refresh` déclenche une lecture immédiate.

## L'intégration fonctionne-t-elle ailleurs qu'à Lille ?

Non. Elle lit les données publiées par la MEL et ne connaît que ses communes.

## Je préfère l'anglais

Dans les options de l'intégration, choisissez **English** : les noms des capteurs, les types de déchets et les cartes changent de langue. Un [guide en anglais](en/user_guide.md) est disponible.
