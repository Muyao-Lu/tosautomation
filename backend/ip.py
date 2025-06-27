import datetime
from sqlmodel import SQLModel, Field, create_engine, select, Session
from sqlalchemy.exc import NoResultFound
import os

class IpModel(SQLModel, table=True):
    id: int | None = Field(None, primary_key=True)
    ip: str = Field(None, index=True)
    last_call: datetime.datetime

class IpController:
    def __init__(self, time_limit: float | int = 20):
        self.time_limit = time_limit
        self.DATABASE_URL = "postgresql://postgres.kvzyyqxeawybeukfybkq:{key}@aws-0-ca-central-1.pooler.supabase.com:6543/postgres".format(key=os.environ["SUPABASE_KEY"])
        self.engine = create_engine(self.DATABASE_URL)
        SQLModel.metadata.create_all(self.engine)

    def add_ip(self, ip):
        """
            Adds an ip and time to the database
        """
        with Session(self.engine) as session:
            try:
                self.get_ip(ip)
            except NoResultFound:
                session.add(IpModel(ip=ip, last_call=datetime.datetime.now()))
                session.commit()

    def get_ip(self, ip):
        """
           Gets the row with the corresponding ip from the database
        """
        with Session(self.engine) as session:
            condition = select(IpModel).where(IpModel.ip == ip)
            results = session.exec(condition)
            return results.one()

    def update_ip(self, ip):
        """
            Updates IP information
        """
        with Session(self.engine) as session:
            entry = self.get_ip(ip)
            entry.last_call = datetime.datetime.now()
            session.add(entry)
            session.commit()

    def check_request_time_validity(self, ip):
        """
            Checks time validity of an API Request
        """
        try:
            entry = self.get_ip(ip)
            if (datetime.datetime.now() - entry.last_call).total_seconds() > self.time_limit:
                self.update_ip(ip)
                return True
            else:
                return False
        except NoResultFound:
            self.add_ip(ip)
            return True

