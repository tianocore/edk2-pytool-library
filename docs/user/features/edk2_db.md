# Edk2 Database

Edk2DB enables EDKII repository developers or maintainers to query specific information about their workspace. `Edk2Db`
utilizes the sqlite3 python module to create and manipulate a sqlite database. Multiple Table generators are provided
with edk2-pytool-library that developers can register and use, however a [Table Generator](#table-generators) interface
is also provided to allow the creation of additional parsers that create tables and insert rows into them.

Edk2DB automatically registers an environment table which records the current environment at the time of parsing, and
provides a unique key (a uuid) for that parse to all table generators. This unique key can optionally be used as a
column in the table to distinguish common values between parsing (Such as having a database that contains parsed
information about a platform as if it was built in DEBUG mode and as if it was built in RELEASE mode. Another example
is database that contains parsed information for multiple platforms or packages.)

Edk2DB automatically registers a junction table, `junction`, that acts as a lookup table between unique keys in two
tables to link them together, primarily for a one-to-many relation. One example used in the codebase is to associate
an INF file with the many source files it uses.

The database generated in an actual sqlite database and any tools that work on a sqlite database will work on this
database. VSCode provides multiple extensions for viewing and running queries on a standalone database, along with
other downloadable tools.

## General Flow

The expected usage of Edk2DB is fairly simple:

1. Instantiate the DB
2. Register and run the necessary table generators
3. (optional) run queries on the database through python's sqlite3 module
4. Release the database
5. (optional) run queries on the database through external tools

### Instantiate Edk2DB

Edk2DB supports normal instantiation and instantiation through a context manager. It is suggested to open the database
through a context manager, but if using it through normal instantion, remember to do a a final `db.connection.commit()`
and `db.connection.close()` to cleanly close the database.

``` python
db = Edk2DB(db_path, pathobj=pathobj)

with Edk2DB(db_path, pathobj=pathobj) as db:
   ...

```

### Register and run table generators

A [Table Generator](#table-generators) is a type of parser that creates a table in the database and fills it with rows
of data. A Table Generator should never expect specific data in a table to exist. It's simple to register a table
generator! simply call the `register()` with one or more of the instantiated parsers:

``` python
db.register(Parser1())
db.register(Parser2(), Parser3())
```

If your parser needs some type of metadata, then that metadata can be set in the initialization of the Parser
(`__init__(*args, **kwargs)`).

``` python
db.register(Parser1(x = 5, y = 7))
```

A method is provided to clear any registered parsers:

``` python
db.clear_parsers()
```

Lastly is running all registered parsers. The `parse(env: dict)` method expects to be provided a dictionary of
environment variables used when building a platform. Depending on the parser, the dictionary can be empty.

The `parse(env: dict)` command will perform two loops across the parsers.The first loop will create all tables for all
table parsers. This ensures that any dependencies on tables existing between parsers is handled. The second loop
performs the parsing and row insertion. The order in which parsers execute is the same as the order that they are
registered.

```python
# Option 1: parse one at a time
db.register(Parser(key=value2))
db.parse()
db.clear_parsers()
db.register(Parser(key=value2))
db.parse(env)

# Option 2: parse together
db.register(Parser(key=value1), Parser(key=value2))
db.parse(env)
```

### Release the Database

If you are using a context manager, then this is handled automatically for you. Otherwise, you need to call
`db.connection.commit()` and `db.connection.close()` on the database (or `__exit__()`)

## Table Generators

Table generators are just that, classes that subclass the [TableGenerator](/api/database/edk2_db/#edk2toollib.database.edk2_db.TableGenerator)
, parse some type of information (typically the workspace) and insert the data into one of the tables managed by Edk2DB.
Multiple table generators are provided by edk2toollib, and can be seen at [edk2toollib/database/tables](https://github.com/tianocore/edk2-pytool-library/tree/master/edk2toollib/database/tables).
Edk2DB can use any class that implements the `TableGenerator` interface.
