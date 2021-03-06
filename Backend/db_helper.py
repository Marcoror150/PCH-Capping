#!/usr/bin/env python3

# Helper functions that connects Python to the database
# Michael Gutierrez
# 10/16/2018

import pyodbc
from flask import flash, session

# Connect to the db and return the connection and cursor for query execution
def connectToDB():
    try:
        # Connect to the db and capture its object
        conn = pyodbc.connect('DSN=CHP-Server;UID=MaristSA;PWD=MaristSAPa$$1;')
        # conn = pyodbc.connect('DSN=childrenshomeus.local;UID=SOMETHING;PWD=SOMETHING;')

        conn.setencoding('utf-8') 

        # Create a cursor from the connection object
        cur = conn.cursor()
        return conn, cur
    except:
        raise ValueError('Unable to connect to the database')

# Check if a given table exists in the db
def tableExists(table):
    conn, cur = connectToDB()

    # Tables come back from db as list of tuples
    tables = getAllTables()
    
    # Loop through to find the table
    for tup in tables:
        if table in tup:
            return True
    else:
        return False 

# Get all columns of a given table
def getTableCols(table, showSerial):
    conn, cur = connectToDB()
    sql = ""
    if showSerial == False:

        # Query to get all columns except those that are serializable 
        sql = """
            SELECT c.name 
            FROM sys.columns c
            JOIN sys.tables AS t
            ON t.object_id=c.object_id
            WHERE c.name NOT IN(
                SELECT name 
                FROM sys.identity_columns
                WHERE is_identity=1)
            AND  t.name='%s'
        """
    else:
        # Query to get all columns
        sql = """
            SELECT [name] 
            FROM sys.columns 
            WHERE object_id = OBJECT_ID('%s') 
        """
    # Stitch together the sql query
    sql = sql % (table)

     # Execute the query and close the connection and return the results
    try:
        cur.execute(sql)
        entries = cur.fetchall()
        conn.close()
        return entries
    except:
        conn.close()

# Insert new entries into an existing table
def insertTable(table,values):
    conn, cur = connectToDB()

    # Check if the table exists first
    if not tableExists(table):
        raise ValueError('Table:%s does not exist' %table)

    # Unpack the columns because they come in as a list of tuples
    columns = [col for tupl in getTableCols(table,False) for col in tupl]

    sql = """
        INSERT INTO %s values(%s);
    """

    values_sql = ''
    if table == 'Incidents':
        sql = """
            INSERT INTO %s (kid,M_In_Pgm,uid) values(%s);
        """
        values_sql = ','.join(['?' for i in range(3)])
    else:
        values_sql = ','.join(['?' for i in range(len(values))])


    # Stitch together the sql query
    sql = sql % (table,values_sql)
    print(sql)

    # Execute the query, commit changes and close the connection
    try:
        cur.execute(sql, values)
        conn.commit()
        conn.close()
    except ValueError:
        conn.close()
        print('Unable to insert into table %s, check proper values or duplicate values' %table)


# Get all entries of a given table
def getTable(table):
    conn, cur = connectToDB()
    sql = """
        SELECT * FROM %s;
    """

    # Stitch together the sql query
    sql = sql % (table)

    # Execute the query and close the connection
    try:
        cur.execute(sql)

        # Iterate through the cursor results if there are any
        entries = cur.fetchall()
        conn.close()
        if not entries:
            print('No entries')
            return
        return entries

    except:
        conn.close()
        raise ValueError('Table:%d does not exist' %table)

# Get all tables in the db
def getAllTables():
    conn, cur = connectToDB()
    sql = """
        SELECT [name]
        FROM sys.tables
        WHERE create_date > Convert(datetime,'2018-01-01')
    """
    # Execute the query and close the connection
    try:
        cur.execute(sql)
        # Check if there are any results
        entries = cur.fetchall()
        conn.close()
        return entries
    except Exception as e: 
        print(e)
        conn.close()

# Run any general query
def query(query):
    conn, cur = connectToDB()
    sql = """
        %s
    """
    # Stitch together the sql query
    sql = sql % (query)

    # Execute the query and close the connection
    try:
        cur.execute(sql)

        # Iterate through the cursor results if there are any
        entries = cur.fetchall()
        if not entries:
            print('No entries')
            return
        # Print all entries to check
        for entry in entries:
            print(entry)

        conn.close()
    except Exception as e: 
        print(e)
        conn.close()

# Run any general query
def countChildren():
    conn, cur = connectToDB()
    sql = """
        SELECT count(KID)
        FROM Children
    """
    # Execute the query and close the connection
    try:
        cur.execute(sql)

        # Iterate through the cursor results if there are any
        count = cur.fetchall()
        conn.close()
        if not count:
            print('No entries')
            return
        return count[0][0]
    
    except Exception as e: 
        print(e)
        conn.close()


# Get children associated with a given program
def getChildrenProgram(program):
    conn, cur = connectToDB()
    sql = """
        SELECT *
        FROM ChildrenProgram
        WHERE PID in (
            SELECT PID
            FROM Program
            WHERE PID ='%s'
        )
    """
    # Stitch together the sql query
    sql = sql % (program)

    # Execute the query and close the connection
    try:
        cur.execute(sql)

        # Check if there are any results
        entries = cur.fetchall()
        conn.close()
        if not entries:
            print('No entries')
            return
        return entries

    except Exception as e: 
        print(e)

# Get the programs that have at least one child enrolled in it
def getPopulatedPrograms():
    conn, cur = connectToDB()
    sql = """
        SELECT DISTINCT PID
        FROM ChildrenProgram
    """
    # Execute the query and close the connection
    try:
        cur.execute(sql)

        # Check if there are any results
        entries = cur.fetchall()
        conn.close()
        if not entries:
            print('No entries')
            return
        return entries

    except Exception as e: 
        print(e)

# Get all incident types
def getIncidentTypes():
    conn, cur = connectToDB()
    sql = """
        SELECT *
        FROM IncidentTypes
    """
    # Execute the query and close the connection
    try:
        cur.execute(sql)

        # Check if there are any results
        entries = cur.fetchall()
        conn.close()
        if not entries:
            print('No entries')
            return
        return entries

    except Exception as e: 
        print(e)

# Get means per month for children of a given Incident Type
def getMeansPerMonth(incident_type,kid,daterange):
    conn, cur = connectToDB()
    sql = """
        SELECT count(Children.KID)
        FROM Incidents
        INNER JOIN IncidentClassification ON Incidents.IID = IncidentClassification.IID
        INNER JOIN IncidentTypes ON IncidentClassification.TID = IncidentTypes.TID
        INNER JOIN Children ON Children.KID = Incidents.KID
        INNER JOIN ChildrenProgram ON ChildrenProgram.KID = Children.KID
        WHERE M_In_Pgm = %s
        AND IncidentTypes.Name = '%s'
    """

    if kid is not 0:
        sql += f'AND Incidents.KID = {kid} '

    if daterange is not 0:
        daterange = daterange.split(' to ')
        date1 = daterange[0]
        date2 = daterange[1]

        sql += f"AND ChildrenProgram.StartDate >= '{date1}' AND ChildrenProgram.StartDate <= '{date2}'"

    # Execute the query and close the connection
    try:
        total_children = countChildren()
        incident_type = str(incident_type)

        # X axis
        months = [str(i) for i in range(1,13)]

        # Y axis
        means = []

        for month in months:
            query = sql % (month, incident_type)
            cur.execute(query)

            # Check if there are any results
            entries = cur.fetchall()
            if entries:
                means.append(round(float(entries[0][0]/total_children), 2))
        conn.close()

        mean = {'Mean Percentage of Youth':means}
        month = {'Month in Placement':months}

        return month, mean

    except Exception as e: 
        print(e)

# Check whether a username and password combination exists
def validateLogin(uname,pwd):
	conn, cur = connectToDB()
	sql = "SELECT * FROM Users WHERE username = '"+uname+"' AND password='"+pwd+"';"
	try:
		cur.execute(sql)	
		entries = cur.fetchall()
		conn.close()
		return entries
	except:
		conn.close()

# Given a username return that user's type
def getUserType(uname):
	conn, cur = connectToDB()
	sql = "SELECT UserType FROM Users WHERE username = '"+uname+"';"

	try:
		cur.execute(sql)
		entries = cur.fetchall()
		conn.close()
		return (entries[0][0])
	except:
		conn.close()

# Get the incident_type id given an incident name
def getTID(name):
    conn, cur = connectToDB()
    sql = """
        SELECT TID
        FROM IncidentTypes
        WHERE Name='%s'
    """
    # Stitch together the sql query
    sql = sql % (name)

    # Execute the query and close the connection
    try:
        cur.execute(sql)

        # Check if IncidentType exists
        entry = cur.fetchall()
        if not entry:
            conn.close()
            print('No entry')
            return
        else:
            conn.close()
            return entry[0][0]
    except Exception as e: 
        print(e)
        conn.close()
# Get latest id of the table last inserted to (serializable tables only)
def getLastID(id,table):
    conn, cur = connectToDB()
    sql = """
        SELECT MAX(%s) FROM %s;
    """
    sql = sql % (id, table)

    # Execute the query and close the connection
    try:
        cur.execute(sql)

        # Check if IncidentType exists
        entry = cur.fetchall()
        if not entry:
            conn.close()
            print('No entry')
            return
        else:
            conn.close()
            return entry[0][0]
    except Exception as e: 
        print(e)
        conn.close()

# Gets all entries from the User table
def getUsers():
	conn, cur = connectToDB()
	sql = "SELECT * FROM Users ORDER BY Last_Name;"
	
	try:
		cur.execute(sql)
		users = cur.fetchall()
		conn.close()
		return users
	except Exception as e:
		print(e)
		conn.close()
		
# Checks if the given username is already in the DB
def validateUsername(username):
	conn, cur = connectToDB()
	sql = "SELECT * FROM Users WHERE username='"+username+"';"
	
	try:
		cur.execute(sql)
		users = cur.fetchall()
		conn.close()
		if not users:
			return True
		else:
			return False
	except Exception as e:
		print(e)
		conn.close()

# Creates a new entry in the Users table with the given values
def createUser(values):
	conn, cur = connectToDB()
	sql = "INSERT INTO Users VALUES("
	for value in values:
		sql = sql + "'" + value + "',"
	
	sql = sql[:-1] + ");"

	try:
		cur.execute(sql)
		conn.commit()
		conn.close()
	except Exception as e:
		print(e)
		conn.close()
		
# Deletes a user from the Users table with the given UID
def removeUser(UID):
	conn, cur = connectToDB()
	sql = "DELETE FROM Users WHERE UID="+UID
	try:
		cur.execute(sql)
		conn.commit()
		conn.close()
	except Exception as e:
		print (e)
		conn.close()
		
# Changes the userType of the user with the given UID to the given userType
def changeUserType(UID,userType):
	conn, cur = connectToDB()
	sql = "UPDATE Users SET UserType = '"+userType+"' WHERE UID = "+UID+";"
	try:
		cur.execute(sql)
		conn.commit()
		conn.close()
	except Exception as e:
		print (e)
		conn.close()
	
# Changes the password of the user with the given UID to the given password
def changeUserPassword(UID,password):
	conn, cur = connectToDB()
	sql = "UPDATE Users SET Password = '"+password+"' WHERE UID = "+UID+";"
	try:
		cur.execute(sql)
		conn.commit()
		conn.close()
	except Exception as e:
		print (e)
		conn.close()
		
# Stores an already generated report as a string in the db
def storeReport(title,report):
    conn, cur = connectToDB()
    sql = f"""
        INSERT INTO Graph VALUES ('{title}',GETDATE(),'{report}')
    """
    try:
        cur.execute(sql)
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)
        conn.close()

# Gets all of the saved report queries
def getSavedReports():
	conn, cur = connectToDB()
	sql = "SELECT * FROM Graph ORDER BY GID DESC"
	try:
		cur.execute(sql)
		entries = cur.fetchall()
		conn.close()
		return entries
	except Exception as e:
		print (e)
		conn.close()
		
# Deletes a report from the Graph table with the given GID
def removeReport(GID):
	conn, cur = connectToDB()
	sql = "DELETE FROM Graph WHERE GID="+GID
	try:
		print(sql)
		cur.execute(sql)
		conn.commit()
		conn.close()
	except Exception as e:
		print (e)
		conn.close()
		
# Verifies that the password meets CHP's requirements
def verifyPassword(pwd):
	# Requirement 1: Password must be between 8-25 characters
	if len(pwd) < 8:
		flash("Password must be at least 8 characters.","error")
	elif len(pwd) > 25:
		flash("Password must be no more than 25 characters.","error")
	
	# Requirement 2: Password must contain at least 1 letter, 1 number, and 1 symbol
	hasLetter = False
	hasNumber = False
	hasSymbol = False
	validSymbols = ["!","@","#","$","%","^","&","*","(",")","`","~","-","_","+","=","{","}","[","]",":",";","'","|","\"","<",",",">",".","?","/"]
	
	# Requirement 3: Password must not contain spaces
	hasSpace = False
	
	# Checking requirements 2 and 3
	for char in pwd:
		if char.isalpha():
			hasLetter = True
		elif char.isdigit():
			hasNumber = True
		elif char in validSymbols:
			hasSymbol = True
		elif " " in pwd:
			hasSpace = True
			
	# Check if any of the requirements failed and display the proper message(s)
	error = False
	
	if not hasLetter:
		flash("Password must contain at least one letter.","error")
		error = True
	if not hasNumber:
		flash("Password must contain at least one number.","error")
		error = True
	if not hasSymbol:
		flash("Password must contain at least one symbol.","error")
		error = True
	if hasSpace:
		flash("Password cannot contain spaces.","error")
		error = True
		
	# Return the opposite of error because this function should return true if the password is valid
	return not error
		
# Gets all Incident Reports	submitted by Donnamarie or SuperInterns that have not been reviewed
def getUnreviewedReportsSuperInterns():
	conn, cur = connectToDB()
	sql = "SELECT * FROM Incidents WHERE status = 'NR' AND UID IN (SELECT UID FROM Users WHERE UserType='Full User' OR UserType='Super Intern');"
	try:
		cur.execute(sql)
		entries = cur.fetchall()
		conn.close()
		return entries
	except Exception as e:
		print (e)
		conn.close()

# Gets all Incident Reports submitted by Interns that have not been reviewed
def getUnreviewedReportsInterns():
	conn, cur = connectToDB()
	sql = "SELECT * FROM Incidents WHERE status = 'NR' AND UID NOT IN (SELECT UID FROM Users WHERE UserType='Full User' OR UserType='Super Intern');"
	try:
		cur.execute(sql)
		entries = cur.fetchall()
		conn.close()
		return entries
	except Exception as e:
		print (e)
		conn.close()

# Gets all Incident Reports submitted by Interns that have not been reviewed
def getAllUnreviewedReports():
	conn, cur = connectToDB()
	sql = "SELECT Incidents.*, Users.username, IncidentTypes.Name FROM Incidents INNER JOIN Users ON Incidents.UID = Users.UID INNER JOIN IncidentClassification ON Incidents.IID = IncidentClassification.IID INNER JOIN IncidentTypes ON IncidentClassification.TID = IncidentTypes.TID WHERE status = 'NR';"
	try:
		cur.execute(sql)
		entries = cur.fetchall()
		conn.close()
		return entries
	except Exception as e:
		print (e)
		conn.close()		
		
# Changes the Incident's Status to 'A' for accepted
def acceptReport(IID):
	conn, cur = connectToDB()
	sql = "UPDATE Incidents SET Status = 'A', UID = '1' WHERE IID = "+IID+";"
	try:
		cur.execute(sql)
		conn.commit()
		conn.close()
	except Exception as e:
		print (e)
		conn.close()
		
# Changes the Incident's Status to 'R' for rejected
def denyReport(IID):
	conn, cur = connectToDB()
	sql = "UPDATE Incidents SET Status = 'R' WHERE IID = "+IID+";"
	try:
		cur.execute(sql)
		conn.commit()
		conn.close()
	except Exception as e:
		print (e)
		conn.close()

# Changes all Incident Statuses to 'A' for accepted where the UID was that of a Full User or Super Intern
def acceptAllReports():
  conn, cur = connectToDB()
  sql = "UPDATE Incidents SET Status = 'A', UID = '1' WHERE UID IN (SELECT UID FROM Users WHERE UserType='Full User' OR UserType='Super Intern');"
  try:
    cur.execute(sql)
    conn.commit()
    conn.close()
  except Exception as e:
    print (e)
    conn.close()
    
# Gets all Incident Types from the DB
def getIncidentTypes():
  conn,cur = connectToDB()
  sql = "SELECT * FROM IncidentTypes;"
  try:
    cur.execute(sql)
    return cur.fetchall()
    conn.close()
  except Exception as e:
    print (e)
    conn.close()
    
# Creates an Incident record in the DB from the manual entry modal
def createManualIncident(KID,incidentType,UID):
  conn,cur = connectToDB()
  
  # Must create an entry in the Incident table first.
  sql = "INSERT INTO Incidents (KID,UID) VALUES ("+str(KID)+","+str(UID)+");"
  try:
    cur.execute(sql)
    conn.commit()
  except Exception as e:
    print (e)
    conn.close()
    
  # Create an entry in IncidentClassification, using the last IID created (the one we just created)
  iid = getLastID('IID','Incidents')
  sql = "INSERT INTO IncidentClassification VALUES("+str(iid)+","+incidentType+");"
  try:
    cur.execute(sql)
    conn.commit()
    conn.close()
  except Exception as e:
    print (e)
    conn.close()
    
# Creates an Incident record in the DB from the manual entry modal
def createManualIncidentAccept(KID,incidentType,UID):
  conn,cur = connectToDB()
  
  # Must create an entry in the Incident table first.
  sql = "INSERT INTO Incidents (KID,Status,UID) VALUES ("+str(KID)+",'A',"+str(UID)+");"
  try:
    cur.execute(sql)
    conn.commit()
  except Exception as e:
    print (e)
    conn.close()
    
  # Create an entry in IncidentClassification, using the last IID created (the one we just created)
  iid = getLastID('IID','Incidents')
  sql = "INSERT INTO IncidentClassification VALUES("+str(iid)+","+incidentType+");"
  try:
    cur.execute(sql)
    conn.commit()
    conn.close()
  except Exception as e:
    print (e)
    conn.close()