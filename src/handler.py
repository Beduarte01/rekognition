# import os
# import json
# import boto3
# from urllib.parse import unquote_plus
# from config import CFG
# from utils import validate_image_bytes  # ver utils más abajo

# s3 = boto3.client("s3", region_name=CFG["aws_region"])

# def _read_s3_bytes(bucket: str, key: str) -> bytes:
#     obj = s3.get_object(Bucket=bucket, Key=key)
#     return obj["Body"].read()

# def _write_s3_json(bucket: str, key: str, data: dict):
#     s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(data, indent=2).encode("utf-8"), ContentType="application/json")

# def handler(event, context):
#     # S3 Event
#     for record in event.get("Records", []):
#         bucket = record["s3"]["bucket"]["name"]
#         key = unquote_plus(record["s3"]["object"]["key"])

#         # Validar que viene del prefijo de imágenes
#         if not key.startswith(CFG["images_prefix"]):
#             continue

#         # Se espera: images/{exam_id}/{user_id}/{filename}
#         parts = key.split("/")
#         # ["images", exam_id, user_id, filename]
#         if len(parts) < 4:
#             print(f"Key no cumple convención: {key}")
#             continue

#         _, exam_id, user_id, filename = parts[0], parts[1], parts[2], "/".join(parts[3:])
#         ref_key = f"{CFG['reference_prefix']}{user_id}.jpg"

#         try:
#             img_bytes = _read_s3_bytes(bucket, key)
#         except Exception as e:
#             print(f"Error leyendo imagen: s3://{bucket}/{key} - {e}")
#             continue

#         try:
#             ref_bytes = _read_s3_bytes(bucket, ref_key)
#         except Exception as e:
#             # Sin referencia → alerta directa o “enroll pending”
#             result = {
#                 "status": "ALERT",
#                 "reason": "Reference image not found",
#                 "exam_id": exam_id,
#                 "user_id": user_id,
#                 "s3_input": f"s3://{bucket}/{key}"
#             }
#             out_key = f"{CFG['results_prefix']}{exam_id}/{user_id}/{os.path.splitext(os.path.basename(filename))[0]}.json"
#             _write_s3_json(bucket, out_key, result)
#             _maybe_notify_proctoring(result)
#             continue

#         # Ejecutar validación (tu core adaptado a bytes)
#         result = validate_image_bytes(
#             image_bytes=img_bytes,
#             ref_bytes=ref_bytes,
#             min_confidence=CFG["min_confidence"],
#             max_labels=CFG["max_labels"]
#         )

#         # Enriquecer con metadatos
#         result.update({
#             "exam_id": exam_id,
#             "user_id": user_id,
#             "s3_input": f"s3://{bucket}/{key}"
#         })

#         # Guardar resultados
#         out_key = f"{CFG['results_prefix']}{exam_id}/{user_id}/{os.path.splitext(os.path.basename(filename))[0]}.json"
#         _write_s3_json(bucket, out_key, result)

#         # (Opcional) snapshot latest
#         _write_s3_json(bucket, f"{CFG['results_prefix']}{exam_id}/{user_id}/latest.json", result)

#         # (Opcional) DynamoDB
#         # _maybe_ddb_put(result)

#         # Notificar Proctoring
#         _maybe_notify_proctoring(result)

#     return {"ok": True}

# # def _maybe_ddb_put(result: dict):
# #     table = os.getenv("DDB_TABLE")
# #     if not table:
# #         return
# #     ddb = boto3.resource("dynamodb", region_name=CFG["aws_region"]).Table(table)
    
# #     item = {
# #         "pk": f"exam#{result['exam_id']}#user#{result['user_id']}",
# #         "sk": result["s3_input"],
# #         "status": result.get("status"),
# #         "reason": result.get("reason"),
# #         "details": result.get("details", []),
# #     }
# #     ddb.put_item(Item=item)

# def _maybe_notify_proctoring(payload: dict):
#     url = os.getenv("PROCTORING_WEBHOOK_URL")
#     if not url:
#         return
#     # Simple notify vía API Gateway (firma opcional con API key)
#     import urllib.request
#     req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type":"application/json"})
#     try:
#         with urllib.request.urlopen(req, timeout=3) as r:
#             print(f"Proctoring notified: {r.status}")
#     except Exception as e:
#         print(f"Notify error: {e}")

import os
import json
import boto3
from urllib.parse import unquote_plus
from config import CFG
from utils import validate_image_bytes

s3 = boto3.client("s3", region_name=CFG["aws_region"])

def _read_s3_bytes(bucket: str, key: str) -> bytes:
    """Lee un objeto de S3 y retorna sus bytes"""
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read()

def _write_s3_json(bucket: str, key: str, data: dict):
    """Escribe un JSON en S3"""
    s3.put_object(
        Bucket=bucket, 
        Key=key, 
        Body=json.dumps(data, indent=2).encode("utf-8"), 
        ContentType="application/json"
    )

def handler(event, context):
    """
    Lambda handler para procesar imágenes de proctoring.
    Se activa cuando se sube una imagen al prefijo images/
    """
    # S3 Event
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        # Validar que viene del prefijo de imágenes
        if not key.startswith(CFG["images_prefix"]):
            print(f"Key ignorado (no está en images/): {key}")
            continue

        # Se espera: images/{exam_id}/{user_id}/{filename}
        parts = key.split("/")
        # ["images", exam_id, user_id, filename]
        if len(parts) < 4:
            print(f"Key no cumple convención: {key}")
            continue

        _, exam_id, user_id, filename = parts[0], parts[1], parts[2], "/".join(parts[3:])
        ref_key = f"{CFG['reference_prefix']}{user_id}.jpg"

        # Leer imagen subida
        try:
            img_bytes = _read_s3_bytes(bucket, key)
            print(f"Imagen leída: s3://{bucket}/{key}")
        except Exception as e:
            print(f"Error leyendo imagen: s3://{bucket}/{key} - {e}")
            continue

        # Leer imagen de referencia
        try:
            ref_bytes = _read_s3_bytes(bucket, ref_key)
            print(f"Referencia leída: s3://{bucket}/{ref_key}")
        except Exception as e:
            # Sin referencia → alerta directa
            print(f"Referencia no encontrada para {user_id}: {e}")
            result = {
                "status": "ALERT",
                "reason": "Reference image not found",
                "exam_id": exam_id,
                "user_id": user_id,
                "s3_input": f"s3://{bucket}/{key}"
            }
            out_key = f"{CFG['results_prefix']}{exam_id}/{user_id}/{os.path.splitext(os.path.basename(filename))[0]}.json"
            _write_s3_json(bucket, out_key, result)
            _maybe_notify_proctoring(result)
            continue

        # Ejecutar validación con Rekognition
        result = validate_image_bytes(
            image_bytes=img_bytes,
            ref_bytes=ref_bytes,
            min_confidence=CFG["min_confidence"],
            max_labels=CFG["max_labels"]
        )

        # Enriquecer con metadatos
        result.update({
            "exam_id": exam_id,
            "user_id": user_id,
            "s3_input": f"s3://{bucket}/{key}"
        })

        # Guardar resultado en S3
        out_key = f"{CFG['results_prefix']}{exam_id}/{user_id}/{os.path.splitext(os.path.basename(filename))[0]}.json"
        _write_s3_json(bucket, out_key, result)
        print(f"Resultado guardado: s3://{bucket}/{out_key}")

        # Guardar snapshot del último resultado
        _write_s3_json(bucket, f"{CFG['results_prefix']}{exam_id}/{user_id}/latest.json", result)

        # Notificar al sistema de Proctoring
        _maybe_notify_proctoring(result)

    return {"statusCode": 200, "body": json.dumps({"message": "Processing completed"})}

def _maybe_notify_proctoring(payload: dict):
    """
    Notifica al webhook de proctoring si está configurado.
    Envía el resultado de la validación vía HTTP POST.
    """
    url = os.getenv("PROCTORING_WEBHOOK_URL")
    if not url:
        print("PROCTORING_WEBHOOK_URL no configurado, omitiendo notificación")
        return
    
    import urllib.request
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode("utf-8"), 
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"Proctoring notificado exitosamente: {r.status}")
    except Exception as e:
        print(f"Error al notificar proctoring: {e}")