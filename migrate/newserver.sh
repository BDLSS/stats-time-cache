# A script to help migration of data from an old server with an old version
# of Piwik to a new server and enable migration to newer versions of Piwik.
#
# It will:
# 1. download existing data (which you have previously dumped)
# 2. setup the new database
# 3. load existing data into it
# 4. remove any existing achives and convert engine to InnoDB
# 5. download and install old version of Piwik
# 6. pause whilst you setup Piwk and upgrade via web interface
# 7. migrate the data to the upgraded version via command line.
# 8. show command to run the archive cron job


# Find out name to use for db and web folder. This enables
# multiple installation of Piwik on the same server.
dbname=$1
if [ -z $dbname ]
then
  dbname="piwik_test1"
fi

# This needs to match the version installed on the old server since
# it needs installing after the database has been loaded with
# existing data. (Piwik installer lets you use existing data.)
old_version="1.11.1"

workdir="workdir_migrate"
mkdir $workdir

ip_address="$(ifconfig  | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}')"
echo "Running script on server with IP: $ip_address"


echo "1a. Fetching backup from existing database."
user="USERNAME ON SERVER"
server="orastats.bodleian.ox.ac.uk"
spath="/opt/statmaker/export/"
filename="orastatspiwik.sql"
echo "When prompted you need to enter the password on the remote server."
scp $user@$server:$spath/$filename.bz2 $workdir/$filename.bz2

echo "1b. Decompressing backup file."
bunzip2 $workdir/$filename.bz2
ls -lh $workdir/$filename


echo "2. Creating new database and user with full rights."
dbuser=$dbname
dbpass="PASSWORD FOR PIWIK DB"
mysql -u root -<MYSQLROOTPASSWORD> -e "create database $dbname; GRANT ALL PRIVILEGES ON $dbname.* TO $dbuser@localhost IDENTIFIED BY '$dbpass'"
echo "DB setup okay, configuration options when setting up Piwik."
echo "Database name: $dbname"
echo "Database user: $dbuser"
echo "Database password: $dbpass"

echo "3. Loading old data into new database. (takes about 2 minutes)"
mysql -u $dbuser -p$dbpass $dbname < $workdir/$filename

#read -p "When ready, press enter to drop the archive tables."
echo "4a. Dropping old archive tables."
tables="$(mysql -u $dbuser -p$dbpass $dbname -Bse 'show tables')"
for table in $tables; do
  if [[ $table == *piwik_archive* ]]; then
    echo "Deleting $table"
    mysql -u $dbuser -p$dbpass $dbname -Bse "drop table $table"
  fi
done

#read -p "When ready, press enter to convert tables to InnoDB."
echo "4b. Changing tables to INNODB engine."
tables="$(mysql -u $dbuser -p$dbpass $dbname -Bse 'show tables')"
for table in $tables; do
  echo "Change table to InnoDB engine: $table." 
  mysql -u $dbuser -p$dbpass $dbname -Bse "alter table $table engine=InnoDB"
done


echo "5a. Getting old version of Piwik, as used on old server."
piwname="piwik-$old_version.zip"
wget -P $workdir http://builds.piwik.org/$piwname

echo "Uncompressing and moving to webserver folder."
echo "When prompted you need to use the password on the local server."


echo "Uncompressing and moving to webserver folder."
echo "When prompted you need to use the password on the local server."
webname="test1_piwik"
webroot="/var/www"
webpath="$webroot/$webname"
unzip -q -d $workdir $workdir/$piwname
sudo mv $workdir/piwik $webpath
sudo chown -R www-data:www-data $webpath


echo "Connect to the webserver and run upgrade."
#See https://piwik.org/docs/update/
echo "Setting permissions 777 to enable auto update run via Piwik web interface."
sudo chmod -R 777 $webpath


#read -p "Upgrade to beta?"
#upgrade="2.0.4-b7"
#piwupname="piwik-$upgrade.zip"
#wget -P $workdir http://builds.piwik.org/$piwupname
#cp $webpath/config/config.ini.php $workdir/config.ini.php.from1.11.1
#ls -l $webpath
#unzip -q -d $workdir $workdir/$piwupname
#sudo unzip -o -d $webpath $workdir/$piwupname
#sudo cp -R  $workdir/piwik/*.* $webpath/
#ls -l $webpath
#sudo cp $workdir/config.ini.php.from1.11.1 $webpath/config/config.ini.php
#sudo chown -R www-data:www-data $webpath
#sudo chmod -R 755 $webpath

echo "6. You should now setup the old version of piwik via the web interface. Then"
echo "run the update of the core system. A blank page will appear. Redisplay"
echo "the index.php page and you get a prompt to update your DB structure. This"
echo "script will run the command shown."
echo "Web interface: http://$ip_address/$webname/"

read -p "7. When ready, press enter to run the DB update."
sudo -u www-data php $webpath/index.php -- "module=CoreUpdater"

echo "You should now edit the general settings in Piwik and install version >2.0.4-b7"
echo "When you get the prompt to update you DB stucture use the link provided since"
echo "it is usually a minor upgrade that is quick to run."
#read -p "When ready, press enter to run DB update."
#sudo -u www-data php $webpath/index.php -- "module=CoreUpdater"


echo "Setting permissions to 755, after updates."
sudo chmod -R 755 $webpath

echo "8. The migration has finished. You need to setup the cronjob. "
echo "The following will run it via the command line."
echo "The first run, good idea to increase memory_limit increase in php.ini config file. I used 2GB."
echo "On my test VM it takes about 60 minutes the first run."
echo "This command will fail (memory issues) on Piwik 2.0.3 hence the need for >2.0.4-b7"
echo "sudo su www-data -c \"/usr/bin/php5 $webpath/misc/cron/archive.php -- url=http://$ip_address/$webname\""
