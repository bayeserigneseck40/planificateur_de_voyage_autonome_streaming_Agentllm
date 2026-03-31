# Agent Planificateur de Voyage Autonome — Architecture et Choix Techniques

Ce document détaille l'architecture sous-jacente de l'Agent Planificateur de Voyage Autonome. L'objectif de ce projet est de fournir un système capable d'organiser un voyage complet (vols, hôtels, restaurants, météo, itinéraire) de manière interactive et itérative avec l'utilisateur. Pour relever ce défi de planification complexe impliquant de multiples contraintes et sources de données, nous avons implémenté deux paradigmes majeurs de l'Intelligence Artificielle générative : **Chain-of-Thought (CoT)** et **ReAct (Reasoning + Acting)**.

---

## 1. Le Défi de la Planification Autonome

La planification d'un voyage n'est pas une tâche de simple récupération d'informations (Q&A). Elle requiert une compréhension profonde des intentions de l'utilisateur (souvent incomplètes, par exemple "je veux aller en Malaisie en septembre"), la collecte de données dynamiques via divers outils (météo, vols, hôtels), et la synthèse de ces données en un plan cohérent. 

Un modèle de langage (LLM) classique, interrogé de manière directe (Zero-Shot), échoue souvent sur ce type de problème car il a tendance à halluciner des données (prix de vols inventés) ou à oublier des contraintes temporelles et budgétaires. C'est pour pallier ces limites que les techniques CoT et ReAct ont été intégrées.

---

## 2. Chain-of-Thought (CoT) : Structuration du Raisonnement

La technique du **Chain-of-Thought (CoT)**, ou "Chaîne de Pensée", consiste à forcer le modèle à décomposer un problème complexe en une série d'étapes logiques intermédiaires avant de fournir une réponse finale [1].

### Pourquoi avoir choisi le CoT ?
Dans le contexte de notre planificateur de voyage, l'agent doit évaluer la faisabilité d'une destination à une période donnée avant de réserver quoi que ce soit. Par exemple, si l'utilisateur demande la Malaisie en septembre, l'agent doit d'abord penser : *"Je dois vérifier la météo en Malaisie en septembre. Si c'est la mousson sur la côte ouest, je devrai orienter l'itinéraire vers la côte est"*. Le CoT permet à l'agent de verbaliser cette réflexion, réduisant drastiquement les erreurs de logique et les recommandations incohérentes.

### Implémentation dans l'Agent
Nous avons implémenté le CoT à travers un bloc explicite `Thought:` (Pensée) généré par le modèle avant chaque action. Ce raisonnement est streamé en temps réel sur l'interface utilisateur. 

**Avantages observés :**
- **Transparence** : L'utilisateur comprend *pourquoi* l'agent fait certains choix (ex: pourquoi il recommande la côte est de la Malaisie).
- **Fiabilité** : En décomposant le problème, le LLM ne saute pas d'étapes cruciales (comme vérifier les vols avant de réserver un hôtel).

---

## 3. ReAct (Reasoning + Acting) : L'Interaction avec le Monde Réel

Si le CoT permet au modèle de mieux raisonner, il ne lui donne pas accès aux informations du monde réel. C'est ici qu'intervient **ReAct (Reasoning + Acting)** [2]. ReAct est un framework qui entrelace le raisonnement (Thought) avec la capacité d'exécuter des actions (Action) et d'observer leurs résultats (Observation).

### Pourquoi avoir choisi ReAct ?
Un planificateur de voyage a besoin de données spécifiques et à jour : les horaires de vols, les tarifs hôteliers, les conditions météorologiques. Le framework ReAct permet à l'agent d'agir comme un véritable assistant autonome : il réfléchit à ce dont il a besoin, appelle l'outil approprié, lit le résultat, et décide de la prochaine étape en fonction de ce résultat.

### La Boucle ReAct Implémentée
Le cœur de notre moteur (`agent_engine.py`) repose sur une boucle itérative stricte qui suit ce cycle :

| Étape | Rôle dans l'Agent | Exemple d'exécution |
|-------|-------------------|---------------------|
| **Thought** (Raisonnement) | Analyse l'état actuel et décide de la prochaine information à chercher. | *"L'utilisateur veut aller au Japon. Je dois d'abord vérifier la météo en avril."* |
| **Action** (Exécution) | Sélectionne un outil spécifique et formule les paramètres d'appel. | `get_weather_info(destination="Japon", month="avril")` |
| **Observation** (Retour) | Reçoit les données brutes renvoyées par l'outil exécuté. | *"Températures douces, saison des cerisiers en fleurs (Sakura)."* |

Cette boucle se répète jusqu'à ce que l'agent estime avoir collecté suffisamment d'informations pour construire l'itinéraire final via l'outil `build_itinerary`.

---

## 4. Synergie et Avantages de l'Approche Combinée

L'association de CoT et ReAct transforme un simple LLM textuel en un **Agent Autonome**. 

1. **Résolution de l'ambiguïté** : Grâce au CoT, l'agent identifie les informations manquantes. Grâce à ReAct, il peut soit utiliser un outil pour les trouver, soit décider de poser une question à l'utilisateur.
2. **Gestion des erreurs** : Si un outil renvoie une erreur (ex: "Aucun vol trouvé"), l'étape d'Observation capte cette erreur. Le prochain Thought analysera cet échec et proposera une alternative (ex: "Je vais chercher des vols pour des dates flexibles").
3. **Expérience Utilisateur (Streaming)** : En affichant la trace ReAct (les pensées et les appels d'outils) en temps réel sur l'interface Streamlit, l'utilisateur n'attend pas passivement face à un écran de chargement. Il voit l'agent "travailler" pour lui, ce qui renforce la confiance dans le système.

## Conclusion

L'utilisation conjointe des techniques Chain-of-Thought et ReAct est fondamentale pour la réussite de ce planificateur de voyage. Elle permet de dépasser les limites des modèles de langage statiques en leur offrant une structure de raisonnement rigoureuse couplée à une capacité d'interaction dynamique avec des outils externes, aboutissant à des recommandations de voyage précises, logiques et personnalisées.

---

## 5. Envoi d'Email avec SMTP

L'agent intègre un module d'envoi d'email natif (`utils/email_sender.py`) reposant exclusivement sur la bibliothèque standard Python (`smtplib`, `email`), sans dépendance externe supplémentaire. Il supporte les fournisseurs Gmail, Outlook, Yahoo et tout serveur SMTP personnalisé.

### Fonctionnement

Lorsque l'utilisateur clique sur **"Envoyer par Email"** dans l'interface Streamlit, un formulaire s'affiche permettant de :

1. Sélectionner son fournisseur de messagerie (Gmail, Outlook, Yahoo, ou SMTP custom)
2. Saisir l'adresse destinataire et les identifiants SMTP
3. Déclencher l'envoi en un clic

L'agent génère automatiquement le PDF de l'itinéraire, puis envoie un email avec un **corps HTML élégant** (aperçu de l'itinéraire, mise en page responsive) et le **PDF en pièce jointe**.

### Configuration Gmail (recommandée)

Gmail exige l'utilisation d'un **Mot de passe d'application** (App Password) et non votre mot de passe principal, pour des raisons de sécurité. Pour en générer un :

1. Activez la validation en deux étapes sur votre compte Google
2. Rendez-vous sur [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Créez un mot de passe pour "Autre application" et copiez-le dans le champ SMTP

Ces identifiants peuvent également être pré-remplis dans le fichier `.env` pour éviter de les ressaisir à chaque session :

```env
SMTP_SENDER_EMAIL=votre.email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

| Fournisseur | Serveur SMTP | Port | Authentification |
|-------------|-------------|------|------------------|
| Gmail | smtp.gmail.com | 587 | App Password |
| Outlook / Hotmail | smtp-mail.outlook.com | 587 | Mot de passe habituel |
| Yahoo Mail | smtp.mail.yahoo.com | 587 | App Password |
| Custom | Votre serveur | 587 | Selon config |

---

## Références

[1] Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q., & Zhou, D. (2022). Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. *arXiv preprint arXiv:2201.11903*.
[2] Yao, S., Zhao, J., Yu, D., Du, N., Narasimhan, I., Hwang, V., & Chen, K. (2022). ReAct: Synergizing Reasoning and Acting in Language Models. *arXiv preprint arXiv:2210.03629*.
