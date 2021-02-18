SQL_CREATE_TABLE = '''\
CREATE TABLE %(table)s (
    %(definition)s
)\
'''

SQL_CREATE_CHECK = '''\
ALTER TABLE %(table)s
    ADD CONSTRAINT %(name)s
    CHECK (%(check)s)\
'''

SQL_COMMENT_ON_COLUMN = '''\
COMMENT ON COLUMN %(table)s.%(column)s
    is '%(comment)s'\
'''

SQL_CREATE_PK = '''\
ALTER TABLE %(table)s
    ADD CONSTRAINT %(name)s
    PRIMARY KEY (%(columns)s)\
'''

SQL_CREATE_FK = '''\
ALTER TABLE %(table)s
    ADD CONSTRAINT %(name)s FOREIGN KEY (%(column)s)
    REFERENCES %(to_table)s (%(to_column)s)%(deferrable)s\
'''

SQL_CREATE_UNIQUE = '''
ALTER TABLE %(table)s
    ADD CONSTRAINT %(name)s
    UNIQUE (%(columns)s)\
'''

SQL_CREATE_INDEX = '''\
CREATE INDEX %(name)s
    ON %(table)s (%(columns)s)\
'''

SQL_GRANT = '''\
GRANT %(privileges)s
    ON %(name)s
    TO %(role)s\
'''

SQL_CREATE_SEQUENCE = '''\
CREATE SEQUENCE %(sq_name)s
    MINVALUE 1
    MAXVALUE %(sq_max_value)s
    START WITH 1
    INCREMENT BY 1
    CACHE 20\
'''

SQL_CREATE_TRIGGER = '''\
CREATE OR REPLACE TRIGGER %(tr_name)s
BEFORE INSERT ON %(tbl_name)s
FOR EACH ROW
WHEN (new.%(col_name)s IS NULL)
    BEGIN
        SELECT %(sq_name)s.nextval
        INTO :new.%(col_name)s FROM dual;
    END\
'''
