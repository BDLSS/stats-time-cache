echo This script takes a back up of the existing stats data and 
echo compresses it. It will take some time (when setup) to get
echo the stats for all years.

echo Dumping stats database to statspiwik.sql
#mysqldump -u <user> -p<PASSWORD>  piwik > statspiwik.sql
ls -lh statspiwik.sql
echo The file statspiwik.sql should be +800MB

echo Dump finished, compressing file.
#bzip2 statspiwik.sql
ls -lh statspiwik.sql.bz2
echo The file statspiwik.sql.bz2 should be +193MB
