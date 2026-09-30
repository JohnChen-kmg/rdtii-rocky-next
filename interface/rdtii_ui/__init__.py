"""RDTII Rocky interface: a standard-library web front over the three pipeline stages.

Four tabs (Scraping, Extraction, Mapping, Other). The interface never imports stage code and never
edits anything under stages/. It launches stage command lines as subprocesses and reads what they write.
"""

__version__ = "0.1.0"
