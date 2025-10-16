import boto3
import os
import time
from utils import load_config, save_result

config = load_config()
rekognition = boto3.client("rekognition", region_name=config["aws_region"])

def detect_faces(image_bytes):
    return rekognition.detect_faces(Image={"Bytes": image_bytes}, Attributes=["ALL"])

def compare_faces(image_bytes, ref_bytes):
    return rekognition.compare_faces(
        SourceImage={"Bytes": ref_bytes},
        TargetImage={"Bytes": image_bytes},
        SimilarityThreshold=90
    )

def detect_labels(image_bytes):
    return rekognition.detect_labels(
        Image={"Bytes": image_bytes},
        MaxLabels=config["max_labels"],
        MinConfidence=config["min_confidence"]
    )

def validate_image(image_bytes, ref_bytes, last_face=None):
    result = {"status": "OK", "details": []}

    # labels = detect_labels(image_bytes)
    # objects = [label["Name"].lower() for label in labels["Labels"]]
    # if any(x in objects for x in ["wall", "hand", "dark", "screen", "monitor", "phone"]):
    #     result.update({"status": "ALERT", "reason": "Possible obstruction detected"})
    #     return result, None

    labels = detect_labels(image_bytes)
    objects = {label["Name"].lower(): label["Confidence"] for label in labels["Labels"]}

    faces = detect_faces(image_bytes)
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
        result.update({
            "status": "ALERT",
            # "reason": f"Possible obstruction detected: {obstruction_type}"
            "reason": f"Possible obstruction detected"
        })
        result["details"].append({
            "obstruction_type": obstruction_type,
            "confidence": int(max(objects.values()) * 100) / 100
        })
        return result, None

    faces = detect_faces(image_bytes)
    if len(faces["FaceDetails"]) == 0:
        result.update({"status": "ALERT", "reason": "No face detected"})
        return result, None

    if len(faces["FaceDetails"]) > 1:
        result.update({"status": "ALERT", "reason": "More than one face detected"})
        return result, None

    comparison = compare_faces(image_bytes, ref_bytes)
    if not comparison["FaceMatches"]:
        result.update({"status": "ALERT", "reason": "Face does not match reference"})
        return result, None

    if last_face:
        prev = last_face["BoundingBox"]
        curr = faces["FaceDetails"][0]["BoundingBox"]
        if abs(prev["Left"] - curr["Left"]) < 0.01 and abs(prev["Top"] - curr["Top"]) < 0.01:
            result.update({"status": "ALERT", "reason": "Possible static photo"})
            return result, None

    return result, faces["FaceDetails"][0]

def main():

    ref_file = os.listdir(config["reference_path"])[0]
    with open(os.path.join(config["reference_path"], ref_file), "rb") as f:
        ref_bytes = f.read()

    last_face = None
    for file in os.listdir(config["images_path"]):
        if file.lower().endswith((".jpg", ".jpeg", ".png")):
            with open(os.path.join(config["images_path"], file), "rb") as f:
                img_bytes = f.read()

            result, face = validate_image(img_bytes, ref_bytes, last_face)
            if result["status"] == "OK":
                last_face = face
            save_result(result, f"{os.path.splitext(file)[0]}.json", config["results_path"])
            print(f"-{file}: {result}")

            time.sleep(2)

if __name__ == "__main__":
    main()