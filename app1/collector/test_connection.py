import os
import obd

OBD_PORT = os.getenv("OBD_PORT", None)

connection = obd.OBD(portstr=OBD_PORT, fast=False, timeout=10)

print("Conectado:", connection.is_connected())

if connection.is_connected():
    rpm = connection.query(obd.commands.RPM)
    temp = connection.query(obd.commands.COOLANT_TEMP)
    volt = connection.query(obd.commands.ELM_VOLTAGE)

    print("RPM:", rpm.value if not rpm.is_null() else None)
    print("TEMP:", temp.value if not temp.is_null() else None)
    print("VOLT:", volt.value if not volt.is_null() else None)


# probar: python collector/test_connection.py
