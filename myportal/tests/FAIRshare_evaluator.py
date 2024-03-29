import requests

# Get FAIRShare Tests

# headers = { 'presqt-email-opt-in': 'False'}
r = requests.get('https://presqt-prod.crc.nd.edu/api_v1/services/fairshare/evaluator')
r.json()
# FAIRShare example through PresQT endpoint

json = {
    "resource_id": "10.17605/OSF.IO/EGGS12",
    "tests": [1, 2]
}
headers = {'presqt-email-opt-in': 'False'}
r = requests.post('https://presqt-prod.crc.nd.edu/api_v1/services/fairshare/evaluator', headers=headers, json=json)
r.json()

# Direct Evaluation through FAIR Maturity Indicators and Tools
# Resources and guidelines to assess the FAIRness of a digital resource.

# json = {"subject": "10.4211/hs.9c4a6e2090924d97955a197fea67fd72"}
# r = requests.post('https://fair-tests.137.120.31.101.nip.io/tests/gen2_unique_identifier', json=json)
# r.json()
r = requests.get('http://presqt-prod.crc.nd.edu/api_v1/services/fairshare/evaluator/')
r.json()
presQT_tests = {'Unique Identifier': 'https://w3id.org/FAIR_Tests/tests/gen2_unique_identifier',
                'Identifier persistence': 'https://w3id.org/FAIR_Tests/tests/gen2_metadata_identifier_persistence',
                'Structured metadata': 'https://w3id.org/FAIR_Tests/tests/gen2_structured_metadata',
                'Grounded metadata': 'https://w3id.org/FAIR_Tests/tests/gen2_grounded_metadata',
                'Data Identifier Explicitly in Metadata': 'https://w3id.org/FAIR_Tests/tests/gen2_data_identifier_in_metadata',
                'Searchable in major search engine': 'https://w3id.org/FAIR_Tests/tests/gen2_searchable',
                'Uses open free protocol for metadata retrieval': 'https://w3id.org/FAIR_Tests/tests/gen2_metadata_protocol',
                'Metadata persistence': 'https://w3id.org/FAIR_Tests/tests/gen2_metadata_persistence',
                'Data Knowledge Representation Language (strong)': 'https://w3id.org/FAIR_Tests/tests/gen2_data_kr_language_strong',
                'Metadata uses FAIR vocabularies (strong)': 'https://w3id.org/FAIR_Tests/tests/gen2_metadata_uses_fair_vocabularies_strong',
                'Metadata Includes License (weak)': 'https://w3id.org/FAIR_Tests/tests/gen2_metadata_includes_license_weak'}
subject = 'http://localhost:8002/schema-org-index/resource/a7d9795b-e799-4761-9289-a8643f06bdb0'
# subject = '10.5072/zenodo.926573'


def runFAIRMITest(test, url, subject):
    r = requests.post(url, json={'subject': subject})
    passed = bool(r.json()[0]['http://semanticscience.org/resource/SIO_000300'][0]['@value'])
    print('%s: %s' % (test, str(passed)))
    return passed


for test, url in presQT_tests.items():
    runFAIRMITest(test, url, subject)
