from logging import basicConfig, info, error, INFO
from pathlib import Path
from argparse import ArgumentParser, Namespace
from datetime import datetime, timedelta, UTC
from typing import Dict
from json import dumps, loads
from urllib.request import Request, urlopen

SOLIDBENCH_QUERY_SEP = "\n\n"
SOLIDBENCH_QUERY_EXT = ".sparql"
STANDARD_QUERY_EXT = ".rq"


class QueryNamespace(Namespace):
    output: Path
    queries: Path
    endpoint: str


def setup_logging() -> None:
    basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=INFO,
    )


def parse_args() -> QueryNamespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        help="The output path for results",
        default=Path(__file__).parent.parent.joinpath("results"),
    )
    parser.add_argument(
        "--queries",
        type=Path,
        help="Path to the SolidBench queries",
        default=Path(__file__).parent.parent.joinpath("out-queries"),
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        help="The SPARQL endpoint URI",
        default="http://localhost:3030/sparql",
    )
    args = parser.parse_args()
    return args


def load_queries(path: Path) -> Dict[str, str]:
    queries_by_id: Dict[str, str] = {}
    info(f"Loading queries from {path}")
    for fp in path.iterdir():
        if fp.name.endswith(SOLIDBENCH_QUERY_EXT):
            template_id = fp.name.removesuffix(SOLIDBENCH_QUERY_EXT)
            with open(fp, "r") as template_file:
                queries = list(
                    query.strip()
                    for query in template_file.read().split(SOLIDBENCH_QUERY_SEP)
                    if len(query.strip()) > 0
                )
            for query_id in range(0, len(queries)):
                queries_by_id[f"{template_id}-{query_id + 1}"] = queries[query_id]
    info(f"Loaded {len(queries_by_id)} queries")
    return queries_by_id


def execute_query(endpoint: str, query: str) -> dict:
    request = Request(
        url=endpoint,
        data=query.encode(),
        headers={
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/sparql-query",
        },
        method="POST",
    )
    with urlopen(url=request, timeout=None) as response:
        response_text = response.read().decode().strip()
    try:
        return loads(response_text)
    except Exception:
        raise Exception(response_text)


def save_query_data(
    path: Path,
    id: str,
    query: str,
    result: dict,
    error: Exception | None,
    time: timedelta,
) -> None:
    info(f"Saving data in {path} for query {id}")
    query_path = path.joinpath(f"{id}.{STANDARD_QUERY_EXT}")
    result_path = path.joinpath(f"{id}.json")
    metadata_path = path.joinpath(f"{id}-meta.json")
    metadata = {
        "time_seconds": time.total_seconds(),
        "error": str(error) if error else None,
        "success": False if error else True,
        "results": len(result["results"]["bindings"]) if "results" in result else 0,
    }
    with open(query_path, "w") as query_file:
        query_file.write(query + "\n")
    with open(result_path, "w") as result_file:
        result_file.write(
            dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
        )
    with open(metadata_path, "w") as metadata_file:
        metadata_file.write(
            dumps(metadata, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
        )


def run_queries(queries: Dict[str, str], endpoint: str, output_path: Path) -> None:
    info(f"Running queries against {endpoint}")
    all_start = datetime.now(tz=UTC)
    for id, query in queries.items():
        info(f"Running query {id}")
        start_time = datetime.now(tz=UTC)
        try:
            result = execute_query(endpoint, query)
            result_error = None
        except Exception as ex:
            error(f"Failed to execute query")
            result = {}
            result_error = ex
        end_time = datetime.now(tz=UTC)
        save_query_data(
            path=output_path,
            id=id,
            query=query,
            result=result,
            error=result_error,
            time=(end_time - start_time),
        )
    all_end = datetime.now(tz=UTC)
    all_duration = round((all_end - all_start).total_seconds())
    info(f"Finished running all queries in ~{all_duration} seconds")


if __name__ == "__main__":
    setup_logging()
    args = parse_args()
    queries = load_queries(args.queries)
    run_queries(queries=queries, endpoint=args.endpoint, output_path=args.output)
