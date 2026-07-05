from datetime import datetime, timezone


# UTC naive, substituindo datetime.utcnow() deprecated no 3.12 (RP-10 / AP-08).
# Mantém naive para permanecer compatível com as datas já persistidas.
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)
