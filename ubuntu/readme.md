# Ubuntu Packages

To install all the required ubuntu packages run:

    $ sudo apt install -y $(cat ubuntu/packages.txt)
    
# Installing Elasticsearch on Ubuntu

    $ wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
    $ sudo apt-get install apt-transport-https
    $ echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-6.x.list
    $ sudo apt-get update && sudo apt-get install elasticsearch

This installs but does not start the system. See:

    $ sudo /bin/systemctl daemon-reload
    $ sudo /bin/systemctl enable elasticsearch.service
    $ sudo systemctl start elasticsearch.service
    $ sudo systemctl stop elasticsearch.service
    
To change the the address Elasticsearch is running on let’s edit `/etc/elasticsearch/elasticsearch.yml`.  Find the line with `network.host` and update to look like this:

    network.host: 127.0.0.1
    
Check that it's running with curl:

    $ curl -XGET 'localhost:9200/?pretty'
