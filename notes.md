# TODOs
* detect license plates https://github.com/openalpr/openalpr
* weather station (https://github.com/tomvanswam/compass-card)
* curtains: https://nl.slide.store

# Fix energy statistics
* SELECT * FROM `statistics` where start BETWEEN '2022-02-28 00:00:00' and '2022-02-28 12:00:00' and metadata_id = 95  
ORDER BY `statistics`.`start` DESC
