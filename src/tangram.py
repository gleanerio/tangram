"""
Script to perform SOSO verification tasks.

"""
import os
import sys
import logging
import time
import click
import sosov.verify

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "FATAL": logging.CRITICAL,
    "CRITICAL": logging.CRITICAL,
}
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
LOG_FORMAT = "%(asctime)s %(name)s:%(levelname)s: %(message)s"


def getLogger():
    return logging.getLogger("soso")


def fileChanged(file_name, t0=0):
    t1 = os.stat(file_name).st_mtime
    return t1 > t0, t1


@click.group()
@click.option(
    "--verbosity", default="INFO", help="Specify logging level", show_default=True
)
def main(verbosity):
    """
    Utility operations for SOSO verification tools
    """
    verbosity = verbosity.upper()
    logging.basicConfig(
        level=LOG_LEVELS.get(verbosity, logging.INFO),
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    if verbosity not in LOG_LEVELS.keys():
        L = getLogger()
        L.warning("%s is not a log level, set to INFO", verbosity)


# == download operation ==
@main.command()
@click.option(
    "--dest_path",
    help=f"Target folder for schema.org graph",
    default=sosov.SCHEMA_DEST_PATH,
    show_default=True,
)
@click.option(
    "--dest_name",
    help="File name for downloaded graph",
    default=None,
    show_default=True,
)
def download(dest_path, dest_name):
    """
    Download the schema.org graph and save with namespace adjusted.

    The schema.org rdf document enables evaluation of class hierarchy during
    the verification process. This script retrieves the current version of the
    complete schema.org graph and updates the namespace to use `https://` rather
    than `http://` as per the guidelines.
    """
    L = getLogger()
    full_path = sosov.downloadSchemaOrg(dest_path, dest_name)
    L.info("Downloaded to: %s", full_path)


# == verfiy operation ==
@main.command()
@click.option("--data-file", "-d", help="Data shape to be verified", required=True)
@click.option(
    "--data-format",
    "-f",
    default="json-ld",
    help="RDFLIB parser format for data shape",
    show_default=True,
)
@click.option("--shacl-file", "-s", help="SHACL shape to evaluate", required=True)
@click.option(
    "--schema-org",
    help="Path to schema.org turtle file",
    default=os.path.abspath(os.path.join(sosov.SCHEMA_DEST_PATH, "schema.org.ttl")),
    show_default=True,
)
@click.option(
    "--watch",
    "-w",
    help="Watch sources and re-verify on change, ctrl-c to stop",
    default=False,
    show_default=True,
    is_flag=True,
)
@click.option(
    "--out-format", "-o", help="Output format", default="text", show_default=True,
)
def verify(data_file, data_format, shacl_file, schema_org, watch, out_format):
    """
    Verify a data shape against one or more shacl shapes.
    Args:
        data_file: Path to data shape file
        data_format: format of datashape, see rdflib
        shacl_file: Path to shacl file in turtle
        schema_org: Path to schema.org vocabulary in turtle
        watch: (boolean) Watch data or shape file for changes and recompute
        out_format: format for output, "text" or rdflib format

    Returns:
        integer status
    """
    L = getLogger()
    if not os.path.exists(data_file):
        L.error("Data shape not found: %s", data_file)
        return 1
    if not os.path.exists(shacl_file):
        L.error("SHACL shape not found: %s", shacl_file)
        return 1
    data_graph = None
    data_mtime = 0
    shacl_graph = None
    shacl_mtime = 0
    schema_graph = None
    if not os.path.exists(schema_org):
        L.warning(
            "Schema.org graph not present, tests of class hierarchy will be unreliable."
        )
    else:
        L.info("Loading schema.org graph: %s", schema_org)
        schema_graph = sosov.loadGraph(schema_org)
    out_format = out_format.lower()
    more_work = True
    processed = False
    if watch:
        L.info("Watching Data and SHACL sources for changes. Ctrl-C to exit.")
    while more_work:
        try:
            # check files for modification and load if changed
            data_changed, data_mtime = fileChanged(data_file, data_mtime)
            if data_changed:
                L.info("Loading data source: %s", data_file)
                data_graph = None
                try:
                    data_graph = sosov.loadGraph(data_file, format=data_format)
                    processed = False
                except Exception as e:
                    L.error("Could not load datagraph: %s", e)

            shacl_changed, shacl_mtime = fileChanged(shacl_file, shacl_mtime)
            if shacl_changed:
                L.info("Loading SHACL source: %s", shacl_file)
                shacl_graph = None
                try:
                    shacl_graph = sosov.loadGraph(shacl_file, format="turtle")
                    processed = False
                except Exception as e:
                    L.error("Could not load SHACL shape: %s", e)

            # Run the verification if new content is available
            if not processed and data_graph is not None and shacl_graph is not None:
                try:
                    L.info("Evaluating SHACL constraints...")
                    conforms, result_graph, result_text = sosov.verify.validateSHACL(
                        data_graph, shacl_graph=shacl_graph, ont_graph=schema_graph
                    )
                    if out_format == "text":
                        print("====")
                        print(result_text)
                    else:
                        print(
                            result_graph.serialize(format=out_format, indent=2).decode()
                        )
                except Exception as e:
                    L.error(e)
                processed = True
            more_work = watch
            time.sleep(0.618)

        except KeyboardInterrupt as e:
            more_work = False
            L.info("Exiting...")
            data_graph = None
            shacl_graph = None
            schema_graph = None
    return 0


if __name__ == "__main__":
    sys.exit(main())
