# CampusNet architecture

```text
Student device / supplicant → access point → FreeRADIUS
                                      ↓
                           safe structured event log
                                      ↓
                         FastAPI ingestion worker → SQLite
                                      ↓
                              Next.js dashboard
```

The prototype uses a local FreeRADIUS demo identity source. In production, the authenticator, identity provider, VLAN policy, DHCP/DNS, firewall, roaming, certificate lifecycle, and monitoring require institutional network design and approval. CampusNet does not collect Google passwords or claim to be a student directory.

