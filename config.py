
database_urls = {
    'local': "sqlite:///./local.db",
    'docker': "sqlite:///./docker.db",
}

database_url = database_urls['docker']

redis_hosts = {
    'local': 'localhost',
    'docker': 'redis'
}

redis_host = redis_hosts['docker']
