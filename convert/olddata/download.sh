echo 'You must pass the username who has access to the export.'
user="$1"
server="orastats.bodleian.ox.ac.uk"
path="/opt/statmaker/export"
#scp -C "$user@$server:$path/actions.tsv" actions.tsv
#scp -C "$user@$server:$path/visits.tsv" visits.tsv
#scp -C "$user@$server:$path/links.tsv" links.tsv

# Copy entire dump for importing onto new server.
# This new server must have same version of Piwik.
#scp -C "$user@$server:$path/orastatspiwik.sql.bz2" orastatspiwik.sql.bz2
echo Uncompressing the SQL file...
#bunzip2 orastatspiwik.sql.bz2
ls -lh
