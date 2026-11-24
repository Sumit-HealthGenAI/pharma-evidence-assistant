import requests

url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

params = {
    "query": "drug solubility",
    "format": "json",
    "pageSize": 5
}

try:
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

except requests.exceptions.JSONDecodeError:
    print("The server returned an invalid response.")
    raise SystemExit(1)

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    raise SystemExit(1)

results = data["resultList"]["result"]


def normalize_title(title):
    return title.lower().strip().rstrip(".")


def duplicate_papers(papers):
    unique_papers = []
    confirmed_duplicates = []
    possible_duplicates = []
    identifier_conflicts = []

    seen_dois = set()
    seen_titles = set()
    seen_pmids = set()

    doi_to_pmid = {}
    pmid_to_doi = {}

    for paper in papers:
        doi = paper.get("doi")
        pmid = paper.get("pmid")
        title = normalize_title(paper.get("title", ""))

        if doi:
            doi = doi.strip().lower()

        if pmid:
            pmid = str(pmid).strip()

        # Confirmed duplicate by DOI
        if doi and doi in seen_dois:
            existing_pmid = doi_to_pmid.get(doi)

            if existing_pmid and pmid and existing_pmid != pmid:
                identifier_conflicts.append(paper)
            else:
                confirmed_duplicates.append(paper)

            continue

        # PMID already seen
        if pmid and pmid in seen_pmids:
            existing_doi = pmid_to_doi.get(pmid)

            if existing_doi and doi and existing_doi != doi:
                identifier_conflicts.append(paper)
            else:
                confirmed_duplicates.append(paper)

            continue

        # Track new DOI and PMID
        if doi:
            seen_dois.add(doi)
            doi_to_pmid[doi] = pmid

        if pmid:
            seen_pmids.add(pmid)
            pmid_to_doi[pmid] = doi

        # Without a DOI, a matching title is a possible duplicate.
        if not doi and title:
            if title in seen_titles:
                possible_duplicates.append(paper)
                continue
            seen_titles.add(title)
        elif title:
            seen_titles.add(title)

        unique_papers.append(paper)

    return unique_papers, confirmed_duplicates, possible_duplicates, identifier_conflicts


# Test title normalization
print(normalize_title("Drug Solubility Research."))
print(normalize_title("  DRUG SOLUBILITY RESEARCH  "))

# Process API results
unique_papers, confirmed_duplicates, possible_duplicates, identifier_conflicts = duplicate_papers(results)

print("\nOriginal records:", len(results))
print("Unique records:", len(unique_papers))
print("Confirmed duplicates:", len(confirmed_duplicates))
print("Possible duplicates:", len(possible_duplicates))
print("Identifier conflicts:", len(identifier_conflicts))


# Controlled test data
test_papers = [
    # Same DOI and same PMID
    {"doi": "10.1000/a", "pmid": "101", "title": "Paper A"},
    {"doi": "10.1000/a", "pmid": "101", "title": "Paper A Copy"},

    # Same DOI, different PMID
    {"doi": "10.2000/b", "pmid": "202", "title": "Paper B"},
    {"doi": "10.2000/b", "pmid": "203", "title": "Paper B Copy"},

    # Same PMID, different DOI
    {"doi": "10.3000/c", "pmid": "303", "title": "Paper C"},
    {"doi": "10.4000/d", "pmid": "303", "title": "Paper D"},

    # None doi or pmid
    {"doi": None, "pmid": None, "title": "Drug Solubility Research"},
    {"doi": None, "pmid": None, "title": "  DRUG SOLUBILITY RESEARCH. "}
]

unique, confirmed, possible, conflicts = duplicate_papers(test_papers)

print("\n--- Test Results ---")
print("Unique:", len(unique))
print("Confirmed:", len(confirmed))
print("Possible:", len(possible))
print("Identifier conflicts:", len(conflicts))


# Display unique papers from API
for paper in unique_papers:
    print("\nTitle:", paper.get("title", "Unavailable"))
    print("Authors:", paper.get("authorString", "Unavailable"))
    print("Journal:", paper.get("journalTitle", "Unavailable"))
    print(
        "Year:",
        paper.get("pubYear")
        or paper.get("firstPublicationDate", "Unavailable")
    )
    print("DOI:", paper.get("doi", "Unavailable"))
    print("PMID:", paper.get("pmid", "Unavailable"))