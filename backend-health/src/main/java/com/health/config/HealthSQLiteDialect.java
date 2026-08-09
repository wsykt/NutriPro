package com.health.config;

public class HealthSQLiteDialect extends org.hibernate.dialect.Dialect {
    public HealthSQLiteDialect() {
        super();
        registerColumnType(java.sql.Types.INTEGER, "INTEGER");
        registerColumnType(java.sql.Types.VARCHAR, "TEXT");
        registerColumnType(java.sql.Types.REAL, "REAL");
        registerColumnType(java.sql.Types.BLOB, "BLOB");
    }
}
