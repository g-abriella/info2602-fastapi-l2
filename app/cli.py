import typer
from typing import Annotated
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command()
def initialize():
    """
    Creates a database and defines the schema.
    """
    with get_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        bob = User('bob', 'bob@mail.com', 'bobpass') # Create a new user (in memory)
        db.add(bob) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(bob) # Update the user (we use this to get the ID from the db)
        print("Database Initialized")

@cli.command()
def get_user(
    username: Annotated[str, typer.Argument(help="A unique string to identify a user")]
):
    """
    Finds and prints a user given a username.
    """
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    """
    Lists all users in the database.
    """
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)


@cli.command()
def change_email(
    username: Annotated[str, typer.Argument(help="A unique string to identify a user")],
    new_email:Annotated[str, typer.Argument(help="An email address different from the current")]
    ):
    """
    Updates a user's email field.
    """
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command()
def create_user(
    username: Annotated[str, typer.Argument(help="A unique string to identify a user")],
    email: Annotated[str, typer.Argument(help="An email address to contact a user")],
    password: Annotated[str, typer.Argument(help="A secret string to access a user record")]
    ):
    """
    Creates a new user record.
    """
    with get_session() as db: # Get a connection to the database
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback() #let the database undo any previous steps of a transaction
            #print(e.orig) #optionally print the error raised by the database
            print("Username or email already taken!") #give the user a useful message
        else:
            print(newuser) # print the newly created user

@cli.command()
def delete_user(
    username: Annotated[str, typer.Argument(help="A unique string to identify a user")]
):
    """
    Deletes a user record.
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')


# --> Exercises

# Exercise 1
# find a user using a partial match of their email OR username

@cli.command()
def get_user_from_partial(
    query: Annotated[str, typer.Argument(help="Username or email")]
):
    """
    Finds and prints a user given a partial match of their email or username.
    """
    with get_session() as db:
        matching_users = db.exec(
            select(User).where(
                User.email.ilike(f'%{query}%') |
                User.username.ilike(f'%{query}%')
            )
        ).all()
        if not matching_users:
            print(f"No matches for '{query}'.")
            return
        else:
            for user in matching_users:
                print(user)

# Exercise 2
# list the first N users of the database to be used by a paginated table

@cli.command()
def get_first_n_users(
    limit: Annotated[int, typer.Argument(help="Number of records to return")] = 10,
    offset: Annotated[int, typer.Argument(help="Number of records to skip")] = 0
):
    """
    Lists a specified number of users. 
    """
    with get_session() as db:
        users = db.exec(
            select(User)
            .offset(offset)
            .limit(limit)
        ).all()

        if not users:
            print("No users found.")
            return
        
        for user in users:
            print(user)


if __name__ == "__main__":
    cli()