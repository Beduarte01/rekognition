import boto3

rekognition = boto3.client("rekognition")

def _detect_faces(image_bytes):
    return rekognition.detect_faces(Image={"Bytes": image_bytes}, Attributes=["ALL"])

def _compare_faces(image_bytes, ref_bytes):
    return rekognition.compare_faces(
        SourceImage={"Bytes": ref_bytes},
        TargetImage={"Bytes": image_bytes},
        SimilarityThreshold=90
    )

def _detect_labels(image_bytes, max_labels=10, min_confidence=75.0):
    return rekognition.detect_labels(
        Image={"Bytes": image_bytes},
        MaxLabels=max_labels,
        MinConfidence=min_confidence
    )

def validate_image_bytes(image_bytes: bytes, ref_bytes: bytes, min_confidence=75.0, max_labels=10, last_face_bbox=None):
    result = {"status": "OK", "details": []}

    labels = _detect_labels(image_bytes, max_labels=max_labels, min_confidence=min_confidence)
    objects = {label["Name"].lower(): label["Confidence"] for label in labels["Labels"]}

    faces = _detect_faces(image_bytes)
    face_detected = len(faces["FaceDetails"]) > 0

    obstruction_type = None

    if "hand" in objects and objects["hand"] > 80:
        if not face_detected:
            obstruction_type = "hand covering camera"
        else:
            obstruction_type = "hand visible but not obstructing"
    elif "dark" in objects or ("person" not in objects and "face" not in objects):
        obstruction_type = "camera too dark or covered"
    elif "wall" in objects and objects["wall"] > 70:
        obstruction_type = "camera facing a wall"
    elif any(x in objects for x in ["screen", "monitor", "laptop", "tv"]):
        obstruction_type = "camera facing a screen or monitor"
    elif "phone" in objects:
        obstruction_type = "phone or device detected"

    if obstruction_type:
        result.update({"status": "ALERT", "reason": "Possible obstruction detected"})
        result["details"].append({
            "obstruction_type": obstruction_type,
            "confidence": round(max(objects.values()) if objects else 0, 2)
        })
        return result

    if len(faces["FaceDetails"]) == 0:
        result.update({"status": "ALERT", "reason": "No face detected"})
        return result

    if len(faces["FaceDetails"]) > 1:
        result.update({"status": "ALERT", "reason": "More than one face detected"})
        return result

    comparison = _compare_faces(image_bytes, ref_bytes)
    if not comparison["FaceMatches"]:
        result.update({"status": "ALERT", "reason": "Face does not match reference"})
        return result

    # Anti “foto estática” simple (si provees last_face_bbox)
    if last_face_bbox:
        curr = faces["FaceDetails"][0]["BoundingBox"]
        if abs(last_face_bbox["Left"] - curr["Left"]) < 0.01 and abs(last_face_bbox["Top"] - curr["Top"]) < 0.01:
            result.update({"status": "ALERT", "reason": "Possible static photo"})
            return result

    # Acompaña algunos datos de la detección para auditoría
    result["face"] = {
        "BoundingBox": faces["FaceDetails"][0]["BoundingBox"],
        "Confidence": faces["FaceDetails"][0]["Confidence"]
    }
    return result