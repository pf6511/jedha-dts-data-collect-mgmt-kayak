# jedha-dts-data-collect-mgmt-kayak
Data collection and Management module - project Kayak


## Kayak

Kayak est un moteur de recherche de voyages.

L’équipe marketing de Kayak souhaiterait créer une application capable de recommander aux utilisateurs où planifier leurs prochaines vacances. Cette application devrait s’appuyer sur des données réelles concernant :

* la météo,

* les hôtels dans la région.

L’application devrait ensuite être en mesure de recommander les meilleures destinations et hôtels en fonction de ces variables, à tout moment.


## But du projet

- Scraper les données des destinations  
- Récupérer les données météo de chaque destination  
- Obtenir des informations sur les hôtels de chaque destination  
- Stocker toutes les informations ci-dessus dans un data lake  (AWS S3)
- Extraire, transformer et charger les données nettoyées de votre data lake vers un data warehouse (AWS RDS)


## Livrables

- un csv dans un bucket S3 avec les informations Hotels X destinations X hotels
- une Base SQL avec les données de la base RDS
- une Map avec le Top-5 destinations (en terme de prévisions météo) 
- une map avec le Top-20 destinations de chaque top-destinations