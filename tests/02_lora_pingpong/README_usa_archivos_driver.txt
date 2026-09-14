# Prueba rápida de conexión
def test_connection(lora):
    version = lora.read_reg(0x42)
    if version == 0x12:
        print("✅ Conexión exitosa: SX1278 detectado (Versión 0x12)")
    else:
        print(f"❌ Error: Se leyó 0x{version:02x}, se esperaba 0x12. Revisa el cableado.")

# Ejecución
test_connection(lora)