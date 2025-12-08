import pymysql
pymysql.install_as_MySQLdb()

# Esto engaña a Django para que no verifique si la versión es vieja
from django.db.backends.mysql.base import DatabaseWrapper
DatabaseWrapper.check_database_version_supported = lambda self: None
