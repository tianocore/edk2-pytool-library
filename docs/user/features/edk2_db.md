# Edk2 Database

Edk2DB enables EDKII repository developers or maintainers to query specific information about their workspace. `Edk2Db`
utilizes the sqlalchemy and sqlite3 python modules to create and manipulate a sqlite database. Multiple Table
generators are provided with edk2-pytool-library that developers can register and use, however a [Table Generator](#table-generators)
interface is also provided to allow the creation of additional parsers that create tables and insert rows into them.

Edk2DB provides a unique key (a uuid) for each execution of `parse` to all table generators. This unique key can
optionally be used as a column in the table to distinguish common values between parsing (Such as having a database
that contains parsed information about a platform as if it was built in DEBUG mode and as if it was built in RELEASE
mode. Another example is database that contains parsed information for multiple platforms or packages.)

The database generated in an actual sqlite database and any tools that work on a sqlite database will work on this
database. VSCode provides multiple extensions for viewing and running queries on a standalone database, along with
other downloadable tools.

Once parsing is complete, the easiest way to work with the data is to use the context manager
`with <db>.session() as session:` which provides access to a sqlalchemy session variable for working with data in the
database. By using sqlalchemy as an ORM, users do not need to worry about the database itself, and will be able to
work with python objects representing rows in a database. This will be discussed in [Working with Database Data](#working-with-database-data).

## General Flow

The expected usage of Edk2DB is fairly simple:

1. Instantiate the DB
2. Register and run the necessary table generators
3. (optional) Work with the data
4. Release the database
5. (optional) run queries on the database through external tools

### Instantiate Edk2DB

Instantiating a database is as simple as initializing `Edk2DB` with the database path and optionally a Edk2Path object.
The Edk2Path object is only necessary if running parsers. If you are opening an existing database to work with the
data, it is not needed. You can optionally create an in-memory database by passing ":memory:" as the path.

``` python
db = Edk2DB(db_path, pathobj=pathobj)
db = Edk2DB(db_path)
db = Edk2DB(":memory")
```

### Register and run table generators

A [Table Generator](#table-generators) is a type of parser that creates a table(s) in the database and fills it with
rows of data. Pre-made table generators exist at `edk2toollib.database.tables`, but a user can create their own by
subclassing the `TableGenerator` object also found at `edk2toollib.database.tables`. It's simple to register a table
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

## Table Generators

Table generators are just that, classes that subclass the [TableGenerator](/api/database/edk2_db/#edk2toollib.database.edk2_db.TableGenerator)
, parse some type of information (typically the workspace) and insert the data into one of the tables managed by Edk2DB.
Multiple table generators are provided by edk2toollib, and can be seen at [edk2toollib.database.tables](https://github.com/tianocore/edk2-pytool-library/tree/master/edk2toollib/database/tables).
Edk2DB can use any class that implements the `TableGenerator` interface.

When creating a a custom table generator, you will also need to create create an ORM mapping for your table(s). Reading
the [ORM Quick Start](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) provided by sqlalchemy is the best way to
go, but here is a simple example so you know what to expect

```python
from edk2toollib.database import Edk2DB

class ExampleTable(Edk2DB.Base):
   __tablename__ "example"

   id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
   uuid: Mapped[str] = mapped_column(String(32))
```

This example simply creates a table "example" with two columns. The first is an auto-incrementing primary key while
the second is a string that is always 32 characters long, representing a uuid. Between the provided documentation above
and examples found at [edk2toollib.database](https://github.com/tianocore/edk2-pytool-library/blob/master/edk2toollib/database/__init__.py)
, it should be relatively simple to create a mapping.

## Working with database data

As mentioned at the beggining, Edk2DB uses sqlalchemy's ORM (Object-Relational Mapping) functionality for working with
data in the database. This abstracts the database schema and the complexities of working with databases (particularly
one that is unfamiliar or can change on use-case since adding additional tables is supported). Instead users can rely
on this functionality to write simple queries and get access to database information as objects without needing to
worry about the database itself.

Users should follow the [ORM Querying Guide](https://docs.sqlalchemy.org/en/20/orm/queryguide/index.html) for detailed
documentation, but here is a simple query example using the Mappings provided by Edk2DB at [edk2toollib.database](https://github.com/tianocore/edk2-pytool-library/blob/master/edk2toollib/database/__init__.py)

```python
from edk2toollib.database import Edk2DB, InstancedInf, Fv
from sqlalchemy.orm import aliased

with Edk2DB(DB_PATH).session() as session:
   dsc_components_query = (
      session
         .query(InstancedInf)
         .filter_by(cls = None, arch = "IA32")
         .order_by(InstancedInf.package_name, InstancedInf.path)
   )

   fdf_components_query = (
      session
         .query(InstancedInf)
         .join(Fv.infs)
         .filter(InstancedInf.arch == "IA32")
   )

   dsc_components = set([inf.path for inf in dsc_components_query.all()])
   fdf_components = set([inf.path for inf in fdf_components_query.all()])

   unused_componets = dsc_components - fdf_components
```

The above example is a simple way to determine which IA32 components were compiled per the DSC but not placed in the
final binary per the FDF.
