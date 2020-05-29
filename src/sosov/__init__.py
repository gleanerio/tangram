"""

"""
import os
import re
import urllib.parse
import rdflib
import logging
from urllib.parse import urljoin

__all__ = ["verify", ]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

SCHEMA_ORG_URL = "https://schema.org/version/latest/schema.nq"
SCHEMA_ORG = "https://schema.org/"
SO_PREFIX = "SO"
# Match variants of "https://schema.org/"
RE_SO = re.compile(r"^http.{0,1}://schema\.org/{0,1}")
SCHEMA_DEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources/data/"))


# Mapping file name extension to rdflib parser
FORMAT_MAP = {
    ".ttl":"turtle",
    ".json":"json-ld",
    ".jsonld":"json-ld",
    ".js":"json-ld",
    ".html":"rdfa",
    ".n3":"n3",
    ".nq":"nquads",
}



def filenameFromUrl(url):
    parts = urllib.parse.urlparse(urllib.parse.unquote(url))
    filename = os.path.basename(parts.path)
    if len(filename) < 1:
        # construct from host + path
        path = parts.path.strip("/")
        return f"{parts.netloc}-{path.replace('/','_')}"
    filename = filename.replace(" ", "_")
    return "".join(
        [c for c in filename if c.isalpha() or c.isdigit() or c in (".", "~", "-", "_")]
    ).rstrip()


def downloadRDF(url, dest_name, src_format="turtle", dest_format="turtle"):
    g = rdflib.ConjunctiveGraph()
    try:
        g.load(url, format=src_format)
        encoding = "utf-8"
        # Note that rdflib nt format does not support setting the encoding, it is always ascii.
        g.serialize(destination=dest_name, format=dest_format, encoding="utf-8")
        return dest_name
    except Exception as e:
        logging.error(e)
    return None


def guessGraphFormat(filename):
    root,ext = os.path.splitext(filename)
    ext = ext.lower()
    return FORMAT_MAP.get(ext, None)

def expandQName(g, identifier):
    prefix, _id = rdflib.namespace.split_uri(identifier)
    ns = g.store.namespace(prefix.replace(":", "", 1))
    if not ns is None:
        return rdflib.URIRef(urljoin(ns, _id))
    return rdflib.URIRef(identifier)

def graphFromText(graph_text, publicID=None, format="json-ld"):
    g = rdflib.ConjunctiveGraph()
    g.parse(data=graph_text, format=format, publicID=publicID)
    return g

def loadGraph(file_path, format=None, publicID=None):
    if format is None:
        format = guessGraphFormat(file_path)
    g = rdflib.ConjunctiveGraph()
    g.parse(file_path, format=format, publicID=publicID)
    return g


def _normalizeTerm(t):
    """
    Hack the URIRefs to normalize schema.org to use "https://schema.org/"

    This is an ugly solution to the problem of variable representations of
    the schema.org namespace in the wild.

    Args:
        t: Graph term to process

    Returns:
        Graph term normalized to namespace <https://schema.org/>
    """
    if isinstance(t, rdflib.URIRef):
        v = str(t)
        so_match = RE_SO.match(v)
        if so_match is not None:
            v = v[so_match.end() :]
            if v[-1] == "/":
                v = v[:-1]
            return rdflib.URIRef(v, SCHEMA_ORG)
    return t


def setSchemaOrgNamespace(g):
    """Return g with schema.org namespace adjsuted to "https://schema.org/"
    """
    ns = rdflib.namespace.NamespaceManager(g)
    ns.bind(SO_PREFIX, SCHEMA_ORG, override=True, replace=True)
    g2 = rdflib.ConjunctiveGraph()
    g2.namespace_manager = ns
    for s, p, o in g:
        trip = [s, p, o]
        for i, t in enumerate(trip):
            trip[i] = _normalizeTerm(t)
        g2.add(trip)
    return g2


def downloadSchemaOrg(dest_path, dest_name, url=SCHEMA_ORG_URL):
    """
    Download the schema.org graph and save with namespace adjusted to "https://schema.org/".

    """
    src_format = "nquads"
    dest_format = "turtle"
    g = rdflib.ConjunctiveGraph()
    g.parse(url, format=src_format)
    g2 = setSchemaOrgNamespace(g)
    s, p, o, q = next(g.quads())
    version = str(q.identifier).split("#")[-1]
    logger.info("Schema.org version = %s", version)
    create_link = False
    if dest_name is None:
        dest_name = f"schema.org_v{version}.ttl"
        create_link = True
    full_path = os.path.join(os.path.abspath(dest_path), dest_name)
    g2.serialize(full_path, format=dest_format)
    if create_link:
        # create a symlink for the file
        dest_path = os.path.join(os.path.dirname(full_path),"schema.org.ttl")
        logger.info("Creating symlink %s -> %s", full_path, dest_path)
        os.symlink(full_path, dest_path)
    return full_path


