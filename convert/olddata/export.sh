echo 'Export data from Piwik to TSV files.'
echo 'This will fail if user stat-export does not have select access.'
echo 'Exporting links.'
mysql piwik --user=stat_export -e 'SELECT * FROM piwik_log_link_visit_action' > links.tsv
echo 'Export actions.'
mysql piwik --user=stat_export -e 'SELECT * FROM piwik_log_action' > actions.tsv
echo 'Export visits.'
mysql piwik --user=stat_export -e 'SELECT * FROM piwik_log_visit' > visits.tsv
#
# Dump the entire DB for migration to new server.
#
#mysqldump -u [username] -p[PASSWORD] piwik > orastatspiwik.sql
#bzip2 orastatspiwik.sql
