import logging

# Logging estruturado e centralizado (RP-08 corrige AP-11).
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)


def get_logger(name):
    return logging.getLogger(name)
