from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
)
from pysnmp.hlapi.v3arch.asyncio.cmdgen import getCmd

def snmp_scan(ip: str, community: str = "public"):
    oid_list = {
        "sysDescr": "1.3.6.1.2.1.1.1.0",
        "sysName": "1.3.6.1.2.1.1.5.0",
        "sysUpTime": "1.3.6.1.2.1.1.3.0",
    }

    result = {}

    for key, oid in oid_list.items():
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(community, mpModel=1),
                UdpTransportTarget((ip, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )

            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

            if errorIndication:
                result[key] = f"Erro: {errorIndication}"
            elif errorStatus:
                result[key] = f"{errorStatus.prettyPrint()}"
            else:
                for varBind in varBinds:
                    result[key] = f"{varBind[1]}"

        except Exception as e:
            result[key] = f"Erro: {e}"

    return result
