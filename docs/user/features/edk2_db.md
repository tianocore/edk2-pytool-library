# Edk2 Database

The general purpose of Edk2DB is to allow EDKII repos to query specific information about their environment. `Edk2Db` is
a subclass of [TinyDB](https://tinydb.readthedocs.io/en/latest/), with functionality expanded to meet the purpose, but
also more narrowly scoped in it's expected usage. The most notable is that `Edk2DB` narrows the types of ways it can be
instantiated to the following three scenarios:

1. File Storage Read & Write `FILE_RW`: This mode is intended for generating a database file that can be stored and used
   multiple times. This mode is slow as all database changes are written to file
2. File Storage Read Only `FILE_RO`: This mode is intended for consuming a database file generated in the above scenario
   , and running queries against it
3. In-Memory Storage Read & Write `MEM_RW`: This mode is intended for running quick queries with no persistent data.

`Edk2DB` also adds the concepts of Managing and running [Table Generators](#table-generators) /
[Advanced Queries](#advanced-queries), which will be discussed in more detail, in their own sections.

## General Flow

The expected usage of Edk2DB is fairly simple:

1. Instantiate the DB in the necessary mode
2. Register and run the necessary table generators
3. (optional) run advanced queries to generate wanted data
4. Release the database

### Instantiate Edk2DB

As mentioned above, there are three ways to instantiate the database, depending on your needs. Edk2DB requires that you
define the mode you are attempting to insatiate in, then provide the additional required arguments as kwargs.

``` python
# File Storage, Read and Write
db = Edk2DB(Edk2DB.FILE_RW, db_path=db_path, pathobj=pathobj)

# File Storage, Read Only
db = Edk2DB(Edk2DB.FILE_RO, db_path=db_path)

# In-Memory Storage, Read Only
db = Edk2DB(Edk2DB.MEM_RW, pathobj=pathobj)
```

Additionally, you can **and should** instantiate the database using a context manager, to ensure the database is
properly released when finished:

``` python
with Edk2DB(mode, **kwargs) as db:
    ...
```

### Register and run table generators

A [Table Generator](#table-generators) is a type of parser that creates a table in the database and fills it with rows
of data. While each table generator can generate one or more tables, they should never rely on, or expect, other tables
existing to generate it's own table. Advanced Queries should be used to make those associations.

It's simple to register a table generator! simply call the `register()` with one or more of the instantiated parsers:

``` python
db.register(Parser1())
db.register(Parser2(), Parser3())
```

If your parser needs some type of metadata (As an example, a few of the provided parsers need environment information),
then it can be set using the initializer of the Parser (`__init__(*args, **kwargs)`).

You can also clear your registered parsers, which may be necessary in some situations, such as re-running the same
parser with different environment information:

``` python
db.clear_parsers()
```

Lastly is running all registered parsers. The `parse()` command will iterate through all registered parsers and run
them. If you need to run the same Parser with different sets of metadata, you have two options:

```python
# Option 1: parse one at a time
db.register(Parser(env=env1))
db.parse()
db.clear_parsers()
db.register(Parser(env=env2))
db.parse(append=True)

# Option 2: parse together
db.register(Parser(env=env1), Parser(env=env2))
db.parse()
```

If for some reason, it is necessary to keep Table generators and the database separate, you can reverse the function call:

```python
# Before
db.register(Parser())
db.parse()

# Reversed
Parser().parse(db)
```

### Run Advanced Queries

Running advanced queries is simple! Similar to Table Generators, you will pass the instantiated Query, passing any
necessary metadata to the query to work properly:

```python
db.search(AdvancedQuery(cfg1=cfg1, cfg2=cfg2))
```

TinyDB does not support relationships betweed tables (i.e. Primary / Foreign Keys and JOINs). Due to this, the intent of
the Advanced Query is to compartmentalize the multiple query calls that may be necessary to mock that functionality.
Therefore, the expected return should continue to be a list of rows (json objects), similar to any other database query.
What the caller wishes to do with that data is up to them.

### Release the Database

If you are using a context manager, then this is handled automatically for you. Otherwise, you need to call `.close()`
on the database.

## Table Generators

Table generators are just that, classes that subclass the [TableGenerator](/api/database/edk2_db/#edk2toollib.database.edk2_db.TableGenerator)
, parse some type of information (typically the workspace) and insert the data into one of the tables managed by Edk2DB.
Multiple table generators are provided by edk2toollib, and can be seen at [edk2toollib/database/tables](https://github.com/tianocore/edk2-pytool-library/tree/master/edk2toollib/database/tables).
Edk2DB can use any class that implements the `TableGenerator` interface.

## Advanced Queries

Edk2DB supports running simple queries as defined by [TinyDb Query](https://tinydb.readthedocs.io/en/latest/usage.html#queries),
however TinyDB does not support relationships between tables (i.e. Primary Key / Foreign keys and JOINs). Due to this
limitation, the concept of `Advanced Queries` was created to compartmentalize the extra steps necessary to emulate the
functionality above. The [AdvancedQuery](/api/database/edk2_db/#edk2toollib.database.edk2_db.AdvancedQuery) class is the
interface that should be subclassed when creating a more complex query than filtering on a single database table. As
with the `TableGenerator`, multiple Advanced are provided by edk2toollib, and can be seen at
[edk2toollib/database/queries](https://github.com/tianocore/edk2-pytool-library/tree/master/edk2toollib/database/queries).
Edb2DB can use any class that implements the `AdvancedQuery` interface.
