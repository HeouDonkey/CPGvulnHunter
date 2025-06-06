import logging
from py2joern.cpgs.cpg import CPG
from src.py2joern.hunt import Hunt

def run():

    logging.basicConfig(
        level=logging.DEBUG,  # 可选: DEBUG/INFO/WARNING/ERROR/CRITICAL
        format='[%(asctime)s] %(levelname)s %(message)s'
    )
    test_src = "/home/nstl/data/vuln_hunter/py2joern/test/test_case/test1"
    cpg = CPG(test_src)
    