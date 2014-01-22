echo 'You must pass the username who has access to the export.'
user="$1"
server="orastats.bodleian.ox.ac.uk"
path="/opt/statmaker/export"
scp -C "$user@$server:$path/actions.tsv" actions.tsv
scp -C "$user@$server:$path/visits.tsv" visits.tsv
scp -C "$user@$server:$path/links.tsv" links.tsv
