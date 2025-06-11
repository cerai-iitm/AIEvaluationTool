#/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Sudarsun S
@file: connection.py
@brief: This module provides the database connection and session management for SQLAlchemy.
@details: It includes functions to create a database engine, session, and manage the connection lifecycle.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy import select
from tables import Prompts, Languages, Domains

# Define the MariaDB engine using MariaDB Connector/Python

engine = create_engine("mariadb+mariadbconnector://root:ATmega32*@127.0.0.1:3306/aieval", echo=True, pool_size=5, max_overflow=10)

# Create a base class for declarative models
Base = declarative_base()
Base.metadata.create_all(engine)

# Create a scoped session factory
Session = scoped_session(sessionmaker(bind=engine))




languages = Session.query(Languages).all()  # Example query to test the connection
for lang in languages:
    print(f"Language id: {lang.lang_id}, Name: {lang.lang_name}")

for domain in Session.query(Domains).all():
    print(f"Domain id: {domain.domain_id}, Name: {domain.domain_name}")

result = Session.query(Languages).filter(Languages.lang_name=="tamil").one_or_none()
if result is not None:
    print(f"Language id: {result.lang_id}, Name: {result.lang_name}")

sql = select(Languages).where(Languages.lang_name=="tamil")
result = Session.execute(sql).scalar_one_or_none()
if result is not None:
    print(f"Language id: {result.lang_id}, Name: {result.lang_name}")

result  = Session.scalar(sql)
if result is not None:
    print(f"Language id: {result.lang_id}, Name: {result.lang_name}")

result  = Session.scalars(sql).one_or_none()
if result is not None:
    print(f"Language id: {result.lang_id}, Name: {result.lang_name}")

# insert a new prompt
newPrompt = Prompts(prompt_string="What is AI?", system_prompt="Answer in one sentence.", lang_id=result.lang_id)
#Session.add(newPrompt)
#Session.commit()

# join Prompts and Languages tables to get prompts in Tamil
sql = select(Prompts).select_from(Languages).where(Languages.lang_name=="tamil").where(Languages.lang_id == Prompts.lang_id)
result = Session.execute(sql).scalars().all()
for prompt in result:
    print(f"Prompt id: {prompt.prompt_id}, Prompt: {prompt.prompt_string}, Language: {prompt.lang_id}")


