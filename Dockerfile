FROM docker.elastic.co/elasticsearch/elasticsearch:7.17.3
RUN elasticsearch-plugin install --batch https://github.com/alexklibisz/elastiknn/releases/download/7.17.3.0/elastiknn-7.17.3.0.zip