import mysql.connector
import inquirer
from inquirer import errors
import argparse


def is_int(answers, current):
   if current.isnumeric() != True:
    raise errors.ValidationError('', reason='Not a valid number')
   else: return True

def main():
    
    # INIT VARIABLES
    access_questions = []
    ip_input = None
    user_input = None
    pass_input = None
    db_input = None
    table_input = None


    # SET UP ARGUMENT PARSING
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-i", "--ip", help="host ip address")
    argParser.add_argument("-u", "--username", help="username")
    argParser.add_argument("-p", "--password", help="password")
    argParser.add_argument("-d", "--database", help="target database")
    argParser.add_argument("-t", "--table", help="target table")

    args = argParser.parse_args()
    
    # ADD QUESTIONS TO LIST FOR EACH ARGUMENT NOT ADDED
    if args.ip is None:
        access_questions.append(inquirer.Text('ip', message="Specify a Host IP address"))
    else:
        ip_input = args.ip
    if args.username is None:
        access_questions.append(inquirer.Text('username', message="Enter your Username"))
    else:
        user_input = args.username
    if args.password is None:
        access_questions.append(inquirer.Text('password', message="Enter your Password"))
    else:
        pass_input = args.password
    if args.database is None:
        access_questions.append(inquirer.Text('db_name', message="Enter the Name of the Database you are connecting to"))
    else:
        db_input = args.database
    if args.table is not None:
        table_input = args.table

    # ASK ALL APPENDED QUESTIONS
    access_answers = inquirer.prompt(access_questions)

    # REQUEST TO CONNECT TO THE DATABASE
    access_db = mysql.connector.connect(
        host = ip_input,
        user = user_input,
        password = pass_input,
        database = db_input
    )


    # START CURSOR
    cursor = access_db.cursor(buffered = True)


    # ASK WHICH TABLE TO INSERT INTO
    table_questions = [
       inquirer.Text('table_name', message="What is the exact name of the table you wish to insert into?")
    ]

    # CHECK IF TABLE WAS ENTERED IN ARGS LIST
    table_answers = None
    if table_input is None:
        table_answers = inquirer.prompt(table_questions)
        table_input = table_answers.get("table_name")

    select = "SELECT * FROM " + table_input
    cursor.execute(select)

    # PROCEDURALLY GET EACH COLUMN AND ASK THE USER WHAT SHOULD GO INTO THE COLUMN
    num_fields = len(cursor.description)
    field_names = [i[0] for i in cursor.description]

    input_answers = {}

    for field in field_names:
        type_query = "SELECT\
                            COLUMN_TYPE\
                        FROM\
                            INFORMATION_SCHEMA.COLUMNS\
                        WHERE\
                            TABLE_SCHEMA = \'{0}\' AND TABLE_NAME = \'{1}\' AND COLUMN_NAME = \'{2}\';".format(db_input, table_input, field)

        cursor.execute(type_query)

        field_type = cursor.fetchall()
        field_type = field_type[0][0]

        if "enum" in field_type:

            field_type = field_type.replace("enum", "")
            field_type = field_type.replace("(", "")
            field_type = field_type.replace(")", "")
            field_type = field_type.replace("\'", "")
            enum_vals = field_type.split(",")
            field_questions = [
                inquirer.List(
                    field,
                    message="Pick a type of " + field,
                    choices=enum_vals
                ),
            ]
        elif "year" in field_type or "int" in field_type:
            field_questions = [
                inquirer.Text(field, message="Enter a value for " + field, validate=is_int)
            ]
        else:
            field_questions = [
                inquirer.Text(field, message="Enter a value for " + field)
            ]

        input_answers[field] = inquirer.prompt(field_questions).get(field)

    print(input_answers)

    insert_sql = "INSERT INTO " + "albums" + "(title, media, audio_format, run_length, label, artist, release_year, genre, country, runout, special_notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    values = (input_answers.get("title"), input_answers.get("media"), input_answers.get("audio_format"), input_answers.get("run_length"), input_answers.get("label"), input_answers.get("artist"), int(input_answers.get("release_year")), input_answers.get("genre"), input_answers.get("country"), input_answers.get("runout"), input_answers.get("special_notes"))

    cursor.execute(insert_sql, values)
    access_db.commit()

    print(cursor.rowcount, " details inserted.")
    print("done!")
    access_db.close()

main()