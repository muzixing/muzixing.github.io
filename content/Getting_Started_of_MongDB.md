title:Getting Started of MongoDB
tags:MongoDB, pymongdb
date:2016/08/30
Category:Tech

### What is MongoDB

MongoDB is an open-source document database that provides high performance, high availability, and automatic scaling.[1]


MongoDB（来自于英文单词“Humongous”，中文含义为“庞大”）是可以应用于各种规模的企业、各个行业以及各类应用程序的开源数据库。作为一个适用于敏捷开发的数据库，MongoDB的数据模式可以随着应用程序的发展而灵活地更新。与此同时，它也为开发人员 提供了传统数据库的功能：二级索引，完整的查询系统以及严格一致性等等。 MongoDB能够使企业更加具有敏捷性和可扩展性，各种规模的企业都可以通过使用MongoDB来创建新的应用，提高与客户之间的工作效率，加快产品上市时间，以及降低企业成本。

MongoDB是专为可扩展性，高性能和高可用性而设计的数据库。它可以从单服务器部署扩展到大型、复杂的多数据中心架构。利用内存计算的优势，MongoDB能够提供高性能的数据读写操作。 MongoDB的本地复制和自动故障转移功能使您的应用程序具有企业级的可靠性和操作灵活性。[2]

### About MongoDB
MongoDB is a No-SQL database. MongoDB server can maintain some databases, each database can maintain many collections. Collection is a concept like table in SQL database. Each Collection contain many documents. Each Document is a Json style object, which has many 'key':'value' pairs. For easy under stand, a table refered from [3] shows below.

<table class="table-bordered table-striped table-condensed">
<tbody><tr>
<th>SQL Term/Concept</th>
<th>MongoDB Term/Concept</th>
<th>Description</th>
</tr>
<tr>
<td>database</td>
<td>database</td>
<td>数据库</td>
</tr>
<tr>
<td>table</td>
<td>collection</td>
<td>数据库表/集合</td>
</tr>
<tr>
<td>row</td>
<td>document</td>
<td>数据记录行/文档</td>
</tr>
<tr>
<td>column</td>
<td>field</td>
<td>数据字段/域</td>
</tr>
<tr>
<td>index</td>
<td>index</td>
<td>索引</td>
</tr>
<tr>
<td>table joins</td>
<td>&nbsp;</td>
<td>表连接,MongoDB不支持</td>
</tr>
<tr>
<td>primary key</td>
<td>primary key</td>
<td>主键,MongoDB自动将_id字段设置为主键</td>
</tr>
</tbody></table>


### Install MongoDB
For Mac OS, MongoDB can be installed by using command[4]:

```shell    
    brew install mongodb
```

if you want to install MongoDB with supporting TSL/SSL:

```shell
    brew install mongodb --with-openssl
```

### Install Pymongo
To use MongDB by Python, you still need to install pymongo

```shell
    pip install pymongo
```
if you use Python3, please use pip3 to install pymongo

### Use MongoDB by CLI
After installing MonogoDB, you can start MongoDB by[5]:

```sh
    ./mongo
```

Because the CLI is a JavaScript shell, so you can execute code with it. For example, you can do some easy calculation.

```sh  
    >1+2
    >3
```

#### List database

```sh   
    > show dbs
    local  0.000GB
    test   0.000GB
```

#### Use database

```sh   
    > use test
    switched to db test    
```

#### Show database name of which is using

```sh
    >db
    test
```

#### Create database
You can enter 'use database_name' to create a new database, if the database name is not existed.

```sh
    > use milestone
    switched to db milestone
```

Only when you add some documents into dababase's collection, can you see the database name by using 'show dbs'. However you can use 'db' to show the using database.

#### List collections

```sh
    show collections
```

#### Create collection
You can use createCollection method to create a collection for databse.

```sh
    > show collections
    > db.createCollection("muzixing",{size:100000})
    { "ok" : 1 }
    > show collections
    muzixing
    > 
```

#### Remove collection

```sh
    db.collection_name.drop()
```

#### Add document into collection
You can insert data by insert method:

```sh
    > db.muzixing.insert({"name":"www.muzixing.com"})
    WriteResult({ "nInserted" : 1 })
    >
```

#### Search document
Use find() method to find all documents or fill parameter to select documents.

```sh
    > db.muzixing.find()
    { "_id" : ObjectId("57c6102b4366cfc975563b94"), "name" : "www.muzixing.com" }
    { "_id" : ObjectId("57c611d24366cfc975563b95"), "name" : "chengli" }
    { "_id" : ObjectId("57c611d94366cfc975563b96"), "name" : "milestone" }
    > 
    > db.muzixing.find({'name':'www.muzixing.com'})
    { "_id" : ObjectId("57c6102b4366cfc975563b94"), "name" : "www.muzixing.com" }
    > 
```

Also, findOne method can be use to get one document.

```sh
    > db.muzixing.findOne()
    { "_id" : ObjectId("57c6102b4366cfc975563b94"), "name" : "www.muzixing.com" }
    > db.muzixing.find()
    { "_id" : ObjectId("57c6102b4366cfc975563b94"), "name" : "www.muzixing.com" }
    { "_id" : ObjectId("57c611d24366cfc975563b95"), "name" : "chengli" }
    { "_id" : ObjectId("57c611d94366cfc975563b96"), "name" : "milestone" }
    > 
```

#### Update document
Update command's syntax shows below:

```sh
    db.collection.update(
       <query>,
       <update>,
       {
         upsert: <boolean>,
         multi: <boolean>,
         writeConcern: <document>
       }
    )
```

For example:

```sh
    > db.muzixing.update({"name":"licheng"},{$set:{"name":"chengli"}})
    WriteResult({ "nMatched" : 0, "nUpserted" : 0, "nModified" : 0 })
    
    > db.muzixing.find()
    { "_id" : ObjectId("57c615564366cfc975563b97"), "name" : "chengli", "face" : "handsome" }
    
    > db.muzixing.update({"name":"chengli"},{$set:{"name":"licheng"}})
    WriteResult({ "nMatched" : 1, "nUpserted" : 0, "nModified" : 1 })
    
    > db.muzixing.find()
    { "_id" : ObjectId("57c615564366cfc975563b97"), "name" : "licheng", "face" : "handsome" }
    > 
```

### Remove document

Syntax shows below

```sh
    db.collection.remove(
       <query>,
       <justOne>
    )
```

For example:

```shell
    > db.muzixing.find()
    { "_id" : ObjectId("57c615564366cfc975563b97"), "name" : "licheng", "face" : "handsome" }
    { "_id" : ObjectId("57c617694366cfc975563b98"), "name" : "girl friend", "face" : "beautiful" }
    > db.muzixing.remove({'name':"licheng"})
    WriteResult({ "nRemoved" : 1 })
    > db.muzixing.find()
    { "_id" : ObjectId("57c617694366cfc975563b98"), "name" : "girl friend", "face" : "beautiful" }
    > 
```

For more info of learning MongoDB for Chinese, see [MongoDB tutorial. ](http://www.runoob.com/mongodb/mongodb-tutorial.html)

For English speaker, see [MongoDB Docs.](https://docs.mongodb.com/)and [tutorialspoint-MongoDB](http://www.tutorialspoint.com/mongodb/index.htm)

### Pymongo

Actually, people always use some coding language libs to use MongoDB instead of CLI. After learning MongoDB and CLI usage, it is completely easy to understand how to use pymongo to manipulate MongoDB[7]. 

First of all, you should start a MongoDB server, such as we can start MongoDB at localhost, the default port of MongoDB is 27017.

Example shows below:

```py
    import pymongo
    from pymongo import MongoClient
    
    
    if __name__ == "__main__":
        # get client
        client = MongoClient('mongodb://localhost:27017/')
        print("client", client)
    
        # get database, if the database has existed.Otherwise, create it
        db = client.test
        print("db:", db)
    
        # get collection, if it has existed, otherwise, create it.
        collection = db.chengli
        print("collection name", db.collection_names())
        print("collection: ", collection)
    
        # get document
        print('find one: ', collection.find_one())
    
        # post data item
        new_man = {'age': 20, 'name': 'oo', 'sex': 'male', 'id': 5}
        collection.insert(new_man)
        print(collection.find().count())
    
        # get multi items
        for i in collection.find():
            print(i)
    
        # find data
        data = collection.find_one({'name':"chengli"})
        print(data['name'])
    
        # update data
        collection.update({'name':'haha'},{'$set':{'title':'employee'}})
        collection.remove({'title':'employee'})
        collection.create_index([('age',pymongo.ASCENDING),])
    
        for i in collection.find().sort('age', pymongo.ASCENDING):
            print(i)
```

**Note that**

* This is Python3 code.
* Some code is Non-idempotent, such as insert data and remove data, so different results will generate when run code in different round.

More info of pymongo, see [Mongo API Doc](http://api.mongodb.com/python/current/tutorial.html).


### References

[1]https://www.mongodb.com
[2]https://www.mongodb.com/cn
[3]http://www.runoob.com/mongodb/mongodb-databases-documents-collections.html
[4]https://docs.mongodb.com/manual/installation/
[5]http://www.runoob.com/mongodb/mongodb-linux-install.html
[7]http://wiki.jikexueyuan.com/project/start-learning-python/232.html





