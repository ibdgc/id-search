"""Functions supporting ibdgc-db tool"""

from id_search import db
from sqlalchemy.orm import Session, attributes
from sqlalchemy.exc import OperationalError, NoResultFound
from sqlalchemy.inspection import inspect
from sqlalchemy import select
import pandas as pd
from pprint import pprint
import re

lookups = {'all': []}
for idx in db.Base.metadata.info['lookups']:
    k = f'{idx.parent.persist_selectable}.{idx.key}'
    lookups[k] = [(idx.parent.entity, idx)]
    # Include aliases when looking up by Consortium ID
    if idx is db.RegisteredParticipant.consortium_id:
        lookups[k] += [(db.Alias, db.Alias.alias)]
    lookups['all'] += lookups[k]
# Push 'all' to bottom of list for use in CLI help message
lookups['all'] = lookups.pop('all')


def get_centers():
    """Return list of center names."""

    centers = []
    with Session(db.engine) as session:
        stmt = select(db.Center)
        try:
            for center in session.scalars(stmt):
                centers.append(center.name)
        except OperationalError:
            pass

    return centers


def get_participants(value, keys, session, center=None):
    """
    Return participant(s) based on a single identifier,
    optionally within center.
    """

    results = []
    for table, column in keys:
        if column.info.get('type') == db.PedigreeIndividual:
            tokens = re.split(
                '\s*,\s*|\s*-\s*|\s*\.\s*|\s+',
                value,
                maxsplit=1
            )
            if len(tokens) < 2:
                continue
            else:
                v = db.PedigreeIndividual(*tokens)
        else:
            v = value

        if center:
            center_id = session.scalar(
                select(db.Center)
                .where(db.Center.name == center)
            ).id
            stmt = select(table).where(
                column == v,
                table.center_id == center_id
            )
        else:
            stmt = select(table).where(column == v)

        for item in session.scalars(stmt):
            if isinstance(item, db.RegisteredParticipant):
                results.append(item)
            else:
                results.append(item.participant)

    return set(results)


def extract_participant_data(participant):
    """Extract data from participant object for DataFrame display."""
    # Force loading of lazy attributes
    for attr in attributes.instance_state(participant).unloaded:
        getattr(participant, attr)

    return {
        k: getattr(participant, k)
        for k in vars(participant)
        if k != '_sa_instance_state'
    }


def display_participant(participant):
    """Print participant info."""

    # Force loading of lazy attributes so we can print them
    for attr in attributes.instance_state(participant).unloaded:
        getattr(participant, attr)

    pprint({
        k: v
        for k, v in vars(participant).items()
        if k != '_sa_instance_state'
    })


def _agg_cids(series):
    """Aggregate Consortium IDs from a series of registered participants."""

    unique_cids = set()
    for resultset in series:
        for participant in resultset:
            unique_cids.add(participant.consortium_id)

    unique_cids = list(unique_cids)
    if len(unique_cids) < 2:
        result = unique_cids[0] if len(unique_cids) else None
    else:
        result = sorted(unique_cids)

    return result


def batch_query(values, keys=None, center=None):
    """
    Query participants based on a series or data frame of identifiers.

    Parameters
    ----------
    values : DataFrame or Series
        Each row represents a single individual or sample, identified by one or
        more identifiers in the columns.
    keys : str or list-like of str, optional
        Key(s) for querying data model. If list, length must equal the number
        of columns in values.
    center : str, optional
        Restrict all queries to a single center.

    Returns
    -------
    Series
        Consortium ID(s) (str or list of str) found for each row in values.
    """

    values = pd.DataFrame(values).fillna('')
    if keys is None:
        keys = 'all'
    if isinstance(keys, str):
        keys = [keys]*values.shape[1]
    if len(keys) != values.shape[1]:
        raise Exception(
            'Number of keys does not match number of columns in values'
        )

    df = pd.DataFrame()
    with Session(db.engine) as session:
        for column, key in zip(values.columns, keys):
            df[f'{column}.{key}'] = values[column].apply(get_participants,
                                                         keys=lookups[key],
                                                         session=session,
                                                         center=center)

        return df.aggregate(_agg_cids, axis=1)


def make_primary(alias):
    """Make alias the primary Consortium ID for that participant."""

    with Session(db.engine) as session, session.begin():
        try:
            p = session.scalars(
                select(db.Alias)
                .where(db.Alias.alias == alias)
            ).one().participant
        except NoResultFound:
            raise Exception(f'Alias "{alias}" not found')

        props = {k: v for k, v in vars(p).items()
                 if k not in ['_sa_instance_state', 'consortium_id', 'center']}
        relations = [r for r in
                     inspect(db.RegisteredParticipant).relationships.items()
                     if r[0] not in ['aliases', 'center']]

        new = db.RegisteredParticipant(consortium_id=alias, center=p.center)
        session.add(new)

        aliases = []
        for a in p.aliases:
            if a.alias != alias:
                aliases.append(a)
        new.aliases = aliases + [db.Alias(alias=p.consortium_id)]

        for r in relations:
            setattr(new, r[0], getattr(p, r[0]))

        session.delete(p)
        session.flush()

        for k, v in props.items():
            setattr(new, k, v)


def add_alias(consortium_id, alias):
    """Add alias for existing registered participant."""

    with Session(db.engine) as session, session.begin():
        try:
            p = (session.scalars(
                select(db.RegisteredParticipant)
                .where(db.RegisteredParticipant.consortium_id == consortium_id)
            ).one())
        except NoResultFound:
            raise Exception(f'Participant "{consortium_id}" not found')

        if get_participants(alias, [(db.RegisteredParticipant,
                                     db.RegisteredParticipant.consortium_id),
                                    (db.Alias, db.Alias.alias)], session):
            raise Exception(f'Consortium ID "{alias}" already in use')
        else:
            p.aliases.append(db.Alias(alias=alias))
