from sqlalchemy import create_engine
from sqlalchemy import (Column, String, Integer, Boolean, Date, ForeignKey,
    ForeignKeyConstraint, UniqueConstraint, CheckConstraint)
from sqlalchemy.orm import (DeclarativeBase, Mapped, relationship,
    composite, mapped_column)
from id_search import config
from sqlalchemy.engine import make_url
from pathlib import Path
from dataclasses import dataclass
import os

CID_PATTERN = '[A-Z][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]'

url = make_url(config['db-url'].get())
if url.drivername=='sqlite' and url.database:
    os.makedirs(Path(url.database).parent, exist_ok=True)
engine = create_engine(url)

def init_db():

    print("Initializing database...")
    Base.metadata.create_all(engine)

@dataclass
class PedigreeIndividual:
    pedigree: str
    individual: int

    def __post_init__(self):
        try:
            self.individual = int(self.individual)
        except (TypeError, ValueError):
            pass

class Base(DeclarativeBase):
    pass

class Center(Base):
    __tablename__ = 'center'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    investigator = Column(String, nullable=False)

    participants = relationship('RegisteredParticipant', backref='center')
    local_dna_samples = relationship('LocalDNASample', backref='center')

    __table_args__ = (
        UniqueConstraint('name', 'investigator', name='center_idx'),
    )

    def __repr__(self):
       return (f'Center(name={self.name}, investigator={self.investigator})')

class RegisteredParticipant(Base):
    __tablename__ = 'registered_participant'

    consortium_id = Column(String(14), primary_key=True)
    center_id = Column(Integer, ForeignKey('center.id'), nullable=False)
    fam_ind_id: Mapped[PedigreeIndividual] = (
        composite(mapped_column('family_id', nullable=True),
                  mapped_column('individual_id', nullable=True),
                  info={'type':PedigreeIndividual})
        )
    father = Column(Integer, nullable=True)
    mother = Column(Integer, nullable=True)
    spouse = Column(String(14), nullable=True)

    # Participant ID used for public releases (e.g., dbGaP)
    public_id = Column(Integer, nullable=True)
    # Family ID used for public releases
    public_family_id = Column(Integer, nullable=True)

    # Locally-assigned participant ID
    local_id = Column(String, nullable=True)
    # Locally-assigned pedigree and individual
    ped_ind_id: Mapped[PedigreeIndividual] = (
        composite(mapped_column('local_pedigree', nullable=True),
                  mapped_column('local_individual', nullable=True),
                  info={'type':PedigreeIndividual})
        )
    registration_date = Column(Date, nullable=True)
    yob = Column(Integer, nullable=True)
    sex = Column(String(7), nullable=True)
    affection = Column(String(10), nullable=True)
    diag = Column(String(13), nullable=True)
    control = Column(Boolean, nullable=True)
    withdrawn = Column(Boolean, default=False)

    aliases = relationship('Alias', backref='participant',
                           cascade='all, delete-orphan')
    lcls = relationship('RutgersLCL', backref='participant',
                        cascade='all, delete-orphan')
    dna_samples = relationship('DNASample', backref='participant',
                               cascade='all, delete-orphan')
    serum_samples = relationship('SerumSample', backref='participant',
                                 cascade='all, delete-orphan')
    local_dna_samples = relationship('LocalDNASample', backref='participant',
                                     cascade='all, delete-orphan')

    # Note: We use check constraints below instead of enums since SQLite
    # doesn't support enum fields.
    __table_args__ = (
        UniqueConstraint('family_id', 'individual_id', name='fam_ind_idx'),
        UniqueConstraint('public_id', name='pub_id_idx'),
        UniqueConstraint('center_id', 'local_id', name='local_id_idx'),
        UniqueConstraint('center_id', 'local_pedigree', 'local_individual',
                         name='ped_ind_idx'),
        CheckConstraint(f'consortium_id GLOB "{CID_PATTERN}"', name='cid'),
        CheckConstraint(f'spouse GLOB "{CID_PATTERN}"', name='sp'),
        CheckConstraint('(yob > 1900) AND (yob < 2050)'),
        CheckConstraint('sex IN ("Male","Female","Unknown")'),
        CheckConstraint('affection IN ("Affected","Unaffected","Unknown")'),
        CheckConstraint('diag IN ("CD","UC","Indeterminate","Unknown")'),
        CheckConstraint('((affection IN ("Unaffected","Unknown")) AND (diag IS NULL)) '
                        'OR ((affection IS NULL) AND (diag IS NULL)) '
                        'OR (affection = "Affected")', name='affect_diag'),
        CheckConstraint('((affection IN ("Affected","Unknown")) AND (control IS NULL)) '
                        'OR ((affection IS NULL) AND (control IS NULL)) '
                        'OR (affection = "Unaffected")', name='affect_ctrl')
    )

    def __repr__(self):
       return (f'RegisteredParticipant(consortium_id={self.consortium_id}, '
               f'center={self.center.name}, local_id={self.local_id}, '
               f'ped_ind_id={self.ped_ind_id}, '
               f'registration_date={self.registration_date})')

class Alias(Base):
    __tablename__ = 'alias'

    alias = Column(String(14), primary_key=True)
    consortium_id = Column(String(14), ForeignKey('registered_participant.consortium_id'),
                           nullable=False)

    __table_args__ = (
        CheckConstraint(f'alias GLOB "{CID_PATTERN}"', name='cid'),
    )

    def __repr__(self):
       return f'Alias(alias={self.alias}, consortium_id={self.consortium_id})'

class RutgersLCL(Base):
    __tablename__ = 'rutgers_lcl'

    niddk_no = Column(Integer, primary_key=True)
    knumber = Column(String(7), nullable=True)
    consortium_id = Column(String(14), ForeignKey('registered_participant.consortium_id'),
                           nullable=False)
    date_collected = Column(Date, nullable=True)

    __table_args__ = (
        CheckConstraint(f'niddk_no GLOB "[0-9][0-9][0-9][0-9][0-9][0-9]"', name='niddk_no_chk'),
        CheckConstraint(f'knumber GLOB "K[0-9][0-9][0-9][0-9][0-9]*"', name='knumber_chk')
    )

    def __repr__(self):
       return (f'RutgersLCL(consortium_id={self.consortium_id}, '
               f'niddk_no={self.niddk_no}, knumber={self.knumber}, '
               f'date_collected={self.date_collected})')

class DNASample(Base):
    __tablename__ = 'dna_sample'

    id = Column(String, primary_key=True)
    consortium_id = Column(String(14), ForeignKey('registered_participant.consortium_id'),
                           nullable=False)
    date_collected = Column(Date, nullable=True)

    def __repr__(self):
       return (f'DNASample(consortium_id={self.consortium_id}, '
               f'id={self.id}, date_collected={self.date_collected})')

class SerumSample(Base):
    __tablename__ = 'serum_sample'

    id = Column(String, primary_key=True)
    consortium_id = Column(String(14), ForeignKey('registered_participant.consortium_id'),
                           nullable=False)
    date_collected = Column(Date, nullable=True)

    def __repr__(self):
       return (f'SerumSample(consortium_id={self.consortium_id}, '
               f'id={self.id}, date_collected={self.date_collected})')

class LocalDNASample(Base):
    __tablename__ = 'local_dna_sample'

    id = Column(String, primary_key=True)
    center_id = Column(Integer, ForeignKey('center.id'), primary_key=True)
    consortium_id = Column(String(14), ForeignKey('registered_participant.consortium_id'),
                           nullable=False)
    date_collected = Column(Date, nullable=True)

    def __repr__(self):
       return (f'LocalDNASample(id={self.id}, center={self.participant.center.name}, '
               f'consortium_id={self.consortium_id}, '
               f'date_collected={self.date_collected})')

# List of ways to lookup an individual participant
Base.metadata.info = {
    'lookups': [RegisteredParticipant.consortium_id,
                RegisteredParticipant.local_id,
                RegisteredParticipant.ped_ind_id,
                RutgersLCL.niddk_no,
                RutgersLCL.knumber,
                DNASample.id,
                SerumSample.id,
                LocalDNASample.id]
}
