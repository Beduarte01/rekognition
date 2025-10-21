"""
Local Tester para probar el handler de Lambda localmente.
Este script simula un evento S3 y ejecuta el handler.

IMPORTANTE: 
- Necesitas tener credenciales AWS configuradas
- El bucket y las imágenes deben existir en S3
- Las variables de entorno deben estar en .env
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Importar el handler
from src.handler import handler

def create_s3_event(bucket_name, exam_id, user_id, filename):
    """
    Crea un evento S3 simulado para testing local.
    
    Args:
        bucket_name: Nombre del bucket S3
        exam_id: ID del examen
        user_id: ID del usuario
        filename: Nombre del archivo de imagen
    
    Returns:
        dict: Evento S3 en formato Lambda
    """
    return {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "2024-01-01T00:00:00.000Z",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "bucket": {
                        "name": bucket_name,
                        "arn": f"arn:aws:s3:::{bucket_name}"
                    },
                    "object": {
                        "key": f"images/{exam_id}/{user_id}/{filename}",
                        "size": 1024,
                        "eTag": "test-etag"
                    }
                }
            }
        ]
    }

def test_single_image():
    """
    Prueba con una sola imagen.
    Útil para debugging rápido.
    """
    print("=" * 60)
    print("🧪 TEST: Una sola imagen")
    print("=" * 60)
    
    # Configuración de prueba
    bucket_name = "tu-bucket-proctoring"  # CAMBIAR por tu bucket real
    exam_id = "exam_123"
    user_id = "user_456"
    filename = "capture_001.jpg"
    
    # Crear evento simulado
    event = create_s3_event(bucket_name, exam_id, user_id, filename)
    
    print(f"\n📋 Evento S3 simulado:")
    print(json.dumps(event, indent=2))
    
    print(f"\n🚀 Ejecutando handler...")
    print(f"   Bucket: {bucket_name}")
    print(f"   Imagen: images/{exam_id}/{user_id}/{filename}")
    print(f"   Referencia: reference/{user_id}.jpg")
    
    try:
        result = handler(event, None)
        print(f"\n✅ Handler ejecutado exitosamente")
        print(f"   Resultado: {json.dumps(result, indent=2)}")
        print(f"\n📁 Verifica el resultado en:")
        print(f"   s3://{bucket_name}/results/{exam_id}/{user_id}/")
    except Exception as e:
        print(f"\n❌ Error al ejecutar handler:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def test_multiple_images():
    """
    Prueba con múltiples imágenes simulando un flujo real.
    """
    print("=" * 60)
    print("🧪 TEST: Múltiples imágenes")
    print("=" * 60)
    
    bucket_name = "tu-bucket-proctoring"  # CAMBIAR por tu bucket real
    exam_id = "exam_123"
    user_id = "user_456"
    
    # Simular múltiples capturas
    test_cases = [
        {"filename": "capture_001.jpg", "description": "Primera captura"},
        {"filename": "capture_002.jpg", "description": "Segunda captura"},
        {"filename": "capture_003.jpg", "description": "Tercera captura"},
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 60}")
        print(f"📸 Prueba {i}/{len(test_cases)}: {test['description']}")
        print(f"{'─' * 60}")
        
        event = create_s3_event(bucket_name, exam_id, user_id, test['filename'])
        
        try:
            result = handler(event, None)
            print(f"✅ {test['filename']}: OK")
        except Exception as e:
            print(f"❌ {test['filename']}: ERROR - {e}")

def test_no_reference():
    """
    Prueba el caso cuando no existe imagen de referencia.
    Debería generar una alerta.
    """
    print("=" * 60)
    print("🧪 TEST: Sin imagen de referencia")
    print("=" * 60)
    
    bucket_name = "tu-bucket-proctoring"
    exam_id = "exam_123"
    user_id = "user_sin_referencia"  # Usuario sin imagen de referencia
    filename = "capture_001.jpg"
    
    event = create_s3_event(bucket_name, exam_id, user_id, filename)
    
    print(f"\n🚀 Probando usuario sin referencia: {user_id}")
    
    try:
        result = handler(event, None)
        print(f"✅ Handler ejecutado (debería generar ALERT)")
        print(f"   Verifica que el resultado contenga: status=ALERT, reason='Reference image not found'")
    except Exception as e:
        print(f"❌ Error: {e}")

def verify_environment():
    """
    Verifica que las variables de entorno estén configuradas.
    """
    print("=" * 60)
    print("🔍 Verificando configuración")
    print("=" * 60)
    
    required_vars = [
        "AWS_REGION",
        "MIN_CONFIDENCE",
        "MAX_LABELS",
        "IMAGES_PREFIX",
        "REFERENCE_PREFIX",
        "RESULTS_PREFIX"
    ]
    
    optional_vars = ["PROCTORING_WEBHOOK_URL"]
    
    print("\n📋 Variables requeridas:")
    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var} = {value}")
        else:
            print(f"   ❌ {var} = NO CONFIGURADA")
            all_ok = False
    
    print("\n📋 Variables opcionales:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var} = {value}")
        else:
            print(f"   ⚠️  {var} = no configurada (opcional)")
    
    if not all_ok:
        print("\n❌ Faltan variables de entorno. Revisa tu archivo .env")
        return False
    
    print("\n✅ Configuración correcta")
    return True

def main():
    """
    Función principal del tester.
    """
    print("\n" + "=" * 60)
    print("🚀 LOCAL TESTER - Rekognition Proctoring")
    print("=" * 60)
    
    # Verificar configuración
    if not verify_environment():
        print("\n⚠️  Configura las variables de entorno antes de continuar")
        return
    
    # Menú de opciones
    print("\n📋 Selecciona una opción:")
    print("   1. Probar una sola imagen")
    print("   2. Probar múltiples imágenes")
    print("   3. Probar sin imagen de referencia")
    print("   4. Ejecutar todas las pruebas")
    
    try:
        choice = input("\nOpción (1-4): ").strip()
        
        if choice == "1":
            test_single_image()
        elif choice == "2":
            test_multiple_images()
        elif choice == "3":
            test_no_reference()
        elif choice == "4":
            test_single_image()
            test_multiple_images()
            test_no_reference()
        else:
            print("❌ Opción inválida")
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelado")

if __name__ == "__main__":
    main()